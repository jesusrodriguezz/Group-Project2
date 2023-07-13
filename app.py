from flask import Flask, render_template, redirect, url_for, request
import sqlite3

app = Flask(__name__)

# Create the active_users table
def create_table():
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS active_users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )''')

    con.commit()
    con.close()

# Insert a user into the active_users table
def create_user(username, password):
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute("INSERT INTO active_users (username, password) VALUES (?, ?)", (username, password))

    con.commit()
    con.close()

# Route for users

@app.route('/users', methods=['GET', 'POST'])
def get_users():
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute("SELECT id, username FROM active_users")
    users = cursor.fetchall()

    con.close()

    return render_template('users.html', users=users)
    
# deletes users, I thought maybe this could be helpful
def delete_user(username):
    con = sqlite3.connect('users.db')
    cursor = con.cursor()

    cursor.execute("DELETE FROM active_users WHERE username = ?", (username,))

    con.commit()
    con.close()
    
# Route for login
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        con = sqlite3.connect('users.db')
        cursor = con.cursor()

        name = request.form['name']
        password = request.form['password']

        query = "SELECT username, password FROM active_users WHERE username= ? and password= ?"
        cursor.execute(query, (name, password))

        results = cursor.fetchall()

        if len(results) == 0:
            print("Invalid username or password. Please try again.")
        else:
            return render_template('home.html')

    return render_template('login.html')

# Run program
# I was having trouble connecting the database with the register page
# so I decided to not use it and only use the login page for now
# I added the create_user function so you can register users with their name and password

if __name__ == '__main__':
    # this is how you would add a user, after running make sure to comment out
    #create_user because if not, it will create it twice(I will fix that bug soon)
    #create_user("bob101", "pass101")
    create_table()
    app.run(debug=True, host="0.0.0.0")
