from flask import Blueprint, render_template, redirect, jsonify
from models import TherapistProfile, User

client_bp = Blueprint("client", __name__)

@client_bp.route("/")
@client_bp.route("/client")
def client_dashboard():
    user = {"name": "Binibirocha", "display_name": "User, name", "role": "Client"}
    return render_template("index.html", role="client", active_tab="dashboard", active_page="dashboard", user=user)

@client_bp.route("/search-therapist")
def search_therapist():
    therapists = listed_therapists()
    user = {"name": "Binibirocha", "display_name": "User, name", "role": "Client"}
    return render_template("search-therapist.html", therapists=therapists, user=user)


def listed_therapists():
    profiles = (TherapistProfile.query.join(User).filter(
        TherapistProfile.is_listed.is_(True), User.role == "therapist", User.status == "active"
    ).order_by(User.name.asc()).all())
    return [{"id": p.user.id, "name": p.user.name, "email": p.user.email,
             "title": p.practice_name or "Therapist", "bio": p.bio or "",
             "specialties": [s.strip() for s in (p.specialties or "").split(",") if s.strip()],
             "languages": p.languages or "", "location": p.location or "",
             "session_fee": float(p.session_fee) if p.session_fee is not None else None}
            for p in profiles]


@client_bp.get("/api/therapists")
def therapist_directory_api():
    return jsonify(therapists=listed_therapists())

@client_bp.route("/schedule")
def client_schedule():
    return redirect("/client")

@client_bp.route("/chats")
def client_chats():
    return redirect("/client")
