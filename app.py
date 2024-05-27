from flask import Flask, render_template, request, send_file
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)


app.secret_key = 'abcde'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  
app.config['MYSQL_PASSWORD'] = '' 
app.config['MYSQL_DB'] = 'Final' 
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' 


mysql = MySQL(app)


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_tables():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name TEXT NOT NULL,
            data LONGBLOB NOT NULL,
            mime VARCHAR(255) NOT NULL,
            uname VARCHAR(255) NOT NULL,
            umail VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usinfo (
            id INT AUTO_INCREMENT PRIMARY KEY,
            umail TEXT NOT NULL,
            uspass TEXT NOT NULL
        )
    """)
    mysql.connection.commit()
    cursor.close()


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == 'POST':
        uname = request.form.get("user_name")
        umail = request.form.get("user_email")
        file = request.files['file']

        if file and allowed_file(file.filename):
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO data (name, data, mime, uname, umail) VALUES (%s, %s, %s, %s, %s)",
                           (secure_filename(file.filename), file.read(), file.mimetype, uname, umail))
            mysql.connection.commit()
            cursor.close()

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM data WHERE umail = %s", (umail,))
            userImg = cursor.fetchone()
            cursor.close()

            return render_template("base.html", uname=uname, imga=userImg)

    return render_template("index.html")


@app.route('/download/<int:image_id>')
def download(image_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM data WHERE id = %s", (image_id,))
    img = cursor.fetchone()
    cursor.close()

    return send_file(
        BytesIO(img['data']),
        mimetype=img['mime']
    )


@app.route('/success', methods=["POST", "GET"])
def success():
    if request.method == 'POST':
        passinp = request.form.get("xy")
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO usinfo (umail, uspass) VALUES (%s, %s)",
                       ('shiva@gmail.com', passinp))
        mysql.connection.commit()
        cursor.close()
        return render_template("success.html", msg="Account created")
    return render_template("success.html", msg="")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        dummy = request.form.get("ur_email")
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM data WHERE umail = %s", (dummy,))
        userImg = cursor.fetchone()
        cursor.close()
        return render_template("a.html", imga=userImg)
    return render_template("login.html")


@app.route('/dash', methods=["POST", "GET"])
def authenticate():
    if request.method == 'POST':
        usmail = request.form.get("ur_email")  # Use the email from the login form
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usinfo WHERE umail = %s", (usmail,))
        reqUser = cursor.fetchone()
        cursor.close()

        if not reqUser:
            return render_template("login.html", msg="User not found")

        passdata = reqUser['uspass']
        coordinates = [int(x) for x in passdata.split()]
        loginuser = request.form.get("passxy")
        logco = [int(x) for x in loginuser.split()]

        if len(coordinates) != len(logco):
            return render_template("login.html", msg="Invalid login coordinates")

        for i in range(len(coordinates)):
            if abs(logco[i] - coordinates[i]) > 20 :
                return render_template("dashboard.html", msg="")

        return render_template("login.html", msg="")
    return render_template("dashboard.html")


if __name__ == "__main__":

    create_tables()
    app.run(debug=True)