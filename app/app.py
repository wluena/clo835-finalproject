from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
import logging

app = Flask(__name__)

# --- 1. CONFIGURATION ---
DBHOST = os.environ.get("DBHOST") or "mysql"
DBUSER = os.environ.get("DBUSER") or "root"   # Changed from "db-user" to "DBUSER"
DBPWD = os.environ.get("DBPWD")               # Changed from "db-password" to "DBPWD"
DATABASE = os.environ.get("DATABASE") or "employees"
DBPORT = int(os.environ.get("DBPORT") or 3306)

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_IMAGE_NAME = os.environ.get("S3_IMAGE_NAME")
STUDENT_NAME = os.environ.get("STUDENT_NAME") 
LOCAL_BG_PATH = "static/background.jpg"

# --- 2. S3 IMAGE DOWNLOAD LOGIC ---
def download_bg_from_s3():
    if S3_BUCKET and S3_IMAGE_NAME:
        try:
            s3 = boto3.client('s3')
            if not os.path.exists('static'):
                os.makedirs('static')
            s3.download_file(S3_BUCKET, S3_IMAGE_NAME, LOCAL_BG_PATH)
            print(f"DEBUG: Background image loaded from S3: s3://{S3_BUCKET}/{S3_IMAGE_NAME}")
        except Exception as e:
            print(f"Error fetching from S3: {e}")

# --- 3. RESILIENT DATABASE CONNECTION ---
def get_db_connection():
    """Returns a database connection, or None if it fails."""
    try:
        return connections.Connection(
            host=DBHOST,
            port=DBPORT,
            user=DBUSER,
            password=DBPWD, 
            db=DATABASE
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# --- 4. ROUTES ---
@app.route("/", methods=['GET', 'POST'])
def home():
    download_bg_from_s3()
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

    db_conn = get_db_connection()
    if not db_conn:
        return "Database is currently unavailable. Please try again in a few seconds.", 503

    cursor = db_conn.cursor()
    try:
        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_sql,(emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = f"{first_name} {last_name}"
        return render_template('addempoutput.html', name=emp_name, student_name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)
    except Exception as e:
        print(f"Insert error: {e}")
        return "Error saving data.", 500
    finally:
        cursor.close()
        db_conn.close()

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("getemp.html", name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)

@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']
    db_conn = get_db_connection()
    if not db_conn:
        return "Database is currently unavailable.", 503

    cursor = db_conn.cursor()
    try:
        select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
        cursor.execute(select_sql,(emp_id))
        result = cursor.fetchone()
        
        if result:
            output = {
                "emp_id": result[0],
                "first_name": result[1],
                "last_name": result[2],
                "primary_skills": result[3],
                "location": result[4]
            }
            return render_template("getempoutput.html", id=output["emp_id"], fname=output["first_name"],
                                   lname=output["last_name"], interest=output["primary_skills"], 
                                   location=output["location"], name=STUDENT_NAME, bg_image=LOCAL_BG_PATH)
        else:
            return "Employee not found", 404
    except Exception as e:
        print(f"Fetch error: {e}")
        return "Error fetching data.", 500
    finally:
        cursor.close()
        db_conn.close()

if __name__ == '__main__':
    # Download the image once at startup
    download_bg_from_s3() 
    app.run(host='0.0.0.0', port=81, debug=True)