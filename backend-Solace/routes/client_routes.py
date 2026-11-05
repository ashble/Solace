from flask import Blueprint, render_template, redirect

client_bp = Blueprint("client", __name__)

@client_bp.route("/")
@client_bp.route("/client")
def client_dashboard():
    user = {"name": "Binibirocha", "display_name": "User, name", "role": "Client"}
    return render_template("index.html", role="client", active_tab="dashboard", active_page="dashboard", user=user)

@client_bp.route("/search-therapist")
def search_therapist():
    therapists = [
        {"name": "Dr. Zayne Li", "title": "Licensed Therapist", "bio": "Specializes in cognitive behavioral therapy and anxiety."},
        {"name": "Dr. Sarah Chen", "title": "Clinical Psychologist", "bio": "Specializes in stress reduction and emotional wellness."},
        {"name": "Dr. Nyen", "title": "Mindfulness Practitioner", "bio": "Helping clients navigate personal development and therapy."},
        {"name": "Dr. Shaun Murphy", "title": "Behavioral Specialist", "bio": "Experienced clinical psychologist focusing on youth & adult health."},
        {"name": "Dr. Elena Gilbert", "title": "Family Counselor", "bio": "Dedicated to creating safe, empathetic spaces for holistic healing."},
        {"name": "Dr. Alex Grey", "title": "Relationship Therapist", "bio": "Compassionate mental health professional with 10+ years experience."}
    ]
    user = {"name": "Binibirocha", "display_name": "User, name", "role": "Client"}
    return render_template("search-therapist.html", therapists=therapists, user=user)

@client_bp.route("/schedule")
def client_schedule():
    return redirect("/client")

@client_bp.route("/chats")
def client_chats():
    return redirect("/client")