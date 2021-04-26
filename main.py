from flask import Flask, redirect, render_template, url_for, request, flash, session
import mysql.connector
from mysql.connector import errorcode
from datetime import timedelta
import time
import smtplib
from random import randint
from encrypt import *

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Please keep this key a secret'
app.permanent_session_lifetime = timedelta(days=1)

mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "", #add MySQL password
    database = "test",
    auth_plugin='mysql_native_password'
)
smtpEmail = "" #add your email
smtpPassword = "" #add your password
smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
smtpObj.starttls()
smtpObj.login(smtpEmail,smtpPassword)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        return render_template('index.html')

@app.route('/SignUp', methods=["POST", "GET"])
def signUp():
    if 'user' in session:
        return redirect('home')
    if request.method == "POST":
        userDetails = request.form
        firstname = userDetails['firstname']
        lastname = userDetails['lastname']
        email = userDetails['userEmail']
        password = userDetails['userPassword']
        day = userDetails['birthday_day']
        month = userDetails['birthday_month']
        year = userDetails['birthday_year']
        gender = userDetails['gender']
        DOB = day+"/"+month+"/"+year
        encrypted_password = encryption(password)
        mycursor = mydb.cursor(buffered=True)
        mycursor.execute("INSERT INTO credentials (firstname, lastname, email, password, DOB, gender) VALUES (%s, %s, %s, %s, %s, %s)", (firstname, lastname, email, encrypted_password, DOB, gender))
        mydb.commit()
        mycursor.close()
        generated_otp = str(randint(10000, 99999))
        smtpObj.sendmail('pricetracker000@gmail.com', email, 'Subject: OTP \nThis is a ONE TIME PASSWORD = '+generated_otp)
        return redirect(url_for('verify', false="?dg"+generated_otp[2:]+"2v4"+generated_otp[:2]+"4573747gssSIGNUP"))
    else:
        return render_template('signUp.html')

@app.route('/verify', methods=["POST", "GET"])
def verify():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        generated_otp = request.args['false']
        generated_otp = generated_otp[9:11] + generated_otp[3:6]
        false = request.args['false']
        direction = false[21:]
        if direction == "IDENTIFY":
            email = request.args['email']
            smtpObj.sendmail('pricetracker000@gmail.com', email, 'Subject: OTP \nThis is a ONE TIME PASSWORD = '+generated_otp)
        flash("OTP has been send to your email address")
        if request.method == "POST":
            entered_otp = request.form['otp']
            if entered_otp == generated_otp:
                if direction == "SIGNUP":
                    return redirect(url_for('signIn'))
                elif direction == "IDENTIFY":
                    return redirect(url_for('newCredentials', email=email))
            else:
                flash("Wrong OTP entered, check again")
    return render_template('verify.html')

@app.route('/login', methods=["POST", "GET"])
def signIn():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        if request.method == "POST":
            session.permanent = True
            userDetails = request.form
            email = userDetails['userEmail']
            password = userDetails['userPassword']
            encrypted_password = encryption(password)
            session['user'] = email
            mycursor = mydb.cursor(buffered=True)
            mycursor.execute("SELECT id from credentials where email = %s and password = %s", (email, encrypted_password))
            user_id = mycursor.fetchone()
            session['user_id'] = user_id[0]
            mycursor.close()
            if user_id == None:
                flash('Wrong Email or Password')
            else:
                print("id = ", session['user_id'],", ",session['user'], "User logged in")
                return redirect(url_for('home'))
    return render_template('signIn.html')
  
@app.route('/identify', methods=['POST', 'GET'])
def forgotPassword():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        if request.method == "POST":
            email = request.form['userEmail']
            mycursor = mydb.cursor(buffered=True)
            mycursor.execute("SELECT id from credentials where email = %s ", (email,))
            result = mycursor.fetchone()
            mycursor.close()
            if result == None:
                flash("Wrong email address or not signed up")
            else:
                generated_otp = str(randint(10000, 99999))
                return redirect(url_for('verify', false="?dg"+generated_otp[2:]+"2v4"+generated_otp[:2]+"4573747gssIDENTIFY", email=email))
    return render_template('identify.html')

@app.route('/change_password', methods=['POST', 'GET'])
def newCredentials():
    if 'user' in session:
        return redirect(url_for('home'))
    else:
        email = request.args['email']
        if request.method == "POST":
            userDetails = request.form
            password = userDetails['userPassword']
            confirm_password = userDetails['userRePassword']
            if password == confirm_password:
                encrypted_password = encryption(password)
                mycursor = mydb.cursor(buffered=True)
                mycursor.execute("UPDATE credentials set password = %s where email = %s", (password, email))
                mycursor.close()
                return redirect(url_for('signIn'))
            else:
                flash("Your Password and re-typed password does not match")
    return render_template('change_password.html')        

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' in session:
        todos = fetch("todo")    
        completed = fetch("completed_task") 
        if request.method == 'POST':
            #To-do
            if 'add_btn' in request.form:
                name = request.form['todo']
                mycursor = mydb.cursor(buffered=True)
                mycursor.execute("INSERT INTO todo(user_id, taskname) values(%s, %s)", (session['user_id'], name))
                mydb.commit()
                todos = fetch("todo")
                mycursor.close()
            elif 'completed_btn' in request.form:
                task_id = request.form['completed_btn']
                done(task_id)
                remove(task_id, "todo")
                todos = fetch("todo")
                completed = fetch("completed_task")
            elif 'remove_btn' in request.form:
                task_id = request.form['remove_btn']
                remove(task_id, "todo")
                todos = fetch("todo")
            
            #Completed
            elif 'addtask_btn' in request.form:
                task_id = request.form['addtask_btn']
                addToTodo(task_id)
                remove(task_id, "completed_task")
                todos = fetch("todo")
                completed = fetch("completed_task")
            elif 'removeCompleted_btn' in request.form:
                task_id = request.form['removeCompleted_btn']
                remove(task_id, "completed_task") 
                completed = fetch("completed_task")

         #   return redirect(url_for('home', todo=todos, completed=completed))

    else:
        return redirect(url_for('signIn'))
    return render_template('home.html', todo=todos, completed=completed)

@app.route('/signOut')
def logout():
    print("id = ", session['user_id'],", ",session['user'], "logged out")
    session.pop('user', None)
    return redirect('/')

####################################### End Routes ###################################################33



# Todo Operations
def fetch(table_name):
    mycursor = mydb.cursor(buffered=True)
    if table_name == "todo":
        mycursor.execute("SELECT task_id, taskname from todo where user_id = %s", (session['user_id'],))
    else:
        mycursor.execute("SELECT task_id, taskname from completed_task where user_id = %s", (session['user_id'],))
    result = mycursor.fetchall()
    mycursor.close()
    return result

def done(task_id):
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute("SELECT taskname from todo where user_id = %s and task_id = %s", (session['user_id'], task_id))
    result = mycursor.fetchone()
    mycursor.close()
    result = ','.join(result)
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute("INSERT INTO completed_task(user_id, taskname) VALUES(%s, %s)", (session['user_id'], result))
    mycursor.execute("DELETE from todo where user_id = %s and task_id = %s", (session['user_id'], task_id))
    mydb.commit()
    mycursor.close()

def remove(task_id, table_name):
    mycursor = mydb.cursor(buffered=True)
    if table_name == "todo":
        query = "DELETE FROM todo where user_id = %s and task_id = %s"   
        data = (session['user_id'], task_id)
    else:
        query = "DELETE FROM completed_task where user_id = %s and task_id = %s"  
        data = (session['user_id'], task_id) 
    mycursor.execute(query, data)
    mydb.commit()
    mycursor.close()

def addToTodo(task_id):
    mycursor = mydb.cursor(buffered=True)
    query = "SELECT taskname from completed_task where user_id = %s and task_id = %s"
    data = (session['user_id'], task_id)
    mycursor.execute(query, data)
    result = mycursor.fetchone()
    result = ','.join(result)
    mycursor.close()
    mycursor = mydb.cursor(buffered=True)
    query = "INSERT INTO todo(user_id, taskname) VALUES(%s, %s)"
    data = (session['user_id'], result)
    mycursor.execute(query, data)
    mydb.commit()
    mycursor.close()


if __name__ == '__main__':
    app.run(debug=True)
