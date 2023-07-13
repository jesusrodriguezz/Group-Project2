from flask import Flask, render_template, redirect, request


app = Flask(__name__)
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid username or password. Please try again.'
        else:
            return redirect(url_for('login')) 
    return render_template('login.html', error=error)




    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
