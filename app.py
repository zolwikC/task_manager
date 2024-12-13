from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Model dla zadania
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(10), default="Medium")  # Low, Medium, High


@app.route("/")
def index():
    filter_status = request.args.get("filter")
    sort_by = request.args.get("sort_by", "created_at")
    search_query = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)

    query = Task.query

    # Filtruj po stanie
    if filter_status == "completed":
        query = query.filter_by(completed=True)
    elif filter_status == "pending":
        query = query.filter_by(completed=False)
    elif filter_status == "overdue":
        query = query.filter(Task.deadline < datetime.utcnow(), Task.completed == False)
    elif filter_status == "upcoming":
        query = query.filter(Task.deadline > datetime.utcnow(), Task.deadline < datetime.utcnow() + timedelta(days=7))

    # Wyszukiwanie
    if search_query:
        query = query.filter(Task.title.contains(search_query) | Task.description.contains(search_query))

    # Sortowanie
    if sort_by == "title":
        query = query.order_by(Task.title)
    elif sort_by == "priority":
        query = query.order_by(Task.priority.desc())
    elif sort_by == "deadline":
        query = query.order_by(Task.deadline)
    else:
        query = query.order_by(Task.created_at)

    # Paginacja
    tasks = query.paginate(page=page, per_page=5)

    return render_template("index.html", tasks=tasks, filter_status=filter_status, sort_by=sort_by, search_query=search_query)


@app.route("/add", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        priority = request.form["priority"]
        deadline = request.form["deadline"]
        deadline = datetime.strptime(deadline, "%Y-%m-%d") if deadline else None
        new_task = Task(title=title, description=description, deadline=deadline, priority=priority)
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
        task.priority = request.form["priority"]
        deadline = request.form["deadline"]
        task.deadline = datetime.strptime(deadline, "%Y-%m-%d") if deadline else None
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit_task.html", task=task)


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete_completed")
def delete_completed_tasks():
    Task.query.filter_by(completed=True).delete()
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/details/<int:task_id>")
def task_details(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template("task_details.html", task=task)


@app.route("/export")
def export_tasks():
    tasks = Task.query.all()
    output = io.StringIO()
    writer = csv.writer(output)

    # Nagłówki
    writer.writerow(["ID", "Title", "Description", "Priority", "Completed", "Deadline", "Created At"])

    for task in tasks:
        writer.writerow([task.id, task.title, task.description, task.priority, task.completed, task.deadline, task.created_at])

    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv", as_attachment=True, download_name="tasks.csv")


if __name__ == "__main__":
    app.run(debug=True)
