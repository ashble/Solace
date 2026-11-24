from flask import Blueprint, jsonify, request
from extensions import db
from models import Conversation, Message, TherapistProfile, User
from auth_helpers import current_user, csrf_required, role_required

chat_bp = Blueprint("chat", __name__, url_prefix="/api/conversations")


def is_participant(conversation, user_id):
    return conversation and user_id in {conversation.client_id, conversation.therapist_id}


def message_json(message):
    return {"id": message.id, "conversation_id": message.conversation_id, "sender_id": message.sender_id,
            "body": message.body, "created_at": message.created_at.isoformat()}


@chat_bp.get("")
@role_required("client", "therapist")
def list_conversations():
    user = current_user()
    query = Conversation.query.filter(
        (Conversation.client_id == user.id) | (Conversation.therapist_id == user.id)
    ).order_by(Conversation.created_at.desc())
    result = []
    for item in query.all():
        peer = item.therapist if item.client_id == user.id else item.client
        latest = Message.query.filter_by(conversation_id=item.id).order_by(Message.id.desc()).first()
        result.append({"id": item.id, "participant": {"id": peer.id, "name": peer.name},
                       "last_message": message_json(latest) if latest else None})
    return jsonify(conversations=result)


@chat_bp.post("")
@csrf_required
@role_required("client", "therapist")
def create_conversation():
    user = current_user()
    payload = request.get_json(silent=True) or {}
    try:
        peer_id = int(payload.get("therapist_id" if user.role == "client" else "client_id"))
    except (TypeError, ValueError):
        return jsonify(error="A conversation participant id is required."), 400
    peer = db.session.get(User, peer_id)
    expected_peer_role = "therapist" if user.role == "client" else "client"
    if not peer or peer.role != expected_peer_role or peer.status != "active":
        return jsonify(error="Participant not found."), 404
    if peer.role == "therapist" and not TherapistProfile.query.filter_by(user_id=peer.id, is_listed=True).first():
        return jsonify(error="Therapist is unavailable."), 404
    client_id, therapist_id = (user.id, peer.id) if user.role == "client" else (peer.id, user.id)
    conversation = Conversation.query.filter_by(client_id=client_id, therapist_id=therapist_id).first()
    if not conversation:
        conversation = Conversation(client_id=client_id, therapist_id=therapist_id)
        db.session.add(conversation)
        db.session.commit()
    return jsonify(id=conversation.id, client_id=client_id, therapist_id=therapist_id), 201


@chat_bp.get("/<int:conversation_id>/messages")
@role_required("client", "therapist")
def fetch_messages(conversation_id):
    conversation = db.session.get(Conversation, conversation_id)
    if not is_participant(conversation, current_user().id):
        return jsonify(error="Conversation not found."), 404
    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
        before = int(request.args["before"]) if "before" in request.args else None
    except ValueError:
        return jsonify(error="Invalid pagination parameters."), 400
    query = Message.query.filter_by(conversation_id=conversation_id)
    if before:
        query = query.filter(Message.id < before)
    items = query.order_by(Message.id.desc()).limit(limit).all()
    return jsonify(messages=[message_json(m) for m in reversed(items)])


@chat_bp.post("/<int:conversation_id>/messages")
@csrf_required
@role_required("client", "therapist")
def send_message(conversation_id):
    user = current_user()
    conversation = db.session.get(Conversation, conversation_id)
    if not is_participant(conversation, user.id):
        return jsonify(error="Conversation not found."), 404
    body = str((request.get_json(silent=True) or {}).get("body", "")).strip()
    if not body or len(body) > 5000:
        return jsonify(error="Message must contain 1 to 5000 characters."), 400
    message = Message(conversation_id=conversation_id, sender_id=user.id, body=body)
    db.session.add(message)
    db.session.commit()
    return jsonify(message=message_json(message)), 201
