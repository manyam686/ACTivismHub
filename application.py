# INITIAL BARE BONES FOR APPLICATION LAYER
# 2/14/21
# This file runs the application, SQL queries and route direction will be in here
# Both flask and flask-mysqldb must be installed (on CL: pip install flask--mysqldb)

#IMPORT
#request is for get/post data, render_template is to render html pages
from flask import Flask, request, render_template, session, redirect
from flask_mysqldb import MySQL
import os, datetime
from werkzeug.utils import secure_filename

#INSTANTIATE
app = Flask(__name__)
app.secret_key = b'1234567'

#Instantiate
mysql = MySQL(app)

#Configure MySQL
app.config['MYSQL_HOST'] = 'activism-hub'
app.config['MYSQL_USER'] = 'dba'
app.config['MYSQL_PASSWORD'] = 'Password321$'
app.config['MYSQL_DB'] = 'remote_activismHub'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' #returns queries as dicts instead of default tuples


#Route with nothing appended (in our local machine, localhost:5000)
@app.route("/")
def index():
   #Establish connection
   cursor = mysql.connection.cursor()
   #Get list of clubs and IDs
   clubs = getClubs()
   #Get events
   cursor.execute('''SELECT * FROM testClub_event WHERE event_date > CURDATE()
                     UNION
                     SELECT * FROM testClub_event WHERE event_date = CURDATE() AND event_time > CURTIME()
                     ORDER BY event_date, event_time''')
   events = cursor.fetchall()
   return render_template("homePage.html",events=events,clubs=clubs)



#Route when a club page is clicked
@app.route("/clubPage")
def club_page():
   #Establish connection
   cursor = mysql.connection.cursor()
   #Get which club
   clubID = request.args.get("q")
   #Get club info
   cursor.execute('''SELECT * FROM testClub WHERE clubID = %s''',(clubID,))
   info = cursor.fetchall()[0]
   #Get events
   cursor.execute('''SELECT * FROM testClub_event WHERE event_date > CURDATE() AND clubID=%s
                     UNION
                     SELECT * FROM testClub_event WHERE event_date = CURDATE() AND event_time > CURTIME() AND
                     clubID=%s ORDER BY event_date, event_time''',(clubID,clubID))
   events = cursor.fetchall()
   #Get list of dicts of clubs
   clubs = getClubs()
   return render_template("clubPage.html",info=info,events=events,clubs=clubs)


#Route when user clicks login
@app.route("/login")
def login_page(message=""):
   #sample list of dicts of clubs
   clubs = getClubs()
   return render_template("login.html",clubs=clubs,message=message)


#Route when user clicks create account from login page
@app.route("/createAccount")
def create_account():
   #sample list of dicts of clubs
   clubs = getClubs()
   return render_template("create-account.html",clubs=clubs)


#Route when user clicks submit on login page
@app.route("/doLogin",methods=["POST"])
def do_login():
   cursor = mysql.connection.cursor()
   #get user and password
   user = request.form['Email']
   password = request.form['Password']
   #check if club email exists
   cursor.execute('''SELECT EXISTS(SELECT * FROM testClub WHERE club_email = %s) AS club_exists''',(user,))
   if cursor.fetchall()[0]['club_exists']==1:
       #get club ID and correct password
       cursor.execute('''SELECT clubID, password FROM testClub where club_email = %s''',(user,))
       result=cursor.fetchall()[0]
       clubID = result['clubID']
       correct_password = result['password']
       #simple authentication
       if password == correct_password:
           #add clubID to session and reroute to homepage
           session['club_id']=clubID
           return index()
       else:
           #if password incorrect, reload login page
           return login("Incorrect password.")
   else:
       return login("There is no account with that email.")


#Route when user clicks logout
@app.route("/logout")
def logout():
   #remove session variable for clubID
   session.pop('club_id',None)
   #reroute to home page
   return index()


#Route when user clicks submit on the create account page
@app.route("/enterAccount",methods=["POST"])
def enter_account():
   #instantiate cursor
   cursor = mysql.connection.cursor()
   #get form info
   email = request.form['clubEmail']
   clubName = request.form['club-name']
   adminName = request.form['admin-name']
   description = request.form['club-description']
   adminEmail = request.form['admin-email']
   password = request.form['password']
   #Insert new account info into club table
   cursor.execute('''INSERT INTO testClub(club_name,admin_name,about_info,club_email)
       VALUES(%s,%s,%s,%s)''',(clubName,adminName,description,email))
   mysql.connection.commit()
   #get club new club id
   cursor.execute('''SELECT clubID FROM testClub where club_name = %s''',(clubName,))
   clubID=cursor.fetchall()[0]['clubID']
   #Insert new account info into admin table
   cursor.execute('''INSERT INTO testClub_admin(club_name,clubID, admin_name,admin_email,password)
       VALUES(%s,%s,%s,%s,%s)''',(clubName,clubID,adminName,adminEmail,password))
   mysql.connection.commit()
   #reroute to home page
   return index()


#Gets list of club names and IDs
def getClubs():
   cursor = mysql.connection.cursor()
   cursor.execute('''SELECT club_name, clubID FROM testClub''')
   return cursor.fetchall()

#formats date - not in use
def formatDateFromSql(sqlDate):
    months = ['January','February','March','April','May','June','July',
        'August','September','October','November','December']
    year = sqlDate.year
    month = sqlDate.month
    day = sqlDate.day
    return months[month-1]+" "+str(day)+", "+str(year)

#formats times - not in use
def formatTimeFromSql(time):
    hours = (int)(time.seconds/3600)
    min = (int)((time.seconds/60)%60)
    if min==0:
        min='00'
    ampm = 'AM'
    if hours>12:
        time=time-12
        ampm='PM'
    return str(hours)+":"+str(min)+" "+ampm



#route when user clicks edit club profile from club page
@app.route("/editClub")
def editClub():
    cursor = mysql.connection.cursor()
    #get which club
    clubID = session['club_id']
    #Get club info
    cursor.execute('''SELECT * FROM testClub WHERE clubID = %s''',(clubID,))
    info = cursor.fetchall()[0]
    #get clubs
    clubs = getClubs()
    return render_template('editClub.html',clubs=clubs,info=info)


#when user clicks submit on edit club page
@app.route("/updateClub",methods=["POST"])
def updateClub():
    #get which club
    clubID = session['club_id']
    #instantiate cursor
    cursor = mysql.connection.cursor()
    #get form info
    club_name = request.form['club_name']
    about_info = request.form['about_info']
    meet_time = request.form['meet_time']
    meet_day = request.form['meet_day']
    meet_location = request.form['meet_location']
    facebook_link = request.form['facebook_link']
    instagram_link = request.form['instagram_link']
    twitter_link = request.form['twitter_link']
    website_link = request.form['website_link']
    #for optional fields, if empty set to none
    if meet_time == '':
            meet_time = None
    if meet_day == '':
            meet_day = None
    if meet_location == '':
            meet_location = None
    if facebook_link == '':
            facebook_link = None
    if instagram_link == '':
            instagram_link = None
    if twitter_link == '':
            twitter_link = None
    if website_link == '':
            website_link = None
    #Get image from form
    image = request.files['club_image']
    #if image inputted, save and make path
    if image.filename != '':
        club_image = "club_image_"+str(clubID)+"_"+secure_filename(image.filename)
        image.save(os.path.join(os.path.abspath(os.getcwd()),'static','clubImages',club_image))
    #if no image inputted, set image as what was in the database -- NOTE change when we display image on edit
    else:
        cursor.execute('''SELECT club_image FROM testClub WHERE clubID=%s''',(clubID,))
        club_image = cursor.fetchall()[0]['club_image']
    #Put new info in database
    cursor.execute('''UPDATE testClub SET club_name=%s,about_info=%s,meet_time=%s,meet_day=%s,meet_location=%s,
                    facebook_link=%s,instagram_link=%s,twitter_link=%s,website_link=%s,club_image=%s WHERE clubID = %s''',(club_name,about_info,
                    meet_time,meet_day,meet_location,facebook_link,instagram_link,twitter_link,website_link,club_image,clubID))
    mysql.connection.commit()
    #reroute to club page
    return redirect(f"/clubPage?q={clubID}")


#route when user clicks add event from add event page
@app.route("/addEvent",methods=["POST"])
def addEvent():
    #get which club
    clubID = session['club_id']
    #get form info
    event_name = request.form['event_name']
    event_type = request.form['event-type']
    event_date = request.form['event_date']
    event_time = request.form['event_time']
    event_location = request.form['event_location']
    event_description = request.form['event-description']
    #if optional fields empty, set as null
    if event_type == '':
        event_type = None
    #instantiate cursor
    cursor = mysql.connection.cursor()
    #get club name
    cursor.execute('''SELECT club_name FROM testClub where clubID = %s''',(clubID,))
    club_name=cursor.fetchall()[0]['club_name']
    #put new event in table NOTE - does not include image
    cursor.execute('''INSERT INTO testClub_event(event_name,club_name,clubID,event_date,event_time,event_location,
            event_description,event_type) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''',(event_name,club_name,clubID,event_date,
            event_time,event_location,event_description,event_type))
    mysql.connection.commit()

    #Get image from form
    image = request.files['event_image']
    #if image inputted, save and store
    if image.filename != '':
        #get eventID
        cursor.execute('''SELECT eventID FROM testClub_event WHERE event_name=%s AND clubID=%s AND
                event_date=%s''',(event_name,clubID,event_date))
        eventID = cursor.fetchall()[0]['eventID']
        #make image name
        event_image = "event_image_"+str(eventID)+"_"+secure_filename(image.filename)
        #save image
        image.save(os.path.join(os.path.abspath(os.getcwd()),'static','eventImages',event_image))
        #save image name in database
        cursor.execute('''UPDATE testClub_event SET event_image=%s WHERE eventID=%s''',(event_image,eventID))
        mysql.connection.commit()

    #rerender club page
    return redirect(f"/clubPage?q={clubID}")


#route when user clicks delete on event on club page
@app.route("/deleteEvent")
def deleteEvent():
    #Get which event
    eventID = request.args.get("q")
    #get which club
    clubID = session['club_id']
    #instantiate cursor
    cursor = mysql.connection.cursor()
    #delete from database
    cursor.execute('''DELETE FROM testClub_event WHERE eventID = %s''',(eventID,))
    mysql.connection.commit()
    #rerender club page
    return redirect(f"/clubPage?q={clubID}")


#route when user clicks submit on edit event
@app.route("/updateEvent",methods=["POST"])
def updateEvent():
    #get which club
    clubID = session['club_id']
    #get which event
    eventID = request.form['eventID']
    #get form info
    event_name = request.form['event_name']
    event_type = request.form['event_type']
    event_date = request.form['event_date']
    event_time = request.form['event_time']
    event_location = request.form['event_location']
    event_description = request.form['event_description']
    #if optional fields empty, set as null
    if event_type == '':
        event_type = None
    #instantiate cursor
    cursor = mysql.connection.cursor()
    #get image from form
    image = request.files['event_image']
    #if image inputted, save and make path
    if image.filename != '':
        event_image = "event_image_"+str(eventID)+"_"+secure_filename(image.filename)
        image.save(os.path.join(os.path.abspath(os.getcwd()),'static','eventImages',event_image))
    #if no image inputted, set image as what was in the database -- NOTE change when we display image on edit
    else:
        cursor.execute('''SELECT event_image FROM testClub_event WHERE eventID=%s''',(eventID,))
        event_image = cursor.fetchall()[0]['event_image']
    #Update event
    cursor.execute('''UPDATE testClub_event SET event_name=%s,event_date=%s,event_time=%s,event_location=%s,
            event_description=%s,event_type=%s,event_image=%s WHERE eventID=%s''',(event_name,event_date,
            event_time,event_location,event_description,event_type,event_image,eventID))
    mysql.connection.commit()

    #rerender club page
    return redirect(f"/clubPage?q={clubID}")


