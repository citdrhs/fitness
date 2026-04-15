from flask import Flask, url_for, request, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
import json
import ast
import builtins

#render_template loads the html files plus anything in the fancy {} brackets
#session saves user information in the form of a variable that's saved for as long as the user is logged in (for example: I could put a user's username in a variable so it's always accessible to the app code)
#request gets POST information from a form
#url_for generates a link the code can follow (works inside an html file too)

#SQL_alchemy creates an instance with a database file inside

#json lets me encrypt and decrypt .json files (types of files used for the storage of dictionaries and lists)

#builtins lets custom functions share the same name as default python functions (since somebody made an index)


#teams_list contains all the teams to be displayed on the signup.html dropdown,
#teams_list = ["Soccer", "Football", "Softball", "Track", "Wrestling"]
with open("teams.json","r") as tjson:
    teams_list = json.load(tjson)




app = Flask(__name__)
app.secret_key = 'SuperBowlFitness'

#database creation ---------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

class User(db.Model):
    #__tablename__ = 'Userinfo'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    #PASSWORD WILL BE HASHED IF WE CONTINUE USING THIS FLASK FILE
    password = db.Column(db.String(250), unique=False, nullable=False)
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    age = db.Column(db.String(10), unique=False, nullable=False)
    goal = db.Column(db.String(10), unique=False, nullable=False)
    workout_num = db.Column(db.String(10), unique=False, nullable=False)
    calories_burned = db.Column(db.String(10), unique=False, nullable=False)
    type = db.Column(db.String(15), unique=False, nullable=False)
    status = db.Column(db.String(30), unique=False, nullable=False)
    team = db.Column(db.String(50), unique=False, nullable=False)

#vv
def __repr__(self):
    return f'<User {self.username}>'
#^^

with app.app_context():
    db.create_all()
#---------------------------------



@app.route('/')
def home():
    return render_template('index.html')


#temporary route to each html file, I may delete some of these after reviewing the website code and its needs.

@app.route('/dashboard')
def dashboard():
    

    if "user" in session:

        user = User.query.filter_by(username=session["user"]).first()



        if user.status != "Pending":

            if session['type'] == "Student":

                return render_template('dashboard.html', workouts=session["workouts"], calories=session["calories"])
            
            #coaches + admins only
            else:
                #get every student and put them in students_list, then send the list to dashboard.html
                students_list = User.query.filter_by(type='Student').all()
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

    user = User.query.filter_by(username=session["user"]).first()
    with open("workouts.json","r") as tjson:
            workouts_list_and_dict = json.load(tjson)

    #workouts_list_and_dict[int(user.id) - 1]["completed_workouts"]

    return render_template('log.html', current_user_complete_workouts=workouts_list_and_dict[int(user.id) - 1]["completed_workouts"])

@app.route('/completeWorkouts', methods=['POST', 'GET'])
def completeWorkouts():

    if request.method == 'POST':

        completed_workout = request.form['Complete']
        with open("workouts.json","r") as tjson:
            workouts_list_and_dict = json.load(tjson)

            #when merging, user could be set to the session value of user perhaps?
            user = User.query.filter_by(username=session["user"]).first()

            #workouts_list_index will be an integer that represents the placement of the workout the user is trying to delete
            workouts_list_index = workouts_list_and_dict[user.id-1]["workouts"].index(ast.literal_eval(completed_workout))
            
            #
            popped_value = workouts_list_and_dict[int(user.id) - 1]["workouts"].pop(workouts_list_index)
            #popped_value does nothing for now, but it'll be useful for sending data to Doolidge and company later

            #newline - append the value taken from the workouts_list in workouts.json and put it into the completed_workouts list
            workouts_list_and_dict[int(user.id) - 1]["completed_workouts"].append(popped_value)
            #

        with open("workouts.json","w") as tjson:
            json.dump(workouts_list_and_dict, tjson)

        #workouts_list gets the list of workouts for the current user in the session
        workouts_list = workouts_list_and_dict[int(session["id"]) - 1] ["workouts"]


    return render_template('workout.html', type=session["type"], workouts_list=workouts_list)




@app.route('/sendWorkouts', methods=['POST', 'GET'])
def sendWorkouts():

    if request.method == 'POST':

        for teams in teams_list:

            #teamWorkouts_list contains a list of every team a player can choose from on the signup page (excluding "None" I believe)
            teamWorkouts_list = request.form.getlist(teams)
            #workouts_listOfdict contains every workout-dictionary in a list format
            workouts_listOfdict = request.form.getlist('workouts')
            
            #element is a number starting at zero which increases by one for every iteration of the for loop, len(workouts_listOfdict) returns the length of the list, not the dict(ionary)
            for element in range(len(workouts_listOfdict)):
                #find a specific iteration (determined by "element") and replace it with the evaluated version of itself
                #ast.literal_eval converts strings into code, in this situation, it's turning each dictionary encased in '' in the list into regular dictionaries
                workouts_listOfdict[element] = ast.literal_eval(workouts_listOfdict[element])
            
            #here for testing purposes
            

            for student in teamWorkouts_list:
                
                with open("workouts.json","r") as tjson:
                    workouts_list_and_dict = json.load(tjson)
                
                
                #should only replace the contents of workouts.json for now
                studentx = User.query.filter_by(username=student).first()


                #workouts_list_and_dict[studentx.id - 1] ["workouts"] = workouts_listOfdict
                for element in workouts_listOfdict:
                    workouts_list_and_dict[studentx.id - 1] ["workouts"].append(element)

                #you can keep these print statements if you're confused by how the code works, but they aren't needed anymore
                print(workouts_listOfdict)
                print("workouts_list_and_dict: " + str(workouts_list_and_dict))

                with open("workouts.json","w") as tjson:
                    json.dump(workouts_list_and_dict, tjson)

                

                #code for retrieving and sending the workout information to workouts.json


                


    return redirect(url_for('dashboard'))




@app.route('/login',  methods=['POST', 'GET'])
def login():

    error = ""

    if request.method == 'POST':

        username = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=username).first()

        with open("workouts.json","r") as tjson:
            #I'm going to call this list workouts_list_and_dict every time I use it so the code's easy to understand, but here, I'm just using it to retrieve the list of teams a student is on
            workouts_list_and_dict = json.load(tjson)

        if user and user.password:

            session["user"] = user.username

            session["workouts"] = user.workout_num
            session["calories"] = user.calories_burned
            session["age"] = user.age
            session["email"] = user.email
            session["goal"] = user.goal
            session["type"] = user.type
            session["status"] = user.status
            session["id"] = user.id
            session["OpenChat"] = []

            session["teams_on"] = workouts_list_and_dict[user.id - 1] ["teams_on"]

            if user.status == "Pending":
                return render_template('login.html', error="Awaiting Approval From Admin")
            else:
                return redirect(url_for('dashboard'))
        
        


        else:
            
            error = "Email and Password Don't Match"
            print("try again")

    #the code below runs no matter the request method
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
            session["SelectedTeamChat"] = request.form['SelectedTeamChat']

            with open("chatrooms.json","r") as tjson:
                chatrooms = json.load(tjson)

            #list
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

#signup, the methods include post because it handles form data
@app.route('/signup', methods=['POST', 'GET'])
def signup():

    #the request.method will equal POST when the form is submitted, otherwise the website is just trying to render the template
    if request.method == 'POST':
        username = request.form['name']
        password = request.form['password']
        email = request.form['email']
        age = request.form['age']
        goal = request.form['goal']
        type = request.form['type']
        #the variable "team" should be deleted later as it now serves no function (I can't remove it now because that would force me to update the database, but I will later) (also update the line that assigns the "unique_user" variable)
        #team = request.form['team']
        #placeholder so code doesn't break while I'm testing
        team = "Football"
        #
        #
        teams_on = request.form.getlist('team')

        if type == "Coach":
            status="Pending"
        else:
            status="None"

        #this code was copied from an old project, I'll modify it if we need this website later, but since we're likely going edit this code heavily once integrated with Swift, we might not even end up needing this.  ...........
        unique_user = User(username=username, email=email, password=password, workout_num=0, calories_burned=0, age=age, goal=goal, type=type, status=status, team=team)
        db.session.add(unique_user)

        try:
            db.session.commit()
            print("user added successfully")
            #log the user in automatically upon signing up
            #this code here should also probably be a function if we continue using this file ********************
            session["user"] = username
            #unlike most session variables in this project, teams_on is a list
            session["teams_on"] = teams_on
            

            #move these three below user.query when moved to /login
            session["age"] = age
            session["email"] = email
            session["goal"] = goal
            session["type"] = type

            user = User.query.filter_by(username=username).first()
            session["workouts"] = user.workout_num
            session["calories"] = user.calories_burned
            session["id"] = user.id
            session["OpenChat"] = []
            print(session["workouts"])


            #add code for updating the json file here!!

            with open("workouts.json","r") as tjson:
                workouts_list_and_dict = json.load(tjson)

            

            #this is the dictionary that'll be created and dumped into teams.json to store student data on workouts (plus the list of teams they're on so you guys wouldn't have to manage merging more than one json file)
            workouts_dictionary = {"id" : user.id, "username" : user.username, "teams_on" : teams_on, "workouts" : [], "completed_workouts":[]}


            workouts_list_and_dict.append(workouts_dictionary)
            #v^v^ glue v^v^#
            with open("workouts.json","w") as tjson:
                json.dump(workouts_list_and_dict, tjson)
                
            #

            #when the dashboard is rendered after 
            if user.status == "Pending":
                return render_template('login.html', error="Awaiting Approval From Admin")
            else:
                return render_template('dashboard.html', workouts=session["workouts"], calories=session["calories"])
            #*****************************************************************************************************
            

        except Exception as e:
            db.session.rollback()
            print("Commit failed. Error:" + str(e))
            return render_template('signup.html', error="That username or email has already been taken.")
        #........................................................................................................................


    return render_template('signup.html', teams=teams_list)


@app.route('/addteam', methods=['POST', 'GET'])
def addteam():
#adding teams logic:
    if request.method == 'POST':

        newTeam = request.form['addedTeam']

        teams_list.append(newTeam)

        #replace old teams.json code with the updated teams_list
        with open("teams.json","w") as tjson:
            json.dump(teams_list, tjson)
    

    return redirect(url_for('dashboard'))



@app.route('/elevateAccess', methods=['POST', 'GET'])
def elevateAccess():
#adding teams logic:
    if request.method == 'POST':

        coach_name = request.form['ApproveButton']

        user = User.query.filter_by(username=coach_name).first()

        user.status = "None"
        db.session.commit()


    return redirect(url_for('requests'))



@app.route('/requests')
def requests():

    #find all accounts with the "Pending" status (and format them into a query / a.k.a. a database dictionary)
    pending_accounts = User.query.filter_by(status='Pending').all()
    print(pending_accounts)

    #for accounts in pending_accounts:
    #    print("USERNAME:")
    #    print(accounts.username)
    #I commented this out because it's a debugging loop I made, I might need it later, but probably not
    

    return render_template('requests.html', accounts=pending_accounts)

@app.route('/workout')
def workout():

    if "user" in session:


        with open("workouts.json","r") as tjson:
            workouts_list_and_dict = json.load(tjson)
                    

        workouts_list = workouts_list_and_dict[int(session["id"]) - 1] ["workouts"]

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

            user = User.query.filter_by(username=session["user"]).first()
            if user:
                user.age  = new_age
                user.goal = new_goal
                try:
                    db.session.commit()
                    session["age"]  = new_age
                    session["goal"] = new_goal
                except Exception:
                    db.session.rollback()

        return render_template('profile.html', username=session["user"], email=session["email"], age=session["age"], goal=session["goal"])
    
    else:
        return render_template('login.html')
#------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)