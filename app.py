from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

from flask_migrate import Migrate

# Inicjalizacja Flask-Migrate
migrate = Migrate(app, db)

# Model dla zadania
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route("/")
def index():
    filter_status = request.args.get("filter")
    sort_by = request.args.get("sort_by", "created_at")
    
    # Filtruj i sortuj
    query = Task.query
    if filter_status == "completed":
        query = query.filter_by(completed=True)
    elif filter_status == "pending":
        query = query.filter_by(completed=False)
    
    if sort_by == "title":
        query = query.order_by(Task.title)
    else:  # Domyślnie sortuj według daty dodania
        query = query.order_by(Task.created_at)
    
    tasks = query.all()
    return render_template("index.html", tasks=tasks, filter_status=filter_status, sort_by=sort_by)

@app.route("/add", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        new_task = Task(title=title, description=description)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_task.html")

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == "POST":
        task.title = request.form["title"]
        task.description = request.form["description"]
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit_task.html", task=task)

@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
