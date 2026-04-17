from flask import Flask, url_for, request, render_template, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import ast
import os
from datetime import date

with open("teams.json","r") as tjson:
    teams_list = json.load(tjson)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-before-running")

DB_PATH = os.path.join("instance", "users.db")

def get_db():
    os.makedirs("instance", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT    UNIQUE NOT NULL,
                email           TEXT    UNIQUE NOT NULL,
                password        TEXT    NOT NULL,
                age             TEXT    NOT NULL,
                goal            TEXT    NOT NULL,
                workout_num     TEXT    NOT NULL,
                calories_burned TEXT    NOT NULL,
                type            TEXT    NOT NULL,
                status          TEXT    NOT NULL,
                team            TEXT    NOT NULL
            )
        """)
        conn.commit()

init_db()

def is_logged_in():
    return "user" in session

def is_admin():
    return session.get("type") == "Admin"

def is_admin_or_coach():
    return session.get("type") in ("Admin", "Coach")

def get_workout_entry(workouts_list, username):
    """Look up a user's workouts.json entry by username (never by index)."""
    return next((w for w in workouts_list if w["username"] == username), {
        "username": username, "teams_on": [], "workouts": [], "completed_workouts": []
    })

def get_workout_index(workouts_list, username):
    """Return the list index for a given username, or None if not found."""
    for i, w in enumerate(workouts_list):
        if w["username"] == username:
            return i
    return None


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/viewInfo')
def viewInfo():
    return redirect(url_for('log'))

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return render_template('login.html')
    if session["status"] == "Pending":
        return render_template('login.html', error="Awaiting Approval From Admin")
    if session['type'] == "Student":
        return render_template('dashboard.html', workouts=session["workouts"], calories=session["calories"])

    with get_db() as conn:
        students_list = conn.execute("SELECT * FROM user WHERE type = 'Student'").fetchall()
    with open("workouts.json","r") as tjson:
        workouts_list_and_dict = json.load(tjson)

    if is_admin():
        self_id = teams_list
    else:
        self_id = get_workout_entry(workouts_list_and_dict, session["user"])["teams_on"]
    return render_template('dashboard.html', students_list=students_list, teams_list=teams_list,
                           workouts_json=workouts_list_and_dict, self_id=self_id)

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/log', methods=['POST', 'GET'])
def log():
    if not is_logged_in():
        return redirect(url_for('login'))
    with open("workouts.json","r") as tjson:
        workouts_list_and_dict = json.load(tjson)

    Identity = None
    
    if session["type"] == "Student":
        Identity = session["user"]
    else:
        if request.method == 'POST':
            Identity = request.form['logging_student']
            print(Identity)

            
                
        
            

    completed = get_workout_entry(workouts_list_and_dict, Identity)["completed_workouts"]
    to_do = get_workout_entry(workouts_list_and_dict, Identity)["workouts"]
    if Identity == None:
        return redirect(url_for('dashboard'))
    else:
        return render_template('log.html', current_user_complete_workouts=completed, viewing=Identity, to_do=to_do)

@app.route('/completeWorkouts', methods=['POST', 'GET'])
def completeWorkouts():
    if not is_logged_in():
        return redirect(url_for('login'))
    with open("workouts.json","r") as tjson:
        workouts_list_and_dict = json.load(tjson)
    idx = get_workout_index(workouts_list_and_dict, session["user"])
    workouts_list = workouts_list_and_dict[idx]["workouts"] if idx is not None else []

    if request.method == 'POST':
        completed_workout = request.form['Complete']
        workout_index = workouts_list_and_dict[idx]["workouts"].index(ast.literal_eval(completed_workout))
        popped_value = workouts_list_and_dict[idx]["workouts"].pop(workout_index)
        workouts_list_and_dict[idx]["completed_workouts"].append(popped_value)
        with open("workouts.json","w") as tjson:
            json.dump(workouts_list_and_dict, tjson)
        workouts_list = workouts_list_and_dict[idx]["workouts"]

    return render_template('workout.html', type=session["type"], workouts_list=workouts_list)

@app.route('/sendWorkouts', methods=['POST', 'GET'])
def sendWorkouts():
    if not is_logged_in() or not is_admin_or_coach():
        return redirect(url_for('login'))
    if request.method == 'POST':
        workouts_listOfdict = request.form.getlist('workouts')
        for element in range(len(workouts_listOfdict)):
            workouts_listOfdict[element] = ast.literal_eval(workouts_listOfdict[element])

        # Collect all checked students across all teams
        all_selected_students = []
        for teams in teams_list:
            all_selected_students.extend(request.form.getlist(teams))

        for student in all_selected_students:
            with open("workouts.json","r") as tjson:
                workouts_list_and_dict = json.load(tjson)
            idx = get_workout_index(workouts_list_and_dict, student)
            if idx is not None:
                for element in workouts_listOfdict:
                    workouts_list_and_dict[idx]["workouts"].append(element)
                with open("workouts.json","w") as tjson:
                    json.dump(workouts_list_and_dict, tjson)
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = ""
    if request.method == 'POST':
        email_input = request.form['email']
        password    = request.form['password']
        with get_db() as conn:
            user = conn.execute("SELECT * FROM user WHERE email = ?", (email_input,)).fetchone()
        with open("workouts.json","r") as tjson:
            workouts_list_and_dict = json.load(tjson)
        if user and check_password_hash(user["password"], password):
            session["user"]     = user["username"]
            session["workouts"] = user["workout_num"]
            session["calories"] = user["calories_burned"]
            session["age"]      = user["age"]
            session["email"]    = user["email"]
            session["goal"]     = user["goal"]
            session["type"]     = user["type"]
            session["status"]   = user["status"]
            session["id"]       = user["id"]
            session["OpenChat"] = []
            session["teams_on"] = get_workout_entry(workouts_list_and_dict, user["username"])["teams_on"]
            if user["status"] == "Pending":
                return render_template('login.html', error="Awaiting Approval From Admin")
            else:
                return redirect(url_for('dashboard'))
        else:
            error = "Email and Password Don't Match"
    if "user" in session:
        session.clear()
    return render_template('login.html', error=error)

@app.route('/communications', methods=['POST', 'GET'])
def communications():
    if not is_logged_in():
        return redirect(url_for('login'))
    if session["status"] == "Pending":
        return render_template('login.html', error="Awaiting Approval From Admin")
    teams_on = session["teams_on"]
    if request.method == 'POST':
        chatTryingToView = request.form['SelectedTeamChat']
        session["SelectedTeamChat"] = chatTryingToView
        with open("chatrooms.json","r") as tjson:
            chatrooms = json.load(tjson)
        session["OpenChat"] = chatrooms.get(chatTryingToView, [])
    return render_template('communications.html', teams_on=teams_on, open_chat=session["OpenChat"], all_teams=teams_list)

@app.route('/sendMessage', methods=['POST', 'GET'])
def sendMessage():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        message = request.form['message']
        if "SelectedTeamChat" in session:
            with open("chatrooms.json", "r") as tjson:
                chatrooms = json.load(tjson)
            chatrooms[session["SelectedTeamChat"]].append(message)
            with open("chatrooms.json","w") as tjson:
                json.dump(chatrooms, tjson)
            session["OpenChat"] = chatrooms[session["SelectedTeamChat"]]
    return redirect(url_for('communications'))

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['name']
        password = request.form['password']
        email    = request.form['email']
        age      = request.form['age']
        goal     = request.form['goal']
        type_    = request.form['type']
        team     = "Football"
        teams_on = request.form.getlist('team')
        status   = "Pending" if type_ == "Coach" else "None"
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO user (username, email, password, workout_num, calories_burned, age, goal, type, status, team) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (username, email, generate_password_hash(password), "0", "0", age, goal, type_, status, team)
                )
                conn.commit()
                user = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()
            session["user"]     = username
            session["teams_on"] = teams_on
            session["age"]      = age
            session["email"]    = email
            session["goal"]     = goal
            session["type"]     = type_
            session["workouts"] = user["workout_num"]
            session["calories"] = user["calories_burned"]
            session["id"]       = user["id"]
            session["OpenChat"] = []
            session["status"]   = status
            with open("workouts.json","r") as tjson:
                workouts_list_and_dict = json.load(tjson)
            workouts_list_and_dict.append({
                "id": user["id"],
                "username": user["username"],
                "teams_on": teams_on,
                "workouts": [],
                "completed_workouts": []
            })
            with open("workouts.json","w") as tjson:
                json.dump(workouts_list_and_dict, tjson)
            if status == "Pending":
                return render_template('login.html', error="Awaiting Approval From Admin")
            else:
                return render_template('dashboard.html', workouts=session["workouts"], calories=session["calories"])
        except Exception as e:
            print("Insert failed. Error:" + str(e))
            return render_template('signup.html', error="That username or email has already been taken.", teams=teams_list)
    return render_template('signup.html', teams=teams_list)

@app.route('/addteam', methods=['POST', 'GET'])
def addteam():
    if not is_logged_in() or not is_admin():
        return redirect(url_for('login'))
    if request.method == 'POST':
        newTeam = request.form['addedTeam']
        teams_list.append(newTeam)
        with open("teams.json","w") as tjson:
            json.dump(teams_list, tjson)
    return redirect(url_for('dashboard'))

@app.route('/elevateAccess', methods=['POST', 'GET'])
def elevateAccess():
    if not is_logged_in() or not is_admin():
        return redirect(url_for('login'))
    if request.method == 'POST':
        coach_name = request.form['ApproveButton']
        with get_db() as conn:
            conn.execute("UPDATE user SET status = 'None' WHERE username = ?", (coach_name,))
            conn.commit()
    return redirect(url_for('requests'))

@app.route('/requests')
def requests():
    if not is_logged_in() or not is_admin():
        return redirect(url_for('login'))
    with get_db() as conn:
        pending_accounts = conn.execute("SELECT * FROM user WHERE status = 'Pending'").fetchall()
    return render_template('requests.html', accounts=pending_accounts)

@app.route('/workout')
def workout():
    if not is_logged_in():
        return redirect(url_for('login'))
    with open("workouts.json","r") as tjson:
        workouts_list_and_dict = json.load(tjson)
    workouts_list = get_workout_entry(workouts_list_and_dict, session["user"])["workouts"]
    if session["type"] == 'Student':
        return render_template('workout.html', type=session["type"], workouts_list=workouts_list)
    else:
        return render_template('workout.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not is_logged_in():
        return render_template('login.html')
    if request.method == 'POST':
        new_age  = request.form.get('age',  session.get('age', ''))
        new_goal = request.form.get('goal', session.get('goal', ''))
        try:
            with get_db() as conn:
                conn.execute(
                    "UPDATE user SET age = ?, goal = ? WHERE username = ?",
                    (new_age, new_goal, session["user"])
                )
                conn.commit()
            session["age"]  = new_age
            session["goal"] = new_goal
        except Exception as e:
            print("Profile update failed:", e)
    return render_template('profile.html', username=session["user"], email=session["email"],
                           age=session["age"], goal=session["goal"])

if __name__ == '__main__':
    app.run(debug=True)