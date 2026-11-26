from flask import Blueprint, render_template, redirect
from auth_helpers import current_user

starter_bp = Blueprint("starter", __name__)


@starter_bp.route("/")
def starter():

    #sends logged-in users straight to their dashboard
    user = current_user()
    if user and user.role == "client":
        return redirect("/client")
    return render_template("starter.html")

@starter_bp.route("/about")
def about():
    return render_template("about.html")