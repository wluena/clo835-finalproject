from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
import logging

app = Flask(__name__)

# --- 1. CONFIGURATION FROM K8S CONFIGMAPS/SECRETS ---
# Database Config [cite: 33, 42, 51]
DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER") 
DBPWD = os.environ.get("DBPWD")
DATABASE = os.environ.get("DATABASE") or "employees"
DBPORT = int(os.environ.get("DBPORT") or 3306)

# UI Config [cite: 24, 28, 34]
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_IMAGE_NAME = os.environ.get("S3_IMAGE_NAME") # Location from ConfigMap
STUDENT_NAME = os.environ.get("STUDENT_NAME")   # Name from ConfigMap

# Local storage for the background image [cite: 29, 30]
LOCAL_BG_PATH = "static/background.jpg"

# --- 2. S3 IMAGE DOWNLOAD LOGIC [cite: 26, 29] ---
def download_bg_from_s3():
    """Retrieves image from private S3 and stores it locally [cite: 26]"""
    if S3_BUCKET and S3_IMAGE_NAME:
        try:
            s3 = boto3.client('s3')
            if not os.path.exists('static'):
                os.makedirs('static')
            s3.download_file(S3_BUCKET, S3_IMAGE_NAME, LOCAL_BG_PATH)
            # Log the background image URL 
            print(f"DEBUG: Background image loaded from S3: s3://{S3_BUCKET}/{S3_IMAGE_NAME}")
        except Exception as e:
            print(f"Error fetching from S3: {e}")

# --- 3. DATABASE CONNECTION ---
try:
    db_conn = connections.Connection(
        host=DBHOST,
        port=DBPORT,
        user=DBUSER,
        password=DBPWD, 
        db=DATABASE
    )
except Exception as e:
    print(f"Database connection failed: {e}")

# --- 4. ROUTES ---
@app.route("/", methods=['GET', 'POST'])
def home():
    download_bg_from_s3() # Ensure image is current [cite: 57]
    return render_template('addemp.html', name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)

@app.route("/about", methods=['GET','POST'])
def about():
    return render_template('about.html', name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)
    
@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

    cursor = db_conn.cursor()
    try:
        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_sql,(emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = f"{first_name} {last_name}"
    finally:
        cursor.close()

    return render_template('addempoutput.html', name=emp_name, student_name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("getemp.html", name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)

@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']
    output = {}
    cursor = db_conn.cursor()

    try:
        select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
        cursor.execute(select_sql,(emp_id))
        result = cursor.fetchone()
        
        output["emp_id"] = result[0]
        output["first_name"] = result[1]
        output["last_name"] = result[2]
        output["primary_skills"] = result[3]
        output["location"] = result[4]
    except Exception as e:
        print(e)
    finally:
        cursor.close()

    return render_template("getempoutput.html", id=output.get("emp_id"), fname=output.get("first_name"),
                           lname=output.get("last_name"), interest=output.get("primary_skills"), 
                           location=output.get("location"), name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)

if __name__ == '__main__':
    # Flask application must listen on port 81 
    app.run(host='0.0.0.0', port=81, debug=True)