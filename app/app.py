from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, get_flashed_messages, \
    Response
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
from datetime import timedelta
from functools import wraps
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Load the environment variables from the .env file
load_dotenv()

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///queue.sqlite3'  # For local testing
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class Image(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)


class Customer(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    image_id = db.Column(db.Integer, nullable=True)

    def __init__(self, name, phone):
        self.name = name
        self.phone = phone

    def __repr__(self):
        return '<Customer %r>' % self.name


@app.route('/')
def index():
    # Add admin access to the welcome page by adding a link
    return render_template('customer_form.html')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/validation', methods=['GET', 'POST'])
def validation():
    # Fix flash message
    # Verify if the phone number already exists in the database
    name = request.form['name']
    phone_area = request.form['phone_area']
    phone_prefix = request.form['phone_prefix']
    phone_line = request.form['phone_line']
    phone_number = f"+1{phone_area}{phone_prefix}{phone_line}"
    customer = Customer.query.filter_by(phone=phone_number).first()
    # If phone number exists, redirect to the dashboard
    if customer is not None:
        flash('You are already in the queue!', 'success')
        return redirect(url_for('welcome'))
    # If not, Send message to the phone number using twillio and redirect to the welcome page
    else:
        # Enter customer info to the db
        new_customer = Customer(name=name, phone=phone_number)
        db.session.add(new_customer)
        db.session.commit()
        # Calculate the estimated wait time based on number of customers in the queue, assuming average wait time is 15 minutes
        wait_time = 15 * Customer.query.count()
        message_body = f"Eid Mubarak! Thank you {name} for joining the queue. Your estimated wait time is {wait_time} minutes."
        client = Client(account_sid, auth_token)
        try:
            print("Sending message...")
            message = client.messages.create(
                body=message_body,
                from_=twilio_phone_number,
                to=phone_number
            )
            # Calculate the estimated wait time based on number of customers in the queue, assuming average wait time is 15 minutes
            wait_time = 15 * Customer.query.count()
            flash(f'Thank you {name} for joining the queue. Your estimated wait time is {wait_time} minutes.',
                  'success')
            return redirect(url_for('welcome'))
        except Exception as e:
            # Handle the error (e.g., log the error or show an error message to the user)
            return f"Error: SMS could not be sent. Please provide a valid phone number {e}"


@app.route('/send_sms_to_customers', methods=['POST'])
def send_sms_to_customers():
    customer_ids = request.form.getlist('customer_ids')
    success_count = 0
    error_count = 0

    for customer_id in customer_ids:
        customer = Customer.query.get(customer_id)
        if customer:
            try:
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                    body="It's your turn! Please come to the desk :)",
                    from_=twilio_phone_number,
                    to=customer.phone
                )
                success_count += 1
            except Exception as e:
                print(f"Error: SMS could not be sent to {customer.phone}. {e}")
                error_count += 1

    flash(f'Messages sent to {success_count} customers. {error_count} failed.',
          'success' if success_count > 0 else 'danger')
    return redirect(url_for('customers'))


@app.route('/welcome')
def welcome():
    images = Image.query.all()
    print(images)
    return render_template('welcome.html', images=images)


# Add the @admin_required decorator to restrict access to the customers page when not logged in as an admin
@app.route('/customers', methods=['GET', 'POST'])
@admin_required
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)


@app.route('/image/<int:image_id>')
def serve_image(image_id):
    image = Image.query.get_or_404(image_id)
    return Response(image.data, content_type=image.mimetype)


@app.route('/remove_image/<int:image_id>', methods=['POST'])
@admin_required
def remove_image(image_id):
    print(image_id)
    image_id = request.json['image_id']
    image = Image.query.get(image_id)
    if image:
        db.session.delete(image)
        db.session.commit()
        flash('Image removed successfully', 'success')
    else:
        flash('Image not found', 'danger')
    return redirect(url_for('welcome'))


@app.route('/remove_customers', methods=['POST'])
def remove_customers():
    customer_ids = request.form.getlist('customer_ids')
    for customer_id in customer_ids:
        customer = Customer.query.get(customer_id)
        if customer:
            db.session.delete(customer)
            db.session.commit()
    flash('Selected customers removed from the queue', 'success')
    return redirect(url_for('customers'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_image', methods=['GET', 'POST'])
@admin_required
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image file found', 'danger')
            return redirect(request.url)

        image_file = request.files['image']
        if image_file.filename == '':
            flash('No image file selected', 'danger')
            return redirect(request.url)

        if image_file and allowed_file(image_file.filename):
            image_title = request.form['title']
            image_mimetype = image_file.mimetype

            new_image = Image(title=image_title, data=image_file.read(), mimetype=image_mimetype)
            db.session.add(new_image)
            db.session.commit()
            flash('Image uploaded successfully', 'success')
            return redirect(url_for('welcome'))
        else:
            flash('Invalid file type', 'danger')

    return render_template('welcome.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        passcode = request.form['passcode']
        print(passcode)
        if passcode == 'mehndi123':
            # Store the admin_logged_in flag in the session
            session['admin_logged_in'] = True
            # Set the session as permanent
            session.permanent = True
            return redirect(url_for('customers'))
        else:
            flash('Incorrect passcode! Hint: Ask Atif', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/get_position')
def get_position():
    customer_id = session.get('customer_id')

    if not customer_id:
        return jsonify(position=None)

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify(position=None)

    position = Customer.query.filter(Customer.id < customer.id).count()
    return jsonify(position=position)


@app.route('/dashboard')
def dashboard():
    # Verify if the user is logged in and has admin privileges
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the queue data from the database and render the dashboard
    queue_data = db.session.query(Customer).all()
    return render_template('dashboard.html', queue=queue_data)


@app.route('/select_image', methods=['POST'])
def select_image():
    image_id = request.json['image_id']
    customer_id = session.get('customer_id')

    if not customer_id:
        return jsonify(success=False)

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify(success=False)

    customer.image_id = image_id
    db.session.commit()

    return jsonify(success=True)


@app.route('/get_queue')
def get_queue():
    customers = Customer.query.all()
    queue_data = [
        {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'image_id': customer.image_id,
        }
        for customer in customers
    ]
    return jsonify(queue_data)


@app.route('/join_queue', methods=['POST'])
def join_queue():
    name = request.form['name']
    phone = request.form['phone']

    new_customer = Customer(name=name, phone=phone)
    db.session.add(new_customer)
    db.session.commit()

    # Send SMS using Twilio
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="Thank you for joining the queue. Your estimated wait time is X minutes.",
        from_=twilio_phone_number,
        to=phone
    )

    return redirect(url_for('index'))


@app.route('/notify_customer', methods=['POST'])
def notify_customer():
    customer_id = request.form['customer_id']
    customer = Customer.query.get(customer_id)
    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('dashboard'))

    # Send SMS using Twilio
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="It's your turn! Please proceed with the service or purchase.",
        from_=twilio_phone_number,
        to=customer.phone
    )

    flash('Notification sent to the customer', 'success')
    return redirect(url_for('dashboard'))


@app.route('/send_message', methods=['POST'])
def send_message():
    customer_id = request.form['customer_id']
    message_text = request.form['message']

    customer = Customer.query.get(customer_id)

    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('dashboard'))

    # Send SMS using Twilio
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=message_text,
        from_=twilio_phone_number,
        to=customer.phone
    )

    flash('Message sent to the customer', 'success')
    return redirect(url_for('dashboard'))


def create_database():
    try:
        connection = mysql.connector.connect(
            host='database-1.cxxoq4akoogy.ca-central-1.rds.amazonaws.com',
            user='admin',
            password='atif_rds'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS `database-1` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            connection.commit()
            print("Database created successfully")

    except Error as e:
        print("Error while connecting to MySQL", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    create_database()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
