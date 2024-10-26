from flask import Flask, render_template, request, redirect, url_for,session,flash,jsonify
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message #new, run pip install Flask-Mail itsdangerous
from itsdangerous import URLSafeTimedSerializer, SignatureExpired #new
from datetime import datetime, time, timedelta
from textblob import TextBlob #new
from collections import defaultdict
import MySQLdb.cursors
import re, os
import time



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app = Flask (__name__)
app.config["SECRET_KEY"] = "secretkey"
app.config["UPLOAD_FOLDER"] = "static/uploads"


app.config["MYSQL_HOST"] = "UniRide.mysql.pythonanywhere-services.com"
app.config["MYSQL_USER"] = "UniRide"
app.config["MYSQL_PASSWORD"] = "Noro151299$"
app.config["MYSQL_DB"] = "UniRide$uniride"
#mysql = MySQL(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'unirides327@gmail.com'  
app.config['MAIL_PASSWORD'] = 'rahq wfal gaqu fzyf'
app.config['MAIL_DEFAULT_SENDER'] = 'unirides327@gmail.com'

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

mysql = MySQL(app)

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to send verification emails
def send_verification_email(email, full_name):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = s.dumps(email, salt='email-confirm')
    confirm_url = url_for('confirm_email', token=token, _external=True)

    html = f'''
    <p>Hello, {full_name}!</p>
    <p>Thank you for signing up with UniRide. Please click on the link below to verify your email address:</p>
    <a href="{confirm_url}">{confirm_url}</a>
    <p>If you did not make this request, simply ignore this email.</p>
    '''

    msg = Message("Email Verification", recipients=[email])
    msg.html = html
    mail.send(msg)

@app.route('/resend_verification', methods=['POST'])
def resend_verification():
    email = request.form.get('email')
    
    if not email:
        flash('Email is required', 'danger')
        return redirect(url_for('email_verification'))

    # Lookup the user from the database to get the full name
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT FullName FROM user WHERE Email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        full_name = result[0]
        # Call your email sending function with both email and full_name
        send_verification_email(email, full_name)
        flash('Verification email resent. Please check your inbox.', 'success')
    else:
        flash('Email not found. Please register first.', 'danger')

    return redirect(url_for('login'))



@app.route('/email_verification', methods=['POST', 'GET'])
def email_verification():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please provide a valid email', 'danger')
            return redirect(url_for('email_verification'))

        # Retrieve full name based on the email from the User table
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT FullName FROM user WHERE Email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            full_name = result['FullName']
            # Pass both email and full_name to the send_verification_email function
            send_verification_email(email, full_name)
            flash('A new verification email has been sent to your email address.', 'success')
        else:
            flash('This email is not registered.', 'danger')
        return redirect(url_for('email_verification'))

    return render_template('EmailVerification.html')




@app.route("/login")
def login():
    return render_template("Login.html")


@app.route('/')
def landing_page():
    # Fetch testimonials from the database
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT FullName, AccountType, UserPhoto, FeedbackSubject, OtherSubject, FeedbackText, FeedbackDate, Rating 
        FROM testimonials 
        WHERE Rating >= 4
    ''')
    testimonials = cursor.fetchall()
    cursor.close()

    # Process the testimonials, ensuring missing fields (NULL values) are handled and sentiment is positive
    processed_testimonials = []
    
    for t in testimonials:
        feedback_text = t[5] if t[5] else 'No Feedback'
        
        # Perform sentiment analysis
        testimonial_sentiment = TextBlob(feedback_text).sentiment.polarity
        
        # Only include positive feedback (sentiment > 0)
        if testimonial_sentiment > 0:
            processed_testimonials.append({
                'FullName': t[0] if t[0] else 'No Name',
                'AccountType': t[1] if t[1] else 'No AccountType',
                'UserPhoto': t[2] if t[2] else 'https://mdbcdn.b-cdn.net/img/Photos/Avatars/avatar-1.webp',
                'FeedbackSubject': t[3] if t[3] else 'No Subject',
                'OtherSubject': t[4] if t[4] else 'No Other Subject',
                'FeedbackText': feedback_text,
                'FeedbackDate': t[6].strftime("%d %B, %Y") if t[6] else 'Unknown Date',
                'Rating': t[7] if t[7] else 0  # Rating column
            })

    return render_template('LandingPage.html', testimonials=processed_testimonials)



@app.route("/login", methods=["GET", "POST"])
def login_post():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]  # Admin/Driver/rider

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Handle Admin login
        if role == "Admin":
            cursor.execute("SELECT * FROM Admin WHERE Email = %s", (email,))
            account = cursor.fetchone()
            if account and check_password_hash(account["Password"], password):
                session["loggedin"] = True
                session["email"] = account["Email"]
                session["role"] = "Admin"
                return redirect(url_for("admin_dashboard"))
            else:
                flash("Incorrect Admin credentials", "danger")
                return redirect(url_for("login"))

        # Handle Driver or rider login
        cursor.execute("SELECT * FROM user WHERE Email = %s", (email,))
        account = cursor.fetchone()

        if account and check_password_hash(account["Password"], password):
            # Ensure the user has verified their email
            if account["Verified"] != '1':
                flash("Verify your email before logging in", "warning")
                return redirect(url_for("login"))

            # Ensure the selected role matches the account type
            if account["AccountType"] != role:
                flash("Invalid role selected", "danger")
                return redirect(url_for("login"))

            # Handle suspended accounts
            if account["Status"] == "Suspended":
                flash("Your account is suspended", "danger")
                return redirect(url_for("login"))

            # Store common session data
            session["loggedin"] = True
            session["id"] = account["UserID"]
            session["email"] = account["Email"]
            session["role"] = account["AccountType"]
            session["fullname"] = account["FullName"]

            # Handle Driver login
            if account["AccountType"] == "Driver":
                cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (account["UserID"],))
                driver = cursor.fetchone()
                if driver:
                    session["driver_id"] = driver["DriverID"]
                    # Store the driver's full name to avoid re-fetching later
                    session["fullname"] = account["FullName"]
                return redirect(url_for("driver_homepage"))

            # Handle rider login
            elif account["AccountType"] == "Rider":
                # Store the rider's full name
                session["fullname"] = account["FullName"]
                return redirect(url_for("rider_homepage"))

        else:
            flash("Incorrect email or password", "danger")
            return redirect(url_for("login"))







@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)
    session.pop("role", None)
    return redirect(url_for("login"))

@app.route('/register')
def register():
    return render_template('Register.html',account_created=False)

@app.route('/register', methods=['POST'])
def register_post():
    # Handle POST request (form submission)
    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    age = request.form['age']
    postal_code = request.form['postal_code']
    gender = request.form['gender']
    account_type = request.form['account_type']
    password = request.form['password']
    secret_question = request.form['secret_question']
    answer = request.form['answer']

    # Extract domain from the email
    email_domain = email.split('@')[-1]

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the email domain is in the AllowedDomains table
    cursor.execute('SELECT * FROM AllowedDomains WHERE DomainName = %s', (email_domain,))
    allowed_domain = cursor.fetchone()

    if not allowed_domain:
        flash("Email domain not allowed. Please use an allowed domain to register.", "danger")
        return render_template('Register.html', account_created=False)
    
    # Check if the email already exists in the User table
    cursor.execute('SELECT * FROM user WHERE Email = %s', (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        flash('Email already registered. Please use a different email.', 'danger')
        return render_template('Register.html', account_created=False)


    hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
    

    try:
        # Insert user data into the user table with 'Inactive' status and Verified = FALSE
        cursor.execute('''INSERT INTO user
                          (FullName, Email, Phone, Age, PostalCode, Gender, Password, SecretQuestion, Answer, AccountType, Status, Verified)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Inactive', FALSE)''', 
                          (full_name, email, phone, age, postal_code, gender, hashed_password, secret_question, answer, account_type))
        mysql.connection.commit()

        user_id = cursor.lastrowid  # Get the generated UserID
        
        if account_type == "Driver":
            car_model = request.form['car_model']
            car_color = request.form['car_color']
            plate_number = request.form['plate_number']
            capacity = request.form['capacity']
            
            # Insert driver data into the driver table
            cursor.execute('''INSERT INTO Driver
                              (UserID, FullName)
                              VALUES (%s, %s)''', 
                              (user_id,full_name))
            mysql.connection.commit()

            driver_id = cursor.lastrowid
            # Insert car details associated with the driver
            cursor.execute('''INSERT INTO Car
                              (DriverID, CarModel, CarColor, PlateNumber, Capacity)
                              VALUES (%s, %s, %s, %s, %s)''', 
                              (driver_id, car_model, car_color, plate_number, capacity))
            mysql.connection.commit()

        elif account_type == "Rider":
            # Insert rider data into the rider table
            cursor.execute('''INSERT INTO rider
                              (UserID, FullName)
                              VALUES (%s, %s)''', 
                              (user_id, full_name))
            mysql.connection.commit()

        # Send the verification email
        send_verification_email(email, full_name)

        flash('Account Successfully Created. Please check your email to verify your account', 'success')
        return render_template('Register.html', account_created=True)

    except Exception as e:
        mysql.connection.rollback()
        flash('Error creating account: {}'.format(str(e)), 'danger')
        return render_template('Register.html', account_created=False)

    finally:
        cursor.close()

@app.route('/confirm/<token>')  # new
def confirm_email(token):
    try:
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = s.loads(token, salt='email-confirm', max_age=3600)  # 1 hour expiration
    except SignatureExpired:
        flash('The confirmation link has expired. Please request a new one.', 'danger')
        return redirect(url_for('email_verification'))

    # Mark the user as verified and update status to Active
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE user SET Verified = 1, Status = 'Active' WHERE Email = %s", (email,))
    mysql.connection.commit()
    cursor.close()

    flash('Your email has been verified! You can now log in.', 'success')
    return redirect(url_for('login'))



@app.route("/email_check", methods=["GET", "POST"])
def email_check():
    if request.method == "POST":
        email = request.form["email"]

        cursor = mysql.connection.cursor()

        # Check the User table for the email
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        account = cursor.fetchone()

        cursor.close()

        if account:
            return redirect(url_for("reset_password", email=email))
        else:
            flash("Email does not exist", "danger")
    return render_template("EmailCheck.html")

@app.route('/reset-password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    cursor = mysql.connection.cursor()

    # Fetch the secret question from the user table
    cursor.execute("SELECT SecretQuestion FROM user WHERE Email = %s", (email,))
    result = cursor.fetchone()

    cursor.close()

    if result:
        secret_question = result[0]  # Accessing the first element in the tuple
    else:
        flash('Email does not exist in our records.', 'danger')
        return redirect(url_for('email_check'))

    if request.method == 'POST':
        secret_answer = request.form['secret_answer']

        # Verify the secret answer from the user table
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user WHERE Email = %s AND Answer = %s", (email, secret_answer))
        account = cursor.fetchone()

        cursor.close()

        if account:
            # Redirect to password reset page or process password reset
            flash('Answer is correct. You can now reset your password.', 'success')
            return redirect(url_for('password_reset', email=email))
        else:
            flash('Incorrect answer to the secret question.', 'danger')

    return render_template('ResetPassword.html', email=email, secret_question=secret_question)

@app.route('/check-answer', methods=['POST'])
def check_answer():
    data = request.json
    email = data['email']
    answer = data['answer']

    # Connect to MySQL
    cursor = mysql.connection.cursor()

    # Query the user table
    cursor.execute("SELECT Answer FROM user WHERE Email = %s", (email,))
    result = cursor.fetchone()

    cursor.close()

    if result and result[0].lower() == answer.lower():
        return jsonify({'correct': True})
    else:
        return jsonify({'correct': False})

@app.route('/password-reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('password_reset'))
        
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=8)

        cursor = mysql.connection.cursor()

        # Update the password in the user table
        cursor.execute('UPDATE user SET Password = %s WHERE Email = %s', (hashed_password, email))
        user_updated = cursor.rowcount  # Check if a row was updated

        if user_updated == 0:
            flash('Email does not exist in our records.', 'danger')
            cursor.close()
            return redirect(url_for('password_reset'))

        mysql.connection.commit()
        cursor.close()

        flash('Password successfully reset', 'success')
        return render_template('PasswordReset.html', password_reset_success=True)

    return render_template('PasswordReset.html')

@app.route('/admin-domains', methods=['GET', 'POST'])
def manage_domains():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor for dictionaries
    
    if request.method == 'POST':
        # Get domain and organization details from the form
        domain_name = request.form.get('domain_name')
        organization = request.form.get('organization')

        # Insert the new domain into the AllowedDomains table
        try:
            cursor.execute('INSERT INTO AllowedDomains (DomainName, Organization) VALUES (%s, %s)', 
                           (domain_name, organization))
            mysql.connection.commit()
            flash('Domain successfully added', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error adding domain: {str(e)}', 'danger')

    # Retrieve all allowed domains for display
    cursor.execute('SELECT * FROM AllowedDomains')
    domains = cursor.fetchall()
    
    cursor.close()

    return render_template('AdminManageDomains.html', domains=domains)

@app.route('/check-duplicate-domain', methods=['POST'])
def check_duplicate_domain():
    domain_name = request.json.get('domain_name')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM AllowedDomains WHERE DomainName = %s', (domain_name,))
    domain = cursor.fetchone()
    cursor.close()

    if domain:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})




@app.route('/admin/remove-domain/<int:domain_id>', methods=['POST'])
def remove_domain(domain_id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute('DELETE FROM AllowedDomains WHERE DomainID = %s', (domain_id,))
        mysql.connection.commit()
        flash('Domain successfully removed', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error removing domain: {str(e)}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('manage_domains'))





@app.route('/admin-dashboard', methods=['GET'])
def admin_dashboard():
    user_type = request.args.get('userType', '')  # Get userType from search, default to empty string
    search_by = request.args.get('searchBy', '')
    search_value = request.args.get('Keyword', '').strip()  # Renamed to match the HTML input name

    # Base query to fetch all users initially
    query = '''
        SELECT u.UserID, u.FullName, u.Email, u.Phone, u.Status,
               COALESCE(r.Rating, 0.0) AS RiderRating, 
               COALESCE(d.Rating, 0.0) AS DriverRating,
               c.CarModel, c.CarColor, c.PlateNumber, c.Capacity,
               u.AccountType
        FROM user u
        LEFT JOIN rider r ON u.UserID = r.UserID
        LEFT JOIN driver d ON u.UserID = d.UserID
        LEFT JOIN car c ON d.DriverID = c.DriverID
    '''
    
    params = []
    where_clauses = []

    # If userType is selected, apply it to the query
    if user_type:
        where_clauses.append('u.AccountType = %s')
        params.append(user_type)

    # Handle keyword searches across multiple fields if no specific searchBy is selected
    if search_value:
        keyword_conditions = []
        if not search_by:  # If no specific filter, search across multiple fields
            keyword_conditions.append('u.FullName LIKE %s')
            keyword_conditions.append('u.Phone LIKE %s')
            keyword_conditions.append('u.Email LIKE %s')
            keyword_conditions.append('u.Status LIKE %s')
            keyword_conditions.append('COALESCE(r.Rating, 0.0) LIKE %s')
            keyword_conditions.append('COALESCE(d.Rating, 0.0) LIKE %s')
            keyword_conditions.append('c.CarModel LIKE %s')
            keyword_conditions.append('c.CarColor LIKE %s')
            keyword_conditions.append('c.PlateNumber LIKE %s')
            keyword_conditions.append('c.Capacity LIKE %s')

            # Append the same keyword for all search fields
            params.extend([f'%{search_value}%'] * len(keyword_conditions))
            where_clauses.append('(' + ' OR '.join(keyword_conditions) + ')')

        else:  # If a specific filter is selected, apply it
            if search_by == 'FullName':
                where_clauses.append('u.FullName LIKE %s')
            elif search_by == 'Phone':
                where_clauses.append('u.Phone LIKE %s')
            elif search_by == 'Email':
                where_clauses.append('u.Email LIKE %s')
            elif search_by == 'Status':
                where_clauses.append('u.Status LIKE %s')
            elif search_by == 'Rating':
                if user_type == 'rider':
                    where_clauses.append('COALESCE(r.Rating, 0.0) LIKE %s')
                else:  # Driver
                    where_clauses.append('COALESCE(d.Rating, 0.0) LIKE %s')
            elif user_type == 'Driver' and search_by in ['CarModel', 'CarColor', 'PlateNumber', 'Capacity']:
                where_clauses.append(f'c.{search_by} LIKE %s')

            params.append(f'%{search_value}%')

    # Append WHERE clauses to the query if any exist
    if where_clauses:
        query += ' WHERE ' + ' AND '.join(where_clauses)

    # Execute the query
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, params)
    users = cursor.fetchall()
    cursor.close()

    # Handle case where no users are found
    if not users:
        flash('No users found for the given search criteria.', 'warning')

    # Render the page, users will be empty if no results found
    return render_template('AdminDashboard.html',
        users=users,
        userType=user_type,
        searchBy=search_by,
        keyword=search_value
    )


@app.route('/change_status/<int:user_id>/<action>', methods=['POST'])
def change_status(user_id, action):
    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM User WHERE UserID = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404

    new_status = 'Suspended' if action == 'suspend' else 'Active'

    cursor.execute("UPDATE user SET Status = %s WHERE UserID = %s", (new_status, user_id))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'success': True})



@app.route('/admin-update-driver', methods=['POST'])
def admin_update_driver():
    data = request.get_json()

    driver_id = data.get('driver_id')
    fullname = data.get('fullname')
    phone = data.get('phone')
    email = data.get('email')
    car_model = data.get('carModel')
    colour = data.get('colour')

    cursor = mysql.connection.cursor()

    try:
        # Update user table (common fields)
        cursor.execute('''
            UPDATE user 
            SET FullName = %s, Phone = %s, Email = %s 
            WHERE UserID = %s
        ''', (fullname, phone, email, driver_id))

        # Update car table (car-specific fields for drivers)
        cursor.execute('''
            UPDATE Car 
            SET CarModel = %s, CarColor = %s 
            WHERE DriverID = %s
        ''', (car_model, colour, driver_id))

        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True})
    except Exception as e:
        cursor.close()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin-update-rider', methods=['POST'])
def admin_update_rider():
    data = request.get_json()

    rider_id = data.get('rider_id')
    fullname = data.get('fullname')
    phone = data.get('phone')
    email = data.get('email')

    cursor = mysql.connection.cursor()

    try:
        # Update user table (common fields)
        cursor.execute('''
            UPDATE user 
            SET FullName = %s, Phone = %s, Email = %s 
            WHERE UserID = %s
        ''', (fullname, phone, email, rider_id))

        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True})
    except Exception as e:
        cursor.close()
        return jsonify({'success': False, 'error': str(e)})



@app.route('/admin-trips')
def admin_trips():
    # Connect to MySQL
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Query to fetch trip details from the Trip table
    cursor.execute('''
        SELECT 
            t.TripID, 
            t.Date, 
            t.PickUpTime, 
            t.DropOffTime, 
            t.From AS PickupLocation, 
            t.To AS DropOffLocation, 
            t.NoOfPassengers, 
            t.Status AS TripStatus,
            r.FullName AS RiderName,
            d.FullName AS DriverName,
            c.PlateNumber
        FROM 
            trip t
        JOIN 
            rider r ON t.TripInitiatorID = r.RiderID  -- Join with User table for Rider info
        LEFT JOIN 
            driver d ON t.DriverID = d.DriverID      -- Join with Driver table for Driver info
        LEFT JOIN 
            car c ON d.DriverID = c.DriverID         -- Join with Car table for vehicle info
    ''')

    trips = cursor.fetchall()  # Get all rows
    cursor.close()

    # Pass the fetched trip data to the template
    return render_template('AdminTrips.html', trips=trips)


@app.route('/admin-trips-search', methods=['GET'])
def admin_trips_search():
    search_by = request.args.get('searchBy')  # Column to search by
    search_value = request.args.get('searchValue')  # Value to search for

    # Mapping of search fields to database columns
    search_fields = {
        'TripID': 't.TripID',
        'PlateNumber': 'c.PlateNumber',
        'PickupLocation': 't.From',
        'DropOffLocation': 't.To',
        'Date': 't.Date',
        'TripStatus': 't.Status',
        'RiderName': 'u.FullName',
        'DriverName': 'd.FullName'
    }

    # Validate the search field
    if search_by in search_fields:
        db_column = search_fields[search_by]
    else:
        return "Invalid search field", 400

    # SQL query to search for the trip details
    query = f'''
        SELECT 
            t.TripID, 
            u.FullName AS RiderName, 
            d.FullName AS DriverName, 
            c.PlateNumber, 
            t.From AS PickupLocation, 
            t.To AS DropOffLocation, 
            t.PickUpTime, 
            t.DropOffTime, 
            t.Date, 
            t.NoOfPassengers, 
            t.Status AS TripStatus
        FROM trip t
        LEFT JOIN user u ON t.TripInitiatorID = u.UserID -- Join User table for Rider info
        LEFT JOIN driver d ON t.DriverID = d.DriverID    -- Join Driver table for Driver info
        LEFT JOIN car c ON d.DriverID = c.DriverID       -- Join Car table for vehicle info
        WHERE {db_column} LIKE %s
    '''

    search_pattern = f"%{search_value}%"  # Use a pattern for partial matching

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, (search_pattern,))
    trips = cursor.fetchall()
    cursor.close()

    # Render the template with the filtered trips
    return render_template('AdminTrips.html', trips=trips, searchBy=search_by, searchValue=search_value)

@app.route('/force_complete/<int:trip_id>', methods=['POST'])
def force_complete(trip_id):
    # Connect to the database
    conn = mysql.connection
    cursor = conn.cursor()

    # SQL Query to update the trip status to 'Completed'
    update_query = """
    UPDATE trip
    SET Status = 'Completed'
    WHERE TripID = %s AND Status = 'Ongoing'
    """

    try:
        # Execute the update query
        cursor.execute(update_query, (trip_id,))
        conn.commit()

        # Check if any row was updated
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Trip has been updated as completed'})
        else:
            return jsonify({'success': False, 'message': 'Fail to update trip status'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()

@app.route('/admin-report')
def admin_report():
    # Connect to MySQL
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # SQL query to join issue reports with the driver or rider table based on the reporter type
    cursor.execute('''
        SELECT 
            ir.ReportID AS CaseID,
            u.FullName AS ReporterName,
            ir.ReporterType AS Role,
            ir.Reason,
            ir.ReportDate AS Date,
            ir.Description AS Details,
            ir.ReportStatus AS Status,
            ir.AdminResponse AS AdminResponse,
            ir.TripID,
            t.From AS PickupLocation,
            t.To AS DropOffLocation
        FROM 
            issueReports ir
        JOIN 
            user u ON ir.ReporterID = u.UserID
        LEFT JOIN 
            trip t ON ir.TripID = t.TripID
    ''')

    reports = cursor.fetchall()
    cursor.close()

    # Pass the fetched report data to the template
    return render_template('AdminReport.html', reports=reports)

# For report search
@app.route('/admin_report_search', methods=['GET'])
def admin_report_search():
    search_by = request.args.get('searchBy')
    search_value = request.args.get('searchValue')

    # Prepare the SQL query based on the search criteria
    if search_by and search_value:
        search_fields = {
            'CaseID': 'ir.ReportID',
            'ReporterName': 'u.FullName',
            'Reason': 'ir.Reason',
            'Date': 'ir.ReportDate',
            'Status': 'ir.ReportStatus'
        }

        # Check if the selected search field is valid
        if search_by not in search_fields:
            return jsonify({'success': False, 'message': 'Invalid search field'}), 400

        query = f'''
            SELECT 
                ir.ReportID AS CaseID,
                u.FullName AS ReporterName,
                ir.Reason,
                ir.ReportDate AS Date,
                ir.Description AS Details,
                ir.ReportStatus AS Status,
                ir.TripID,
                t.From AS PickupLocation,
                t.To AS DropOffLocation
            FROM 
                IssueReports ir
            JOIN 
                user u ON ir.ReporterID = u.UserID
            LEFT JOIN 
                trip t ON ir.TripID = t.TripID
            WHERE 
                {search_fields[search_by]} LIKE %s
        '''
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query, (f'%{search_value}%',))
        reports = cursor.fetchall()
        cursor.close()

        return render_template('AdminReport.html', reports=reports)
    else:
        # If no search criteria is given, return all reports
        return admin_report()
    
@app.route('/update_case_status', methods=['POST'])
def update_case_status():
    data = request.get_json()
    case_id = data.get('case_id')

    if not case_id:
        return jsonify({'success': False, 'message': 'Case ID is missing'}), 400

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Update the status to 'Under Review' and set the admin response
        cursor.execute("""
            UPDATE IssueReports 
            SET ReportStatus = 'Under Review', AdminResponse = 'Case Currently Under Review by Support Team'
            WHERE ReportID = %s
        """, (case_id,))
        
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True, 'message': 'Status updated to Under Review with admin response'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@app.route('/get_report_details/<int:case_id>', methods=['GET'])
def get_report_details(case_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Query to fetch report and trip details
        cursor.execute('''
            SELECT 
                ir.ReportID AS CaseID,
                u.FullName AS ReporterName,
                ir.ReporterType AS Role,
                ir.Reason,
                ir.ReportDate AS Date,
                ir.Description AS Details,
                ir.ReportStatus AS Status,
                ir.AdminResponse,
                ir.TripID,
                t.From AS PickupLocation,
                t.To AS DropOffLocation,
                t.Date AS TripDate,
                t.PickUpTime,
                t.DropOffTime,
                t.NoOfPassengers,
                d.FullName AS DriverName
            FROM 
                issueReports ir
            JOIN 
                user u ON ir.ReporterID = u.UserID
            LEFT JOIN 
                trip t ON ir.TripID = t.TripID
            LEFT JOIN 
                driver d ON t.DriverID = d.DriverID
            WHERE 
                ir.ReportID = %s
        ''', (case_id,))
        
        report_details = cursor.fetchone()
        cursor.close()

        if not report_details:
            return jsonify({'success': False, 'message': 'Report not found'}), 404

        # Convert `PickUpTime` and `DropOffTime` from timedelta to string (HH:MM)
        if report_details['PickUpTime']:
            report_details['PickUpTime'] = (datetime.min + report_details['PickUpTime']).time().strftime('%H:%M')
        else:
            report_details['PickUpTime'] = "N/A"
        
        if report_details['DropOffTime']:
            report_details['DropOffTime'] = (datetime.min + report_details['DropOffTime']).time().strftime('%H:%M')
        else:
            report_details['DropOffTime'] = "N/A"

        # Return the report and trip details as JSON
        return jsonify({'success': True, 'report_details': report_details})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500




@app.route('/close_case', methods=['POST'])
def close_case():
    data = request.get_json()
    case_id = data.get('case_id')
    admin_response = data.get('admin_response')

    if not case_id:
        return jsonify({'success': False, 'message': 'Case ID is missing'}), 400

    if not admin_response:
        return jsonify({'success': False, 'message': 'Admin response is missing'}), 400

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check the current status of the case
        cursor.execute("SELECT ReportStatus FROM IssueReports WHERE ReportID = %s", (case_id,))
        case = cursor.fetchone()

        if not case:
            return jsonify({'success': False, 'message': 'Case not found'}), 404

        if case['ReportStatus'] == 'Closed':
            return jsonify({'success': False, 'message': 'Case is already closed'}), 400

        # Update the status to 'Closed' and add the admin response
        cursor.execute('''
            UPDATE IssueReports 
            SET ReportStatus = 'Closed', AdminResponse = %s 
            WHERE ReportID = %s
        ''', (admin_response, case_id))
        
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True, 'message': 'Case closed successfully and admin response updated'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Rider Pages

@app.route('/get-trip-data', methods=['GET'])
def get_trip_data():
    cursor = mysql.connection.cursor()
    
    # Modify query to count only rider-initiated trips
    query = """
        SELECT MONTHNAME(Date) AS month, COUNT(*) AS trip_count
        FROM trip
        WHERE Date BETWEEN '2024-07-01' AND '2024-12-31'
          AND TripInitiatorType = 'Rider'
        GROUP BY MONTH(Date), month
        ORDER BY MONTH(Date);
    """
    
    cursor.execute(query)
    results = cursor.fetchall()

    # Convert query result to a dictionary
    trip_data = {month: count for month, count in results}
    
    cursor.close()
    return jsonify(trip_data)



@app.route("/rider-homepage", methods=["GET", "POST"])
def rider_homepage():
    userID = session.get('id')  # Get UserID from session
    show_modal = False

    # Fetch the RiderID associated with the UserID from the session
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT RiderID FROM rider WHERE UserID = %s", (userID,))
    rider = cursor.fetchone()

    if not rider:
        flash('Rider not found!', 'danger')
        return redirect(url_for('login'))  # Handle rider not found

    riderID = rider['RiderID']
    #print(f"UserID: {userID}, RiderID: {riderID}")  # Debugging

    if request.method == 'POST':
        driver_gender = request.form.get("driverGender", "Any")
        driver_age = request.form.get('driverAge', "Any")
        pets = request.form.get("pets", "Any")
        passenger_gender = request.form.get("passengerGender", "Any")
        passenger_age = request.form.get("passengerAge", "Any")
        user_type = request.form.get("studentStaff", "Any")

        cursor.execute('''
            INSERT INTO riderpreferences
            (riderId, driverGender, driverAge, pets, passengerGender, passengerAge, userType)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (riderID, driver_gender, driver_age, pets, passenger_gender, passenger_age, user_type))
        mysql.connection.commit()
        flash("Preferences saved successfully", "success")
        return redirect(url_for("rider_homepage"))

    cursor.execute("SELECT * FROM riderpreferences WHERE riderId = %s", (riderID,))
    preferences = cursor.fetchone()
    if preferences is None:
        show_modal = True

    current_month = datetime.now().month
    current_year = datetime.now().year

    # Query for total completed trips
    cursor.execute("""
        SELECT COUNT(*) AS total_completed 
        FROM trip 
        WHERE Status = 'Completed' AND TripInitiatorID = %s
    """, (userID,))
    total_completed = cursor.fetchone()['total_completed']

    # Query for completed trips in the current month
    cursor.execute("""
        SELECT COUNT(*) AS completed_current_month 
        FROM trip 
        WHERE Status = 'Completed' 
          AND MONTH(Date) = %s AND YEAR(Date) = %s
          AND TripInitiatorID = %s
    """, (current_month, current_year, userID))
    completed_current_month = cursor.fetchone()['completed_current_month']

    # Query for upcoming trips
    cursor.execute("""
        SELECT COUNT(*) AS upcoming_trips 
        FROM trip 
        WHERE Status = 'Planned' AND TripInitiatorID = %s
    """, (userID,))
    upcoming_trips = cursor.fetchone()['upcoming_trips']

    # Calculate total carbon savings across all trips
    cursor.execute("""
        SELECT Distance, NoOfPassengers 
        FROM trip 
        WHERE TripInitiatorID = %s
    """, (userID,))
    trips = cursor.fetchall()

    total_carbon_savings = 0.0  # Initialize total savings

    for trip in trips:
        distance = trip['Distance'] if trip['Distance'] is not None else 0.0
        occupants = trip['NoOfPassengers'] or 1  # Default to 1 if not specified

        # Calculate baseline emission (each person drives alone)
        baseline_emission = 251 * distance  # 251 grams/km * distance

        # Calculate actual emission for the carpool trip
        actual_emission = baseline_emission / occupants

        # Calculate emission reduction for this trip
        emission_reduction = baseline_emission - actual_emission

        # Accumulate the total savings
        total_carbon_savings += emission_reduction

    # Convert total savings to kg if it exceeds 1000 grams
    if total_carbon_savings >= 1000:
        formatted_carbon_savings = f"{total_carbon_savings / 1000:.2f} kg"
    else:
        formatted_carbon_savings = f"{total_carbon_savings:.2f} g"

    print(f"Total Trips Completed: {total_completed}")
    print(f"Completed Trips in {current_month}: {completed_current_month}")
    print(f"Upcoming Trips: {upcoming_trips}")
    print(f"Total Carbon Savings: {formatted_carbon_savings}")

    cursor.close()

    return render_template(
        "RiderHomePage.html", 
        show_modal=show_modal, 
        preferences=preferences, 
        total_completed=total_completed, 
        completed_current_month=completed_current_month,
        upcoming_trips=upcoming_trips,
        carbon_savings=formatted_carbon_savings,
        now=datetime.now()
    )


@app.route("/rider-dashboard")
def rider_dashboard():
    userID = session.get('id')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the RiderID associated with the UserID
    cursor.execute("SELECT RiderID FROM rider WHERE UserID = %s", (userID,))
    rider = cursor.fetchone()

    if not rider:
        flash("You are not logged in as a rider", "error")
        return redirect(url_for("login"))

    rider_id = rider['RiderID']

    # Query trips where the rider is the initiator (excluding 'Completed' trips)
    cursor.execute('''
        SELECT trip.*, 
               IFNULL(driver.FullName, 'Searching for Driver') AS DriverName,
               1 AS is_initiator
        FROM trip 
        LEFT JOIN driver ON trip.DriverID = driver.DriverID
        WHERE trip.TripInitiatorID = %s AND trip.Status IN ('Planned', 'Ongoing')
        ORDER BY trip.Date DESC, trip.PickUpTime DESC
    ''', (userID,))

    trips_initiated = cursor.fetchall()

    # Collect the trip IDs of the trips the rider has initiated
    initiated_trip_ids = [trip['TripID'] for trip in trips_initiated]

    # If there are no initiated trip IDs, modify the query accordingly
    if initiated_trip_ids:
        cursor.execute('''
            SELECT trip.*, 
                   driver.FullName AS DriverName,
                   (SELECT COUNT(*) FROM tripriders WHERE tripriders.TripID = trip.TripID) AS current_passengers,
                   0 AS is_initiator
            FROM trip
            JOIN tripriders ON trip.TripID = tripriders.TripID
            LEFT JOIN driver ON trip.DriverID = driver.DriverID
            WHERE tripriders.RiderID = %s AND trip.TripID NOT IN %s AND trip.Status IN ('Planned', 'Ongoing')
            ORDER BY trip.Date DESC, trip.PickUpTime DESC
        ''', (rider_id, tuple(initiated_trip_ids)))
    else:
        cursor.execute('''
            SELECT trip.*, 
                   driver.FullName AS DriverName,
                   (SELECT COUNT(*) FROM tripriders WHERE tripriders.TripID = trip.TripID) AS current_passengers,
                   0 AS is_initiator
            FROM trip
            JOIN tripriders ON trip.TripID = tripriders.TripID
            LEFT JOIN driver ON trip.DriverID = driver.DriverID
            WHERE tripriders.RiderID = %s AND trip.Status IN ('Planned', 'Ongoing')
            ORDER BY trip.Date DESC, trip.PickUpTime DESC
        ''', (rider_id,))

    trips_joined = cursor.fetchall()

    # Combine both initiated and joined trips
    all_trips = trips_initiated + trips_joined

    # Convert date and time formats for each trip
    for trip in all_trips:
        trip['Date'] = datetime.strptime(str(trip['Date']), '%Y-%m-%d').strftime('%d/%m/%Y')
        trip['PickUpTime'] = (datetime.min + trip['PickUpTime']).time().strftime('%H:%M')
        if trip['DropOffTime']:
            trip['DropOffTime'] = (datetime.min + trip['DropOffTime']).time().strftime('%H:%M')

        # Add chat URL dynamically using trip ID
        trip['chat_url'] = url_for('rider_trip_chat', trip_id=trip['TripID'])

    cursor.close()

    return render_template("riderdashboard.html", trips=all_trips)





@app.route("/update_trip", methods=["POST"])
def update_trip():
    if request.method == "POST":
        trip_id = request.form.get("trip_id")
        from_location = request.form.get("from")
        to_location = request.form.get("to")
        pick_up_time = request.form.get("pick_up_time")
        date = request.form.get("date")
        totalpassengers = int(request.form.get("passengers"))
        no_of_guest = totalpassengers-1
        cursor = mysql.connection.cursor()

        try:
            # Update the trip in the database
            cursor.execute('''
                UPDATE trip 
                SET `From` = %s, `To` = %s, PickUpTime = %s, Date = %s, NoOfPassengers = %s, GuestCount = %s
                WHERE TripID = %s
            ''', (from_location, to_location, pick_up_time, date, totalpassengers, no_of_guest, trip_id))
            
            mysql.connection.commit()
            flash("Trip updated successfully", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating trip: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for("rider_dashboard"))

@app.route("/rider-profile", methods=["GET", "POST"])
def rider_profile():
    userID = session.get("id")  # Get UserID from session
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the RiderID associated with the UserID from the session
    cursor.execute("SELECT RiderID FROM rider WHERE UserID = %s", (userID,))
    rider = cursor.fetchone()
    
    if not rider:
        # Handle the case where the rider is not found
        flash('Rider not found!', 'danger')
        return redirect(url_for('login'))  # or another route as needed

    # Fetch the current user data along with the rating
    cursor.execute("""
        SELECT u.FullName, u.Phone, u.Email, u.Picture, r.Rating 
        FROM user u 
        JOIN rider r ON u.UserID = r.UserID 
        WHERE u.UserID = %s
    """, (userID,))
    user = cursor.fetchone()

    # Calculate the average rating for the driver
    cursor.execute("""
        SELECT AVG(Rating) as avg_rating 
        FROM feedbackrating 
        WHERE ToUserID = %s
    """, (userID,))
    avg_rating_result = cursor.fetchone()
    avg_rating = round(avg_rating_result['avg_rating'], 1) if avg_rating_result['avg_rating'] else 0
    

    if request.method == "POST":
        phone = request.form.get("phone")
        picture = request.files.get("picture")

        try:
            if picture:
                # Save the new profile picture
                picture_filename = secure_filename(picture.filename)
                picture_path = os.path.join(app.config["UPLOAD_FOLDER"], picture_filename)
                picture.save(picture_path)

                # Update both phone and picture in the database
                cursor.execute("UPDATE user SET Phone = %s, Picture = %s WHERE UserID = %s", (phone, picture_filename, userID))
            else:
                # Just update the phone number if no picture is uploaded
                cursor.execute("UPDATE user SET Phone = %s WHERE UserID = %s", (phone, userID))

            mysql.connection.commit()
            flash("Profile updated successfully!", "success")

        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating profile: {e}", "danger")

        finally:
            cursor.close()

        return redirect(url_for("rider_profile"))

    return render_template("RiderProfile.html", user=user, avg_rating=avg_rating)

# Helper function to calculate carbon savings
def calculate_carbon_savings(distance):
    """Assume 0.12 kg CO2 savings per km for each trip."""
    return round(distance * 0.12, 2)

@app.route("/rider-createTrip", methods=["GET", "POST"])
def rider_createtrip():
    userID = session.get('id')  # Get UserID from session
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the RiderID associated with the UserID from the session
    cursor.execute("SELECT RiderID FROM rider WHERE UserID = %s", (userID,))
    rider = cursor.fetchone()

    if not rider:
        flash('Rider not found!', 'danger')
        return redirect(url_for('login'))

    riderID = rider['RiderID']  # Use the fetched RiderID

    # Load user preferences if they exist
    cursor.execute("SELECT * FROM RiderPreferences WHERE RiderID = %s", (riderID,))
    preferences = cursor.fetchone()

    if request.method == "POST":
        try:
            trip_initiator_id = userID  # Set trip initiator to the current rider userID
            driver_id = request.form['driver_id'] if request.form['driver_id'] != '' else None
            date = request.form['date']
            pick_up_time = request.form['tripPickUpTime']
            from_location = request.form['from']
            to_location = request.form['to']
            no_of_passengers = int(request.form['tripPassengers'])  # Total number of passengers
            guest_count = no_of_passengers - 1  # Guests are total passengers minus 1
            distance = float(request.form['distance'])  # Distance in kilometers

            # Calculate carbon savings for this trip
            carbon_savings = calculate_carbon_savings(distance)

            # Preferences from the form
            drivers_gender = request.form['driversGender']
            drivers_age = request.form['driversAge']
            passengers_gender = request.form['passengersGender']
            passengers_age = request.form['passengersAge']
            pets = request.form['pets']
            user_type = request.form['studentStaff']

            # Update or insert rider preferences
            if preferences:
                if (preferences['DriverGender'] != drivers_gender or
                    preferences['DriverAge'] != drivers_age or
                    preferences['PassengerGender'] != passengers_gender or
                    preferences['PassengerAge'] != passengers_age or
                    preferences['Pets'] != pets or
                    preferences['UserType'] != user_type):
                    cursor.execute('''
                        UPDATE riderpreferences 
                        SET DriverGender = %s, DriverAge = %s, PassengerGender = %s, 
                            PassengerAge = %s, Pets = %s, UserType = %s 
                        WHERE RiderID = %s
                    ''', (drivers_gender, drivers_age, passengers_gender, passengers_age, pets, user_type, riderID))
                    mysql.connection.commit()
                    flash("Preferences updated.", "success")
            else:
                cursor.execute('''
                    INSERT INTO riderpreferences (RiderID, DriverGender, DriverAge, PassengerGender, PassengerAge, Pets, UserType)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (riderID, drivers_gender, drivers_age, passengers_gender, passengers_age, pets, user_type))
                mysql.connection.commit()
                flash("Preferences saved.", "success")

            # Insert the new trip into the database
            cursor.execute('''
                INSERT INTO trip (TripInitiatorID, TripInitiatorType, DriverID, Date, PickUpTime, DropOffTime, `From`, `To`, NoOfPassengers, GuestCount, Fare, Distance, CarbonSavings)
                VALUES (%s, %s, %s, %s, %s, NULL, %s, %s, %s, %s, %s, %s, %s)
            ''', (trip_initiator_id, 'Rider', driver_id, date, pick_up_time, from_location, to_location, no_of_passengers, guest_count, 0.0, distance, carbon_savings))
            trip_id = cursor.lastrowid  # Get the ID of the newly created trip
            mysql.connection.commit()

            # Insert TripRiders only for registered users
            cursor.execute('INSERT INTO tripriders (TripID, RiderID) VALUES (%s, %s)', (trip_id, riderID))
            mysql.connection.commit()

            flash('Trip created successfully', 'success')
            return redirect(url_for("rider_dashboard"))

        except Exception as e:
            mysql.connection.rollback()
            flash('Error creating trip: {}'.format(str(e)), 'danger')
            return render_template("RiderCreateTrip.html", preferences=preferences)

        finally:
            cursor.close()

    return render_template("RiderCreateTrip.html", preferences=preferences)




@app.route("/rider-savedaddress", methods = ["GET", "POST"])
def rider_savedaddress():
    return render_template("RiderSavedAddress.html")

@app.route("/rider-history")
def rider_history():
    userID = session.get('id')  # Get UserID from session
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Fetch the RiderID associated with the UserID from the session
        cursor.execute("SELECT RiderID FROM rider WHERE UserID = %s", (userID,))
        rider = cursor.fetchone()

        if not rider:
            flash("You are not logged in as a rider", "error")
            return redirect(url_for("login"))

        rider_id = rider['RiderID']  # Use the fetched RiderID

        # Fetch completed trips where the rider is the initiator
        query_initiated = '''
        SELECT trip.TripID, trip.From, trip.To, trip.PickUpTime, trip.DropOffTime, trip.Date, 
               trip.NoOfPassengers, trip.GuestCount, trip.Fare, 'Initiated' AS role,
               (SELECT COUNT(*) FROM tripriders WHERE tripriders.TripID = trip.TripID) AS current_riders,
               (SELECT COUNT(*) FROM feedbackrating WHERE feedbackrating.TripID = trip.TripID AND feedbackrating.FromUserID = %s) AS has_feedback
        FROM trip 
        WHERE trip.TripInitiatorID = %s AND trip.Status = 'Completed'
        ORDER BY trip.Date DESC, trip.PickUpTime DESC
        '''
        cursor.execute(query_initiated, (userID, userID))
        initiated_trips = cursor.fetchall()

        # Fetch completed trips where the rider joined the trip (not initiator)
        if initiated_trips:
            query_joined = '''
            SELECT trip.TripID, trip.From, trip.To, trip.PickUpTime, trip.DropOffTime, trip.Date, 
                   trip.NoOfPassengers, trip.GuestCount, trip.Fare, 'Joined' AS role,
                   (SELECT COUNT(*) FROM tripriders WHERE tripriders.TripID = trip.TripID) AS current_riders,
                   (SELECT COUNT(*) FROM feedbackrating WHERE feedbackrating.TripID = trip.TripID AND feedbackrating.FromUserID = %s) AS has_feedback
            FROM trip
            JOIN tripriders ON trip.TripID = triptiders.TripID
            WHERE tripriders.RiderID = %s AND trip.TripID NOT IN %s AND trip.Status = 'Completed'
            ORDER BY trip.Date DESC, trip.PickUpTime DESC
            '''
            cursor.execute(query_joined, (userID, rider_id, tuple([trip['TripID'] for trip in initiated_trips])))
        else:
            query_joined = '''
            SELECT trip.TripID, trip.From, trip.To, trip.PickUpTime, trip.DropOffTime, trip.Date, 
                   trip.NoOfPassengers, trip.GuestCount, trip.Fare, 'Joined' AS role,
                   (SELECT COUNT(*) FROM tripriders WHERE tripriders.TripID = trip.TripID) AS current_riders,
                   (SELECT COUNT(*) FROM feedbackrating WHERE feedbackrating.TripID = trip.TripID AND feedbackrating.FromUserID = %s) AS has_feedback
            FROM trip
            JOIN tripriders ON trip.TripID = tripriders.TripID
            WHERE tripriders.RiderID = %s AND trip.Status = 'Completed'
            ORDER BY trip.Date DESC, trip.PickUpTime DESC
            '''
            cursor.execute(query_joined, (userID, rider_id))
        
        joined_trips = cursor.fetchall()

        # Combine initiated and joined trips
        completed_trips = initiated_trips + joined_trips

        # Calculate total passengers (riders + guests)
        for trip in completed_trips:
            trip['total_passengers'] = trip['current_riders'] + trip['GuestCount']

    except Exception as e:
        flash(f"Error fetching history: {e}", "danger")
        completed_trips = []

    finally:
        cursor.close()

    return render_template("RiderHistory.html", trips=completed_trips)

@app.route('/submit-review/<int:trip_id>', methods=['POST']) #rider rate driver
def submit_review(trip_id):
    userID = session.get('id')  # Reviewer ID (FromUserID)
    rating = request.form.get('rating')
    review_text = request.form.get('review_text')
    print(trip_id, userID, rating)

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # First, retrieve the DriverID for the trip, then get the corresponding UserID
        cursor.execute('''
            SELECT DriverID 
            FROM trip 
            WHERE TripID = %s
        ''', (trip_id,))
        driver = cursor.fetchone()

        if driver:
            driver_id = driver['DriverID']

            # Now, get the UserID of the driver
            cursor.execute('''
                SELECT UserID 
                FROM driver 
                WHERE DriverID = %s
            ''', (driver_id,))
            driver_user = cursor.fetchone()

            if driver_user:
                to_user_id = driver_user['UserID']

                # Insert the review and rating into the feedbackrating and feedbackcomment tables
                cursor.execute('''
                    INSERT INTO feedbackrating (TripID, FromUserID, ToUserID, Rating)
                    VALUES (%s, %s, %s, %s)
                ''', (trip_id, userID, to_user_id, rating))
                feedback_id = cursor.lastrowid

                # Insert the review text into the feedbackcomment table
                cursor.execute('''
                    INSERT INTO feedbackcomment (FeedbackID, FeedbackComment)
                    VALUES (%s, %s)
                ''', (feedback_id, review_text))

                mysql.connection.commit()
                flash("Review submitted successfully!", "success")
            else:
                flash("Driver not found.", "danger")
        else:
            flash("Trip not found.", "danger")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error submitting review: {e}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('rider_history'))


@app.route('/trip-details/<int:trip_id>')
def trip_details(trip_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Fetch trip details by trip ID
        query = '''
        SELECT trip.TripID, trip.`From`, trip.`To`, trip.PickUpTime, trip.DropOffTime, trip.Date, 
               trip.NoOfPassengers, trip.GuestCount, trip.Fare, trip.Status, driver.FullName AS DriverName,
               (SELECT COUNT(*) FROM tripriders WHERE tripriders.TripID = trip.TripID) AS current_riders
        FROM trip 
        LEFT JOIN driver ON trip.DriverID = driver.DriverID
        WHERE trip.TripID = %s
        '''
        cursor.execute(query, (trip_id,))
        trip_details = cursor.fetchone()

        if trip_details:
            # Calculate total passengers (riders + guests)
            trip_details['total_passengers'] = trip_details['current_riders'] + trip_details['GuestCount']

            # Convert timedelta (PickUpTime and DropOffTime) to HH:mm format
            trip_details['PickUpTime'] = (datetime.min + trip_details['PickUpTime']).time().strftime('%H:%M') if trip_details['PickUpTime'] else 'N/A'
            trip_details['DropOffTime'] = (datetime.min + trip_details['DropOffTime']).time().strftime('%H:%M') if trip_details['DropOffTime'] else 'N/A'
            
            # Convert the date to DD/MM/YYYY format
            trip_details['Date'] = trip_details['Date'].strftime('%d/%m/%Y')  # Or use any format you prefer

            return jsonify(success=True, details=trip_details)
        else:
            return jsonify(success=False, message="Trip not found")

    except Exception as e:
        print(f"Error fetching trip details: {str(e)}")  # Consider using a logging library
        return jsonify(success=False, message="An error occurred while fetching trip details", error=str(e))

    finally:
        cursor.close()



@app.route("/current_tripRider", methods=["GET", "POST"])
def current_tripRider():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get the UserID from the session
    user_id = session.get('id')
    
    if not user_id:
        return "User not logged in", 401  # Unauthorized if no user ID in session

    # Fetch the RiderID for the current user
    rider_query = """
    SELECT RiderID FROM rider WHERE UserID = %s
    """
    cursor.execute(rider_query, (user_id,))
    rider = cursor.fetchone()

    if not rider:
        return "Rider not found", 404

    rider_id = rider['RiderID']

    # Fetch ongoing trip details for the Rider
    trip_query = """
    SELECT `From`, `To`, `PickUpTime`, `DropOffTime`, `NoOfPassengers`, `Fare`, `Status`
    FROM trip
    WHERE Status = 'Ongoing'
    """
    cursor.execute(trip_query)
    trip = cursor.fetchone()

    # Check if no trip exists
    if trip is None:
        # No ongoing trip, pass trip as None to the template
        return render_template('CurrentTripRider.html', trip=None)

    # If there is an ongoing trip, pass the trip details to the template
    return render_template('CurrentTripRider.html', trip=trip)


@app.route("/rider-reportissue", methods=["GET", "POST"])
def rider_reportissue():
    user_id = session.get('id')  # Get the logged-in user's ID
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the RiderID associated with the UserID
    cursor.execute("SELECT RiderID FROM rider WHERE UserID = %s", (user_id,))
    rider = cursor.fetchone()

    if not rider:
        flash('You are not logged in as a rider', 'danger')
        return redirect(url_for("login"))  # Redirect to login or another appropriate route

    rider_id = rider['RiderID']  # Use the fetched RiderID

    if request.method == "POST":
        # Get form data
        trip_id = request.form['trip_id']
        reason = request.form['subject']
        details = request.form['details']

        try:
            # Insert the issue report into the IssueReports table
            cursor.execute('''INSERT INTO IssueReports (ReporterType, ReporterID, TripID, Reason, Description)
                              VALUES (%s, %s, %s, %s, %s)''',
                           ('Rider', user_id, trip_id, reason, details))
            mysql.connection.commit()

            flash('Issue reported successfully', 'success')
            return redirect(url_for("rider_reportissue"))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error reporting issue: {str(e)}', 'danger')

        finally:
            cursor.close()

    # Fetch the rider's reports from the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT ir.ReportID, ir.TripID, ir.Reason, ir.Description, ir.ReportDate, ir.ReportStatus, ir.AdminResponse
        FROM issueReports ir
        WHERE ir.ReporterType = 'Rider' AND ir.ReporterID = %s
        ORDER BY ir.ReportDate DESC
    ''', (user_id,))
    reports = cursor.fetchall()

    # Fetch completed trips for the dropdown
    cursor.execute('''SELECT TripID, `From`, `To`, `Date`
                      FROM trip
                      WHERE (TripInitiatorID = %s OR trip.TripID IN 
                          (SELECT TripID FROM tripriders WHERE RiderID = %s)) 
                      AND Status = 'Completed'
                      ORDER BY Date DESC''', (user_id, rider_id))
    trips = cursor.fetchall()

    cursor.close()

    return render_template("RiderReportIssue.html", trips=trips, reports=reports)




@app.route("/rider-chat")
def rider_chat():
    return render_template("RiderChat.html")

@app.route("/rider-trip-chat/<int:trip_id>")
def rider_trip_chat(trip_id):
    if 'id' not in session:
        return redirect(url_for('login'))
    return render_template('RiderChat.html', trip_id=trip_id)



@app.route('/ridersend_message', methods=['POST'])
def ridersend_message():
    # Ensure the user is logged in
    if 'id' not in session:
        return redirect(url_for('login'))  

    data = request.json
    rider_id = session['id']  # User's ID from the session
    trip_id = data.get('trip_id')
    message = data.get('message')

    # Validate input
    if not trip_id or not message:
        return jsonify({"success": False, "error": "Trip ID or message is missing"}), 400

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Retrieve the driver's UserID associated with the trip
        cursor.execute("""
            SELECT driver.UserID AS ReceiverID 
            FROM trip 
            JOIN driver ON trip.DriverID = driver.DriverID 
            WHERE trip.TripID = %s
        """, (trip_id,))
        receiver = cursor.fetchone()

        if not receiver:
            return jsonify({"success": False, "error": "Driver not found"}), 404

        receiver_id = receiver['ReceiverID']  # Use the driver's UserID

        # Insert the message into the messages table
        query = """
        INSERT INTO messages (TripID, SenderID, ReceiverID, Message, Timestamp)
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (trip_id, rider_id, receiver_id, message))
        mysql.connection.commit()

        # Fetch sender details from the session
        sender_name = session.get('fullname', 'Unknown')
        sender_id = session.get('id')

        cursor.close()

        # Return a success response with relevant information
        return jsonify({
            "success": True,
            "sender_name": sender_name,
            "sender_id": sender_id,
            "message": message
        }), 200

    except MySQLdb.IntegrityError as e:
        # Handle MySQL integrity errors (e.g., foreign key violations)
        return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        # Handle any other unforeseen errors
        return jsonify({"success": False, "error": str(e)}), 500







@app.route('/get_messages/<int:trip_id>', methods=['GET'])
def get_messages(trip_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Define query to fetch messages
    query = """
    SELECT m.MessageID, m.TripID, m.SenderID, u.FullName AS SenderName, m.Message, m.Timestamp
    FROM messages m
    JOIN user u ON m.SenderID = u.UserID
    WHERE m.TripID = %s
    ORDER BY m.Timestamp ASC
    """

    start_time = time.time()
    timeout = 30  # 30 seconds timeout for long-polling

    # Long-polling loop: Keep checking for new messages within the timeout period
    while time.time() - start_time < timeout:
        cursor.execute(query, (trip_id,))
        messages = cursor.fetchall()

        if messages:
            cursor.close()
            return jsonify(messages)

        time.sleep(0.5)  # Sleep to avoid busy-waiting

    cursor.close()
    # No new messages found within timeout period, return empty list
    return jsonify([])



@app.route("/rider-feedback", methods=["GET", "POST"])
def rider_feedback():
    if request.method == "POST":
        # Get the logged-in user's ID from the session
        user_id = session.get('id')

        # Fetch user details from the 'user' table
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT FullName, AccountType, Picture FROM user WHERE UserID = %s", (user_id,))
        user_details = cursor.fetchone()

        if user_details:
            # Since 'user_details' is a tuple, access it using index positions
            full_name = user_details[0]  # Index 0 for 'FullName'
            account_type = user_details[1]  # Index 1 for 'AccountType'
            user_photo = user_details[2]  # Index 2 for 'Picture'

            # Retrieve data from the form
            feedback_subject = request.form.get('subject')
            other_subject = request.form.get('other_subject', None)  # Optional field
            feedback_text = request.form.get('feedback')
            rating = request.form.get('rating')

            # Insert the feedback into the 'testimonials' table
            try:
                cursor.execute('''
                    INSERT INTO testimonials (UserID, FullName, AccountType, UserPhoto, FeedbackSubject, OtherSubject, FeedbackText, FeedbackDate, Rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                ''', (user_id, full_name, account_type, user_photo, feedback_subject, other_subject, feedback_text, rating))
                mysql.connection.commit()
                flash('Feedback submitted successfully!', 'success')
            except Exception as e:
                mysql.connection.rollback()
                flash(f'An error occurred while submitting feedback: {str(e)}', 'danger')
            finally:
                cursor.close()

            return render_template("RiderFeedback.html")
        else:
            flash('User details not found. Please try again.', 'danger')
    return render_template("RiderFeedback.html")




@app.route('/driver-homepage', methods=['GET', 'POST'])
def driver_homepage():
    userID = session.get('id')
    show_modal = False

    # Get the Driver ID for the current user
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (userID,))
    driver = cursor.fetchone()

    if not driver:
        flash("Driver not found.", "danger")
        return redirect(url_for("login"))

    driverID = driver['DriverID']

    if request.method == 'POST':
        # Get form data with defaults
        passenger_gender = request.form.get("passengerGender", "Any")
        passenger_age = request.form.get("passengerAge", "Any")
        user_type = request.form.get("studentStaff", "Any")
        pets = request.form.get("pets", "Any")

        # Insert preferences into the database
        cursor.execute('''INSERT INTO driverpreferences
                        (driverId, passengerAge, passengerGender, userType, pets)
                        VALUES (%s, %s, %s, %s, %s)''',
                       (driverID, passenger_age, passenger_gender, user_type, pets))
        mysql.connection.commit()

        # Flash success message and redirect
        flash("Preferences saved successfully", "success")
        return redirect(url_for("driver_homepage"))

    # Fetch existing preferences if available
    cursor.execute("SELECT * FROM driverpreferences WHERE driverId = %s", (driverID,))
    preferences = cursor.fetchone()

    if preferences is None:
        show_modal = True

    # Fetch trip data by month for the driver
    cursor.execute('''SELECT MONTH(Date) AS month, COUNT(*) AS trip_count
                      FROM trip
                      WHERE DriverID = %s
                      GROUP BY MONTH(Date)
                      ORDER BY MONTH(Date)''', (driverID,))
    trips_by_month = cursor.fetchall()

    # Fetch all completed trips for the driver
    cursor.execute("SELECT * FROM trip WHERE DriverID = %s AND Status = 'Completed'", (driverID,))
    trips = cursor.fetchall()

    total_carbon_savings = 0.0

    # Calculate carbon savings for each trip
    for trip in trips:
        distance = trip['Distance'] if trip['Distance'] else 0.0
        occupants = trip['NoOfPassengers'] if trip['NoOfPassengers'] else 1

        if distance > 0 and occupants > 0:
            baseline_emission = 251 * distance  # 251 grams/km * distance
            actual_emission = baseline_emission / occupants
            emission_reduction = baseline_emission - actual_emission
            total_carbon_savings += emission_reduction

    if total_carbon_savings >= 1000:
        formatted_carbon_savings = f"{total_carbon_savings / 1000:.2f} kg"
    else:
        formatted_carbon_savings = f"{total_carbon_savings:.2f} g"

    trip_data = defaultdict(int)
    for row in trips_by_month:
        trip_data[row['month']] = row['trip_count']

    months = [7, 8, 9, 10, 11, 12]
    trip_counts = [trip_data[month] for month in months]

    cursor.execute('''SELECT COUNT(*) AS total_completed
                      FROM trip
                      WHERE DriverID = %s AND Status = 'Completed' ''', (driverID,))
    total_completed = cursor.fetchone()['total_completed']

    current_month = datetime.now().month
    cursor.execute('''SELECT COUNT(*) AS completed_current_month
                      FROM trip
                      WHERE DriverID = %s AND Status = 'Completed'
                      AND MONTH(Date) = %s''', (driverID, current_month))
    completed_current_month = cursor.fetchone()['completed_current_month']

    cursor.execute('''SELECT COUNT(*) AS upcoming_trips
                      FROM trip
                      WHERE DriverID = %s AND Status = 'Planned' ''', (driverID,))
    upcoming_trips = cursor.fetchone()['upcoming_trips']

    now = datetime.now()
    cursor.close()

    return render_template(
        'DriverHomepage.html',
        now=now,
        show_modal=show_modal,
        preferences=preferences,
        total_completed=total_completed,
        completed_current_month=completed_current_month,
        upcoming_trips=upcoming_trips,
        carbon_savings=formatted_carbon_savings,
        trip_counts=trip_counts
    )



@app.route("/driver-dashboard")
def driver_dashboard():
    userID = session.get('id')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the DriverID associated with the UserID from the session
    cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (userID,))
    driver = cursor.fetchone()

    if not driver:
        flash("You are not logged in as a driver", "error")
        return redirect(url_for("login"))

    driver_id = driver['DriverID']
    
    # Query trips for the logged-in driver, but exclude 'Completed' trips
    cursor.execute('''
        SELECT trip.*, 
               IFNULL(rider.FullName, 'No Rider Assigned') AS RiderName,
               trip.GuestCount,
               (trip.TripInitiatorID = %s) AS is_initiator  -- Check if the driver is the trip initiator
        FROM trip 
        LEFT JOIN rider ON trip.TripInitiatorID = rider.RiderID 
        WHERE trip.DriverID = %s AND trip.Status IN ('Planned', 'Ongoing')
        ORDER BY trip.Date DESC, trip.PickUpTime DESC
    ''', (userID, driver_id))
    
    trips = cursor.fetchall()

    # Fetch the passenger names for all trips (including guests)
    for trip in trips:
        # Fetch all riders for this trip from the TripRiders table
        cursor.execute('''
            SELECT rider.FullName
            FROM rider
            JOIN tripriders ON rider.RiderID = tripriders.RiderID
            WHERE tripriders.TripID = %s
        ''', (trip['TripID'],))
        passengers = cursor.fetchall()

        # Combine passenger names into a single string
        passenger_names = [passenger['FullName'] for passenger in passengers]

        if passenger_names:
            trip['PassengerNames'] = ', '.join(passenger_names)
        else:
            trip['PassengerNames'] = 'No passengers'

        # If there are guests, add the guest count to the display
        if trip['GuestCount'] > 0:
            trip['PassengerNames'] += f" + {trip['GuestCount']} Guest(s)"

        # Format the date to dd/mm/yyyy
        trip['Date'] = datetime.strptime(str(trip['Date']), '%Y-%m-%d').strftime('%d/%m/%Y')

        # Convert PickUpTime and DropOffTime (timedelta) to HH:mm format
        pickup_time = (datetime.min + trip['PickUpTime']).time()  # Convert timedelta to time
        trip['PickUpTime'] = pickup_time.strftime('%H:%M')  # Format to HH:mm

        if trip['DropOffTime']:
            dropoff_time = (datetime.min + trip['DropOffTime']).time()  # Convert timedelta to time
            trip['DropOffTime'] = dropoff_time.strftime('%H:%M')  # Format to HH:mm

    cursor.close()

    return render_template("DriverDashboard.html", trips=trips)



@app.route("/start_trip/<int:trip_id>", methods=["POST"])
def start_trip(trip_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get the driver ID from the session
    driver_id = session.get('id')

    # Check if the driver already has an ongoing trip
    cursor.execute("""
        SELECT TripID FROM trip 
        WHERE DriverID = (SELECT DriverID FROM Driver WHERE UserID = %s) 
        AND Status = 'Ongoing'
    """, (driver_id,))
    ongoing_trip = cursor.fetchone()

    if ongoing_trip:
        # If there is an ongoing trip, prevent starting a new trip
        cursor.close()
        return jsonify({'success': False, 'message': 'You already have an ongoing trip. Complete it before starting a new one.'})

    try:
        # If no ongoing trip, update the selected trip's status to 'Ongoing'
        cursor.execute('''
            UPDATE trip 
            SET Status = 'Ongoing'
            WHERE TripID = %s
        ''', (trip_id,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True, 'message': 'Trip started successfully'})
    except Exception as e:
        mysql.connection.rollback()
        cursor.close()
        return jsonify({'success': False, 'message': str(e)})



@app.route("/driver_update_trip", methods=["POST"])
def driver_update_trip():
    if request.method == "POST":
        # Get form data from the request
        trip_id = request.form.get("trip_id")
        from_location = request.form.get("from")
        to_location = request.form.get("to")
        pick_up_time = request.form.get("pick_up_time")
        date = request.form.get("date")

        cursor = mysql.connection.cursor()

        try:
            # Update the trip in the database
            cursor.execute('''
                UPDATE trip 
                SET `From` = %s, `To` = %s, PickUpTime = %s, Date = %s 
                WHERE TripID = %s
            ''', (from_location, to_location, pick_up_time, date, trip_id))
            
            mysql.connection.commit()
            flash("Trip updated successfully", "success")
        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of error
            flash(f"Error updating trip: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for("driver_dashboard"))




@app.route("/driver-triprequest")
def driver_triprequest():
    # Get the current driver ID from the session or request (assuming it's stored in session)
    user_id = session.get('id')  # Make sure to set this in your login logic
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (user_id,))
    driver = cursor.fetchone()

    if not driver:
        flash("You are not logged in as a driver", "error")
        return redirect(url_for("login"))

    # Query to fetch all trips that do not have an assigned driver and are Planned
    cursor = mysql.connection.cursor()
    query = """
        SELECT 
            TripID AS trip_id,
            `From` AS pickup_location,
            `To` AS dropoff_location,
            PickUpTime AS trip_time,
            Date AS trip_date,
            NoOfPassengers AS passenger_count,
            Fare AS fare
        FROM 
            trip
        WHERE 
            DriverID IS NULL AND Status = 'Planned'
    """
    cursor.execute(query)
    trips = cursor.fetchall()
    cursor.close()

    # Format the trips data into a list of dictionaries
    trips_data = [
        {
            'trip_id': trip[0],
            'pickup_location': trip[1],
            'dropoff_location': trip[2],
            'trip_time': trip[3],
            'trip_date': trip[4],
            'passenger_count': trip[5],
            'fare': trip[6],
        }
        for trip in trips
    ]

    # Render the template with the trips data
    return render_template("DriverTripRequests.html", trips=trips_data)

@app.route("/assign_driver/<int:trip_id>", methods=["POST"])
def assign_driver(trip_id):
    # Get the current driver ID from the session
    user_id = session.get('id')
    
    if not user_id:
        flash("You are not logged in as a driver", "danger")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the driver ID based on the user ID
    cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (user_id,))
    driver = cursor.fetchone()

    if not driver:
        flash("Driver not found", "danger")
        return redirect(url_for("driver_dashboard"))

    driver_id = driver['DriverID']

    try:
        # Update the Trip table to assign the driver and set the status to 'Ongoing'
        cursor.execute('''
            UPDATE trip
            SET DriverID = %s
            WHERE TripID = %s
        ''', (driver_id, trip_id))

        mysql.connection.commit()

        flash("You have successfully picked up the trip.", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error assigning driver: {str(e)}", "danger")

    finally:
        cursor.close()

    return redirect(url_for("driver_triprequest"))


@app.route("/driver-trip-chat/<int:trip_id>")
def driver_trip_chat(trip_id):
    if "driver_id" not in session:
        flash("You must be logged in as a driver to access this chat", "danger")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT DriverID FROM trip WHERE TripID = %s", (trip_id,))
    trip = cursor.fetchone()

    if not trip or trip["DriverID"] != session["driver_id"]:
        flash("You are not authorized to access this chat", "danger")
        return redirect(url_for("driver_dashboard"))

    return render_template("DriverChat.html", trip_id=trip_id)



@app.route('/driversend_message', methods=['POST'])
def driversend_message():
    # Ensure the user is logged in
    if 'id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    # Extract data from the request and session
    data = request.json
    driver_id = session['id']
    driver_name = session.get('fullname', 'Unknown')  # Driver's name from session
    trip_id = data.get('trip_id')
    message = data.get('message')

    # Validate input
    if not trip_id or not message:
        return jsonify({"success": False, "error": "Trip ID or message is missing"}), 400

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Retrieve the Rider's UserID (TripInitiatorID) from the Trip table
        query = """
            SELECT trip.TripInitiatorID AS ReceiverID 
            FROM trip 
            WHERE trip.TripID = %s
        """
        cursor.execute(query, (trip_id,))
        receiver = cursor.fetchone()

        # Validate if the receiver (rider) exists
        if not receiver:
            return jsonify({"success": False, "error": "Rider not found"}), 404

        receiver_id = receiver['ReceiverID']

        # Insert the message into the messages table
        insert_query = """
            INSERT INTO messages (TripID, SenderID, ReceiverID, Message, Timestamp)
            VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(insert_query, (trip_id, driver_id, receiver_id, message))
        mysql.connection.commit()
        cursor.close()

        # Respond with success, including the sender's name
        return jsonify({"success": True, "sender_name": driver_name}), 200

    except MySQLdb.Error as e:
        # Handle any MySQL database errors
        return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        # Handle any other unforeseen exceptions
        return jsonify({"success": False, "error": str(e)}), 500




    
@app.route('/get_driver_messages/<int:trip_id>', methods=['GET'])
def get_driver_messages(trip_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Query to retrieve messages for the driver
        query = """
            SELECT m.MessageID, m.Message, m.SenderID, u.FullName AS SenderName, m.Timestamp
            FROM messages m
            JOIN user u ON m.SenderID = u.UserID
            WHERE m.TripID = %s
            ORDER BY m.Timestamp ASC
        """
        cursor.execute(query, (trip_id,))
        messages = cursor.fetchall()
        cursor.close()

        # Return messages with a 200 status code
        return jsonify(messages), 200

    except Exception as e:
        # Handle any unforeseen errors and print them to the console
        print("Error fetching driver messages:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/driver-profile", methods=["GET", "POST"])
def driver_profile():
    user_id = session.get("id")  # Get the driver's UserID from the session
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the DriverID associated with the UserID from the session
    cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (user_id,))
    driver = cursor.fetchone()

    if not driver:
        flash('Driver not found!', 'danger')
        return redirect(url_for('homepage'))  # or another route as needed

    driver_id = driver["DriverID"]

    # Fetch the current user data
    cursor.execute("""
        SELECT u.FullName, u.Phone, u.Email, u.Picture 
        FROM user u 
        WHERE u.UserID = %s
    """, (user_id,))
    user = cursor.fetchone()

    # Calculate the average rating for the driver
    cursor.execute("""
        SELECT AVG(Rating) as avg_rating 
        FROM feedbackrating 
        WHERE ToUserID = %s
    """, (user_id,))
    avg_rating_result = cursor.fetchone()
    avg_rating = round(avg_rating_result['avg_rating'], 1) if avg_rating_result['avg_rating'] else 0

    # Fetch the most recent 5 reviews/ratings
    cursor.execute("""
        SELECT fr.Rating, fc.FeedbackComment, fc.FeedbackDate 
        FROM feedbackrating fr
        LEFT JOIN feedbackcomment fc ON fr.FeedbackID = fc.FeedbackID
        WHERE fr.ToUserID = %s
        ORDER BY fc.FeedbackDate DESC 
        LIMIT 5
    """, (user_id,))
    reviews = cursor.fetchall()

    if request.method == "POST":
        phone = request.form.get("phone")
        picture = request.files.get("picture")

        try:
            if picture:
                # Save the new profile picture
                picture_filename = secure_filename(picture.filename)
                picture_path = os.path.join(app.config["UPLOAD_FOLDER"], picture_filename)
                picture.save(picture_path)

                # Update both phone and picture in the database
                cursor.execute("UPDATE user SET Phone = %s, Picture = %s WHERE UserID = %s", (phone, picture_filename, user_id))
            else:
                # Just update the phone number if no picture is uploaded
                cursor.execute("UPDATE user SET Phone = %s WHERE UserID = %s", (phone, user_id))

            mysql.connection.commit()
            flash("Profile updated successfully!", "success")

        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating profile: {e}", "danger")

        finally:
            cursor.close()

        return redirect(url_for("driver_profile"))

    return render_template("DriverProfile.html", user=user, avg_rating=avg_rating, reviews=reviews)

@app.route("/driver-savedaddresses")
def driver_savedaddresses():
    return render_template("DriverSavedAddresses.html")

@app.route("/driver-history")
def driver_history():
    userID = session.get('id')  # Get the logged-in user ID
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Fetch the DriverID associated with the UserID
        cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (userID,))
        driver = cursor.fetchone()

        if not driver:
            flash("You are not logged in as a driver", "error")
            return redirect(url_for("login"))

        driver_id = driver['DriverID']  # Use the fetched DriverID

        # Fetch all completed trips for this driver
        query = '''
        SELECT trip.TripID, trip.From, trip.To, trip.PickUpTime, trip.DropOffTime, trip.Date, 
               trip.NoOfPassengers, trip.GuestCount, trip.Fare, 
               (SELECT COUNT(*) FROM tripriders WHERE tripriders.TripID = trip.TripID) AS current_riders
        FROM trip 
        WHERE trip.DriverID = %s AND trip.Status = 'Completed'
        ORDER BY trip.Date DESC, trip.PickUpTime DESC
        '''
        cursor.execute(query, (driver_id,))
        completed_trips = cursor.fetchall()

        # Calculate total passengers for each trip
        for trip in completed_trips:
            trip['total_passengers'] = trip['current_riders'] + trip['GuestCount']

            # Fetch the riders for each trip and check if the driver has rated each one
            cursor.execute('''
                SELECT r.RiderID, u.FullName,
                    (SELECT COUNT(*) FROM feedbackrating 
                     WHERE feedbackrating.TripID = %s 
                     AND feedbackrating.FromUserID = %s 
                     AND feedbackrating.ToUserID = u.UserID) AS has_rating
                FROM tripriders tr
                JOIN rider r ON tr.RiderID = r.RiderID
                JOIN user u ON r.UserID = u.UserID
                WHERE tr.TripID = %s
            ''', (trip['TripID'], userID, trip['TripID']))
            riders = cursor.fetchall()

            # Attach the riders' details and their rating status to the trip
            trip['riders'] = riders

    except Exception as e:
        flash(f"Error fetching history: {e}", "danger")
        completed_trips = []

    finally:
        cursor.close()

    return render_template("DriverHistory.html", trips=completed_trips)


@app.route('/submit-rating/<int:trip_id>', methods=['POST'])
def submit_rating(trip_id):
    driver_id = session.get('id')  # Driver's User ID
    rating = request.form.get('rating')
    rider_id = request.form.get('rider_id')  # Rider to be rated

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Ensure the rider_id is valid for this trip
        cursor.execute('''
            SELECT RiderID FROM tripriders WHERE TripID = %s AND RiderID = %s
        ''', (trip_id, rider_id))
        rider = cursor.fetchone()

        if rider:
            # Now fetch the corresponding UserID for this RiderID
            cursor.execute('''
                SELECT UserID FROM rider WHERE RiderID = %s
            ''', (rider_id,))
            rider_user = cursor.fetchone()

            if rider_user:
                # Insert the rating for the rider by the driver using the UserID
                cursor.execute('''
                    INSERT INTO feedbackrating (TripID, FromUserID, ToUserID, Rating)
                    VALUES (%s, %s, %s, %s)
                ''', (trip_id, driver_id, rider_user['UserID'], rating))
                mysql.connection.commit()
                flash("Rating submitted successfully!", "success")
            else:
                flash("Rider user not found.", "danger")
        else:
            flash("Invalid rider for the selected trip.", "danger")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error submitting rating: {str(e)}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('driver_history'))


@app.route('/trip-riders/<int:trip_id>', methods=['GET'])
def get_trip_riders(trip_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch all riders for the trip
        cursor.execute('''
            SELECT rider.RiderID, user.FullName 
            FROM tripriders 
            JOIN rider ON tripriders.RiderID = rider.RiderID 
            JOIN user ON rider.UserID = user.UserID 
            WHERE tripriders.TripID = %s
        ''', (trip_id,))
        riders = cursor.fetchall()

        return jsonify(success=True, riders=riders)

    except Exception as e:
        return jsonify(success=False, message=str(e))

    finally:
        cursor.close()

@app.route("/driver-reportissue", methods=["GET", "POST"])
def driver_reportissue():
    user_id = session.get('id')  # Get the logged-in user's ID
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the DriverID associated with the UserID
    cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (user_id,))
    driver = cursor.fetchone()

    if not driver:
        flash('You are not logged in as a driver', 'danger')
        return redirect(url_for("login"))  # Redirect to login or another appropriate route

    driver_id = driver['DriverID']  # Use the fetched DriverID

    if request.method == "POST":
        # Get form data
        trip_id = request.form['trip_id']
        reason = request.form['subject']
        details = request.form['details']

        try:
            # Insert the issue report into the IssueReports table
            cursor.execute('''INSERT INTO IssueReports (ReporterType, ReporterID, TripID, Reason, Description)
                              VALUES (%s, %s, %s, %s, %s)''',
                           ('Driver', user_id, trip_id, reason, details))
            mysql.connection.commit()

            flash('Issue reported successfully', 'success')
            return redirect(url_for("driver_reportissue"))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error reporting issue: {str(e)}', 'danger')

        finally:
            cursor.close()

    # Fetch the driver's reports from the database
    cursor.execute('''
        SELECT ir.ReportID, ir.TripID, ir.Reason, ir.Description, ir.ReportDate, ir.ReportStatus, ir.AdminResponse
        FROM IssueReports ir
        WHERE ir.ReporterType = 'Driver' AND ir.ReporterID = %s
        ORDER BY ir.ReportDate DESC
    ''', (user_id,))
    reports = cursor.fetchall()

    # Fetch completed trips for the dropdown
    cursor.execute('''SELECT TripID, `From`, `To`, `Date`
                      FROM trip
                      WHERE DriverID = %s AND Status = 'Completed'
                      ORDER BY Date DESC''', (driver_id,))
    trips = cursor.fetchall()

    return render_template("DriverReportIssue.html", trips=trips, reports=reports)



@app.route("/driver-chat")
def driver_chat():
    return render_template("DriverChat.html")

# Helper function to calculate carbon savings
def calculate_carbon_savings(distance):
    """Assume 0.12 kg CO2 savings per km for each trip."""
    return round(distance * 0.12, 2)

@app.route("/driver-createTrip", methods=["GET", "POST"])
def driver_createtrip():
    userID = session.get('id')  # Get UserID from session
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the DriverID associated with the UserID from the session
    cursor.execute("SELECT DriverID FROM Driver WHERE UserID = %s", (userID,))
    driver = cursor.fetchone()

    if not driver:
        flash('Driver not found!', 'danger')
        return redirect(url_for('login'))

    driverID = driver['DriverID']  # Use the fetched DriverID

    # Load user preferences if they exist
    cursor.execute("SELECT * FROM DriverPreferences WHERE DriverID = %s", (driverID,))
    preferences = cursor.fetchone()

    if request.method == "POST":
        try:
            trip_initiator_id = userID  # Set trip initiator to the current driver userID
            date = request.form['date']
            pick_up_time = request.form['tripPickUpTime']
            from_location = request.form['from']
            to_location = request.form['to']
            no_of_passengers = int(request.form['tripPassengers'])  # Total number of passengers
            
            # Handle the distance field
            distance = request.form.get('distance', '0.0')  # Default to '0.0' if empty
            try:
                distance = float(distance)  # Convert to float safely
            except ValueError:
                distance = 0.0  # Default to 0.0 if conversion fails

            # Calculate carbon savings for this trip
            carbon_savings = calculate_carbon_savings(distance)

            # Preferences from the form
            passengers_gender = request.form['passengersGender']
            passengers_age = request.form['passengersAge']
            pets = request.form['pets']
            user_type = request.form['studentStaff']

            # Update or insert driver preferences
            if preferences:
                if (preferences['PassengerGender'] != passengers_gender or
                    preferences['PassengerAge'] != passengers_age or
                    preferences['Pets'] != pets or
                    preferences['UserType'] != user_type):
                    cursor.execute('''
                        UPDATE DriverPreferences 
                        SET PassengerGender = %s, PassengerAge = %s, Pets = %s, UserType = %s 
                        WHERE DriverID = %s
                    ''', (passengers_gender, passengers_age, pets, user_type, driverID))
                    mysql.connection.commit()
                    flash("Preferences updated.", "success")
            else:
                cursor.execute('''
                    INSERT INTO DriverPreferences (DriverID, PassengerGender, PassengerAge, Pets, UserType)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (driverID, passengers_gender, passengers_age, pets, user_type))
                mysql.connection.commit()
                flash("Preferences saved.", "success")

            # Insert the new trip into the database
            cursor.execute('''
                INSERT INTO trip (TripInitiatorID, TripInitiatorType, DriverID, Date, PickUpTime, `From`, `To`, 
                                  NoOfPassengers, Fare, Distance, CarbonSavings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (trip_initiator_id, 'Driver', driverID, date, pick_up_time, 
                  from_location, to_location, no_of_passengers, 0.0, distance, carbon_savings))
            trip_id = cursor.lastrowid  # Get the ID of the newly created trip
            mysql.connection.commit()

            flash('Trip created successfully', 'success')
            return redirect(url_for("driver_dashboard"))

        except Exception as e:
            mysql.connection.rollback()
            flash('Error creating trip: {}'.format(str(e)), 'danger')
            return render_template("DriverCreateTrip.html", preferences=preferences)

        finally:
            cursor.close()

    return render_template("DriverCreateTrip.html", preferences=preferences)


@app.route('/current_tripDriver', methods=['GET', 'POST'])
def current_tripDriver():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get the UserID from the session
    user_id = session.get('id')
    
    if not user_id:
        return "User not logged in", 401  # Unauthorized if no user ID in session

    # Fetch the user account type (Rider or Driver)
    user_query = """
    SELECT AccountType FROM User WHERE UserID = %s
    """
    cursor.execute(user_query, (user_id,))
    user = cursor.fetchone()

    if not user:
        return "User not found", 404

    account_type = user['AccountType']

    if account_type == 'Driver':
        if request.method == 'POST':
            # Handle the complete trip logic
            trip_id = request.form.get('trip_id')
            # Update the trip status to 'Completed' and DropOffTime to current time
            current_time = datetime.now().time()  # Get current time
            
            update_trip_query = """
            UPDATE trip 
            SET Status = 'Completed', DropOffTime = %s 
            WHERE TripID = %s
            """
            cursor.execute(update_trip_query, (current_time, trip_id))
            mysql.connection.commit() 
            return redirect(url_for('driver_dashboard'))  # Redirect to the dashboard

        # Fetch ongoing trip details for the driver
        trip_query = """
        SELECT TripID, `From`, `To`, `PickUpTime`, `DropOffTime`, `NoOfPassengers`, `Fare`, `Status`
        FROM trip
        WHERE DriverID = (SELECT DriverID FROM Driver WHERE UserID = %s) AND Status = 'Ongoing'
        """
        cursor.execute(trip_query, (user_id,))
        trip = cursor.fetchone()  # Fetch one ongoing trip

        return render_template('CurrentTripDriver.html', trip=trip)  # Pass trip details to the template
    else:
        return "Access denied for riders", 403  # Only drivers can access this route

@app.route("/rider-availabletrips", methods=["GET", "POST"])
def rider_availabletrips():
    user_id = session.get('id')  # Get the logged-in user ID from the session

    if not user_id:
        flash('You are not logged in as a rider', 'danger')
        return redirect(url_for('login'))  # Redirect to login

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the RiderID associated with the UserID
    cursor.execute("SELECT RiderID FROM rider WHERE UserID = %s", (user_id,))
    rider = cursor.fetchone()

    if not rider:
        flash('Rider not found!', 'danger')
        return redirect(url_for('login'))

    rider_id = rider['RiderID']  # Use the fetched RiderID

    if request.method == "POST":
        trip_id = request.form.get('trip_id')

        try:
            # Directly insert the rider into the TripRiders table
            cursor.execute('''
                INSERT INTO tripriders (TripID, RiderID)
                VALUES (%s, %s)
            ''', (trip_id, rider_id))
            mysql.connection.commit()

            flash('You have successfully joined the trip!', 'success')

        except Exception as e:
            # Handle potential insertion errors (e.g., duplicate entry)
            mysql.connection.rollback()
            flash(f'Error joining the trip: {str(e)}', 'danger')

    # Query to get available trips where the current passengers are less than capacity,
    # the current rider hasn't already joined, and the trip was initiated by a driver.
    cursor.execute('''
        SELECT t.TripID, t.From, t.To, t.PickUpTime, t.Date, t.NoOfPassengers, 
            (SELECT COUNT(*) FROM tripriders WHERE TripID = t.TripID) AS current_passengers
        FROM trip t 
        WHERE t.TripInitiatorType = "Driver"
        AND t.Status = 'Planned'
        AND t.TripID NOT IN (SELECT TripID FROM tripriders WHERE RiderID = %s)
        AND (SELECT COUNT(*) FROM tripriders WHERE TripID = t.TripID) < t.NoOfPassengers
    ''', (rider_id,))

    available_trips = cursor.fetchall()
    cursor.close()

    return render_template("rideravailabletrips.html", trips=available_trips)


@app.route('/driver_feedback', methods=['GET', 'POST'])
def driver_feedback():
    if not session.get('loggedin'):
        flash("Please login to submit feedback", 'danger')
        return redirect(url_for('login'))

    user_id = session['id']  # Correct session key for user id
    full_name = session.get('fullname', 'Anonymous')  # Get the full name from session, default to 'Anonymous' if not available
    account_type = session['role']  # Get the role from session
    
    success_message = None
    
    if request.method == 'POST':
        try:
            feedback_subject = request.form['subject']
            feedback_text = request.form['feedback']
            rating = request.form['rating']
            other_subject = request.form.get('other_subject', None)
            
            # Insert feedback into the database
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO testimonials (UserID, FullName, AccountType, FeedbackSubject, OtherSubject, FeedbackText, FeedbackDate, Rating) "
                "VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)",
                (user_id, full_name, account_type, feedback_subject, other_subject, feedback_text, rating)
            )
            mysql.connection.commit()
            cur.close()
            
            # Set a success message to be shown
            success_message = "Feedback successfully submitted!"
        
        except Exception as e:
            print(f"Error inserting feedback: {e}")
            flash("There was an error submitting your feedback. Please try again.", "danger")
    
    return render_template('DriverFeedback.html', success_message=success_message)









if __name__ == "__main__":
    app.run(debug = True)
