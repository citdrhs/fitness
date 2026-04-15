from flask import Flask, url_for, request, render_template, session, redirect
import sqlite3
import json
import ast
import os

#render_template loads the html files plus anything in the fancy {} brackets
#session saves user information in the form of a variable that's saved for as long as the user is logged in (for example: I could put a user's username in a variable so it's always accessible to the app code)
#request gets POST information from a form
#url_for generates a link the code can follow (works inside an html file too)

#sqlite3 is python's built-in database library (no extra install needed)

#json lets me encrypt and decrypt .json files (types of files used for the storage of dictionaries and lists)

# ~~~~~~~~~~

#teams_list contains all the teams to be displayed on the signup.html dropdown
with open("teams.json","r") as tjson:
    teams_list = json.load(tjson)


app = Flask(__name__)
app.secret_key = 'SuperBowlFitness'

# ── Database helpers ──────────────────────────────────────────────────────────
DB_PATH = os.path.join("instance", "users.db")

def get_db():
    """Return a sqlite3 connection with row_factory set so rows act like dicts."""
    os.makedirs("instance", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the users table if it doesn't already exist."""
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

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():

    if "user" in session:

        with get_db() as conn:
            user = conn.execute("SELECT * FROM user WHERE username = ?", (session["user"],)).fetchone()

        if user["status"] != "Pending":

            if session['type'] == "Student":
                return render_template('dashboard.html', workouts=session["workouts"], calories=session["calories"])

            # coaches + admins only
            else:
                with get_db() as conn:
                    students_list = conn.execute("SELECT * FROM user WHERE type = 'Student'").fetchall()
                with open("workouts.json","r") as tjson:
                    workouts_list_and_dict = json.load(tjson)
                return render_template('dashboard.html', students_list=students_list, teams_list=teams_list, workouts_json=workouts_list_and_dict)
        else:
            return render_template('login.html', error="Awaiting Approval From Admin")

    else:
        return render_template('login.html')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/log')
def log():
    with get_db() as conn:
        user = conn.execute("SELECT * FROM user WHERE username = ?", (session["user"],)).fetchone()
    with open("workouts.json","r") as tjson:
        workouts_list_and_dict = json.load(tjson)
    return render_template('log.html', current_user_complete_workouts=workouts_list_and_dict[int(user["id"]) - 1]["completed_workouts"])


@app.route('/completeWorkouts', methods=['POST', 'GET'])
def completeWorkouts():

    if request.method == 'POST':

        completed_workout = request.form['Complete']
        with open("workouts.json","r") as tjson:
            workouts_list_and_dict = json.load(tjson)

        with get_db() as conn:
            user = conn.execute("SELECT * FROM user WHERE username = ?", (session["user"],)).fetchone()

        workouts_list_index = workouts_list_and_dict[user["id"]-1]["workouts"].index(ast.literal_eval(completed_workout))
        popped_value = workouts_list_and_dict[int(user["id"]) - 1]["workouts"].pop(workouts_list_index)
        workouts_list_and_dict[int(user["id"]) - 1]["completed_workouts"].append(popped_value)

        with open("workouts.json","w") as tjson:
            json.dump(workouts_list_and_dict, tjson)

        workouts_list = workouts_list_and_dict[int(session["id"]) - 1]["workouts"]

    return render_template('workout.html', type=session["type"], workouts_list=workouts_list)


@app.route('/sendWorkouts', methods=['POST', 'GET'])
def sendWorkouts():

    if request.method == 'POST':

        for teams in teams_list:

            teamWorkouts_list  = request.form.getlist(teams)
            workouts_listOfdict = request.form.getlist('workouts')

            for element in range(len(workouts_listOfdict)):
                workouts_listOfdict[element] = ast.literal_eval(workouts_listOfdict[element])

            for student in teamWorkouts_list:

                with open("workouts.json","r") as tjson:
                    workouts_list_and_dict = json.load(tjson)

                with get_db() as conn:
                    studentx = conn.execute("SELECT * FROM user WHERE username = ?", (student,)).fetchone()

                for element in workouts_listOfdict:
                    workouts_list_and_dict[studentx["id"] - 1]["workouts"].append(element)

                print(workouts_listOfdict)
                print("workouts_list_and_dict: " + str(workouts_list_and_dict))

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

        if user and user["password"]:

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

            session["teams_on"] = workouts_list_and_dict[user["id"] - 1]["teams_on"]

            if user["status"] == "Pending":
                return render_template('login.html', error="Awaiting Approval From Admin")
            else:
                return redirect(url_for('dashboard'))

        else:
            error = "Email and Password Don't Match"
            print("try again")

    # Clear session on GET (logout)
    if "user" in session:
        session.pop("user", None)
        session.pop("email", None)
        session.pop("workouts", None)
        session.pop("calories", None)
        session.pop("age", None)
        session.pop("status", None)
        session.pop("type", None)
        session.pop("goal", None)
        session.pop("teams_on", None)
        session.pop("OpenChat", None)

    return render_template('login.html', error=error)


@app.route('/communications', methods=['POST', 'GET'])
def communications():

    if "user" in session:

        teams_on = session["teams_on"]

        if request.method == 'POST':

            chatTryingToView = request.form['SelectedTeamChat']
            session["SelectedTeamChat"] = chatTryingToView

            with open("chatrooms.json","r") as tjson:
                chatrooms = json.load(tjson)

            session["OpenChat"] = chatrooms.get(chatTryingToView, [])

        return render_template('communications.html', teams_on=teams_on, open_chat=session["OpenChat"], all_teams=teams_list)
    else:
        return redirect(url_for('login'))


@app.route('/sendMessage', methods=['POST', 'GET'])
def sendMessage():

    if request.method == 'POST':

        message = request.form['message']

        if "SelectedTeamChat" in session:

            print("appending message...")

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
        # team column kept as placeholder (legacy, see comments in original)
        team     = "Football"
        teams_on = request.form.getlist('team')

        status = "Pending" if type_ == "Coach" else "None"

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO user (username, email, password, workout_num, calories_burned, age, goal, type, status, team) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (username, email, password, "0", "0", age, goal, type_, status, team)
                )
                conn.commit()
                user = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()

            print("user added successfully")

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

            with open("workouts.json","r") as tjson:
                workouts_list_and_dict = json.load(tjson)

            workouts_dictionary = {
                "id": user["id"],
                "username": user["username"],
                "teams_on": teams_on,
                "workouts": [],
                "completed_workouts": []
            }

            workouts_list_and_dict.append(workouts_dictionary)

            with open("workouts.json","w") as tjson:
                json.dump(workouts_list_and_dict, tjson)

            if user["status"] == "Pending":
                return render_template('login.html', error="Awaiting Approval From Admin")
            else:
                return render_template('dashboard.html', workouts=session["workouts"], calories=session["calories"])

        except Exception as e:
            print("Insert failed. Error:" + str(e))
            return render_template('signup.html', error="That username or email has already been taken.", teams=teams_list)

    return render_template('signup.html', teams=teams_list)


@app.route('/addteam', methods=['POST', 'GET'])
def addteam():
    if request.method == 'POST':

        newTeam = request.form['addedTeam']
        teams_list.append(newTeam)

        with open("teams.json","w") as tjson:
            json.dump(teams_list, tjson)

    return redirect(url_for('dashboard'))


@app.route('/elevateAccess', methods=['POST', 'GET'])
def elevateAccess():
    if request.method == 'POST':

        coach_name = request.form['ApproveButton']

        with get_db() as conn:
            conn.execute("UPDATE user SET status = 'None' WHERE username = ?", (coach_name,))
            conn.commit()

    return redirect(url_for('requests'))


@app.route('/requests')
def requests():

    with get_db() as conn:
        pending_accounts = conn.execute("SELECT * FROM user WHERE status = 'Pending'").fetchall()

    print(pending_accounts)
    return render_template('requests.html', accounts=pending_accounts)


@app.route('/workout')
def workout():

    if "user" in session:

        with open("workouts.json","r") as tjson:
            workouts_list_and_dict = json.load(tjson)

        workouts_list = workouts_list_and_dict[int(session["id"]) - 1]["workouts"]
        print(workouts_list)

        if session["type"] == 'Student':
            print("student")
            return render_template('workout.html', type=session["type"], workouts_list=workouts_list)
        else:
            return render_template('workout.html')

    else:
        return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if "user" in session:

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

        return render_template('profile.html', username=session["user"], email=session["email"], age=session["age"], goal=session["goal"])

    else:
        return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
