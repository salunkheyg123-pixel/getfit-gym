from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///members.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    number = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(250), nullable=False) 
    plan = db.Column(db.String(50), nullable=False)

    trainer_id = db.Column(db.Integer, db.ForeignKey("trainer.id"), nullable=True)
    trainer = db.relationship("Trainer", backref="members", lazy=True)

    @property
    def assigned(self):
        return self.trainer.name if self.trainer else "Not Assigned"


class Trainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(150), nullable=False)  # for login


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(300), nullable=False)


ADMIN_USERNAME = "Yogesh"
ADMIN_PASSWORD = "yogesh"

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/join", methods=["GET", "POST"])
def join():
    message = None
    error = None

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        number = request.form["number"]
        description = request.form["description"]  # activity
        plan = request.form["plan"]

        if Member.query.filter_by(email=email).first():
            error = "⚠️ Email already registered!"
        else:
            # Assign trainer automatically
            trainer = Trainer.query.filter_by(specialty=description).first()
            new_member = Member(
                name=name,
                email=email,
                number=number,
                description=description,
                plan=plan,
                trainer_id=trainer.id if trainer else None
            )
            db.session.add(new_member)
            db.session.commit()
            message = "✅ You have successfully joined GetFit Gym!"

    return render_template("join.html", error=error, message=message)


@app.route("/contacts")
def contact():
    return render_template("contact.html")


@app.route("/member_login", methods=["GET", "POST"])
def member_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        phone_number = request.form["phone_number"]

        member = Member.query.filter_by(name=username, number=phone_number).first()
        if member:
            session["member_logged_in"] = True
            session["member_id"] = member.id
            return redirect(url_for("member_home"))
        else:
            error = "Invalid Username or Phone Number"

    return render_template("member_login.html", error=error)


@app.route("/member_home")
def member_home():
    if not session.get("member_logged_in"):
        return redirect(url_for("member_login"))

    member = Member.query.get(session["member_id"])
    return render_template("member_home.html", member=member)


@app.route("/about")
def about_you():
    if not session.get("member_logged_in"):
        return redirect(url_for("member_home"))
    member = Member.query.get(session["member_id"])
    return render_template("about_you.html", member=member)


@app.route("/member_dashboard")
def member_dashboard():
    if not session.get("member_logged_in"):
        return redirect(url_for("member_login"))

    member = Member.query.get(session["member_id"])
    return render_template("member_dashboard.html", member=member)


@app.route("/trainer_login", methods=["GET", "POST"])
def trainer_login():
    error = None
    if request.method == "POST":
        trainer_id = request.form["trainer_id"]
        password = request.form["password"]

        trainer = Trainer.query.filter_by(trainer_id=trainer_id, password=password).first()
        if trainer:
            session["trainer_logged_in"] = True
            session["trainer_id"] = trainer.id
            return redirect(url_for("trainer_home"))
        else:
            error = "❌ Invalid Trainer Credentials"

    return render_template("trainer_login.html", error=error)


@app.route("/trainer_home")
def trainer_home():
    if not session.get("trainer_logged_in"):
        return redirect(url_for("trainer_login"))
    trainer = Trainer.query.get(session["trainer_id"])
    return render_template("trainer_home.html", trainer=trainer)


@app.route("/review", methods=["GET", "POST"])
def review():
    if request.method == "POST":
        name = request.form["name"]
        rating = int(request.form["rating"])
        comment = request.form["comment"]

        new_review = Review(name=name, rating=rating, comment=comment)
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for("review"))

    reviews = Review.query.all()
    return render_template("review.html", reviews=reviews)


@app.route("/member_info")
def member_info():
    if not session.get("trainer_logged_in"):
        return redirect(url_for("trainer_login"))

    members = Member.query.all()
    return render_template("member_info.html", Members=members)


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_panel"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    error_member = None
    error_trainer = None

    if request.method == "POST":
        action = request.form.get("action")

        # -------- ADD MEMBER --------
        if action == "add_member":
            name = request.form["name"]
            email = request.form["email"]
            number = request.form["number"]
            description = request.form["description"]
            plan = request.form["plan"]

            selected_trainer_name = request.form.get("assigned_trainer")

            if Member.query.filter_by(email=email).first():
                error_member = "⚠️ Email already exists"
            else:
                trainer = None
                if selected_trainer_name and selected_trainer_name != "None":
                    trainer = Trainer.query.filter_by(
                        name=selected_trainer_name.strip()
                    ).first()

                new_member = Member(
                    name=name,
                    email=email,
                    number=number,
                    description=description,
                    plan=plan,
                    trainer_id=trainer.id if trainer else None
                )
                db.session.add(new_member)
                db.session.commit()
                return redirect(url_for("admin_panel"))

        # -------- ADD TRAINER --------
        elif action == "add_trainer":
            trainer_id = request.form["trainer_id"]
            name = request.form["name"]
            phone = request.form["phone"]
            specialty = request.form["specialty"]
            password = request.form["password"]

            if Trainer.query.filter_by(trainer_id=trainer_id).first():
                error_trainer = "⚠️ Trainer ID already exists"
            else:
                new_trainer = Trainer(
                    trainer_id=trainer_id,
                    name=name,
                    phone=phone,
                    specialty=specialty,
                    password=password
                )
                db.session.add(new_trainer)
                db.session.commit()
                return redirect(url_for("admin_panel"))

    members = Member.query.all()
    trainers = Trainer.query.all()

    return render_template(
        "member.html",
        Members=members,
        Trainers=trainers,
        error_member=error_member,
        error_trainer=error_trainer
    )

@app.route("/remove_member/<int:id>")
def remove_member(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for("admin_panel"))


@app.route("/remove_trainer/<int:id>")
def remove_trainer(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    trainer = Trainer.query.get_or_404(id)

    # Unassign trainer from members
    for member in trainer.members:
        member.trainer_id = None

    db.session.delete(trainer)
    db.session.commit()
    return redirect(url_for("admin_panel"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)
