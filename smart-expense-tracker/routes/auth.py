import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User

bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        if not name or not email or not pw:
            flash("All fields are required.", "danger")
        elif not EMAIL_RE.match(email):
            flash("Enter a valid email address.", "danger")
        elif len(pw) < 8 or not any(c.isdigit() for c in pw) or not any(c.isalpha() for c in pw):
            flash("Password must be 8+ characters with letters and numbers.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
        else:
            db.session.add(User(name=name, email=email, password_hash=generate_password_hash(pw)))
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth.html", mode="register")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")  # same message either way: no user enumeration
    return render_template("auth.html", mode="login")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
