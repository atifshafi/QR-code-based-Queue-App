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
from PIL import Image
from PIL import ImageOps
import io
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError

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


class Image_DB(db.Model):
    # __tablename__ = 'image'
    _id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)


class Customer(db.Model):
    __tablename__ = 'customer'
    _id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    admin = db.relationship('Admin', backref=db.backref('customers', lazy=True))
    image_id = db.Column(db.Integer, nullable=True)

    def __init__(self, name, phone, admin_id):
        self.name = name
        self.phone = phone
        self.admin_id = admin_id

    def __repr__(self):
        return '<Customer %r>' % self.name


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)


@app.route('/')
def index():
    admins = Admin.query.all()
    # Add admin access to the welcome page by adding a link
    return render_template('customer_form.html', admins=admins)


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
    name = request.form['name']
    phone_area = request.form['phone_area']
    phone_prefix = request.form['phone_prefix']
    phone_line = request.form['phone_line']
    admin = request.form['admin']
    # Determine the admin name
    if admin != '3':  # '3' is dedicated for 'Any'
        admin_name = Admin.query.filter_by(id=admin).first().username
    else:
        # invoke function to find the least busy admin
        admin_name = find_least_busy_admin()["username"]

    phone_number = f"+1{phone_area}{phone_prefix}{phone_line}"
    customer = Customer.query.filter_by(phone=phone_number).first()

    if customer is not None:
        flash('You are already in the queue!', 'success')
        return redirect(url_for('welcome'))
    else:
        if admin == '3':
            admin_id = find_least_busy_admin()["id"]
        else:
            admin_id = admin

        new_customer = Customer(name=name, phone=phone_number, admin_id=admin_id)
        db.session.add(new_customer)
        db.session.commit()

        wait_time = 15 * (Customer.query.filter_by(admin_id=admin).count() - 1)
        message_body = f"Eid Mubarak! Thank you {name} for joining the queue. Your estimated wait time is {wait_time} minutes."
        client = Client(account_sid, auth_token)
        try:
            print("Sending message...")
            # message = client.messages.create(
            #     body=message_body,
            #     from_=twilio_phone_number,
            #     to=phone_number
            # )
            flash(
                f'Thank you {name} for joining the queue. Hena artitst {admin_name} is thrilled that you could join us. Your estimated wait time is {wait_time} minutes.',
                'success')

            return redirect(url_for('welcome'))
        except Exception as e:
            db.session.rollback()  # Rollback any changes
            db.session.query(Customer).filter(Customer.phone == phone_number).delete()  # Delete the customer
            db.session.commit()  # Commit the delete operation

            flash(f"Error: Please provide a valid phone number!", "error")
            return redirect(url_for('index'))


def find_least_busy_admin():
    all_admins = Admin.query.all()
    least_busy_admin = {}
    min_customers = float('inf')

    for admin in all_admins:
        customers_count = Customer.query.filter_by(admin_id=admin.id).count()
        if customers_count < min_customers:
            min_customers = customers_count
            least_busy_admin = {"id": admin.id, "username": admin.username}

    return least_busy_admin


def add_predefined_admins():
    admins = [
        {"username": "Naba", "password": "mehndi123"},
        {"username": "Basma", "password": "mehndi123"}
    ]

    for admin in admins:
        try:
            existing_admin = Admin.query.filter_by(username=admin["username"]).first()
            if not existing_admin:
                hashed_password = generate_password_hash(admin["password"])
                new_admin = Admin(username=admin["username"], password=hashed_password)
                db.session.add(new_admin)
                db.session.commit()
                print(f"Admin {admin['username']} added successfully.")
            else:
                print(f"Admin {admin['username']} already exists.")
        except SQLAlchemyError as e:
            print(f"Error while adding admin {admin['username']}: {e}")


@app.route('/send_sms_to_customers_invite', methods=['POST'])
def send_sms_to_customers_invite():
    customer_ids = request.form.getlist('customer_ids')
    success_count = 0
    error_count = 0

    for customer_id in customer_ids:
        customer = Customer.query.get(customer_id)
        if customer:
            try:
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                    body=f"It's your turn, please come to the desk. Happy Mehndi! :)",
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


@app.route('/send_sms_to_customers_thankyou', methods=['POST'])
def send_sms_to_customers_thankyou():
    customer_ids = request.form.getlist('customer_ids')
    success_count = 0
    error_count = 0

    for customer_id in customer_ids:
        customer = Customer.query.get(customer_id)
        if customer:
            try:
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                    body="Thank you for visiting us! We hope you enjoyed your experience. Follow the artists on Instagram @henna_by_naba and @basus_mehndi_art. Hope to see you again soon!",
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
    # images = Image.query.all()
    images = Image_DB.query.order_by(Image_DB._id.desc()).all()
    return render_template('welcome.html', images=images)


@app.route('/customers', methods=['GET', 'POST'])
@admin_required
def customers():
    admin_username = session.get('admin_username')
    if admin_username:
        admin = Admin.query.filter_by(username=admin_username).first()
        if admin:
            admin_id = admin.id
            customers = Customer.query.filter_by(admin_id=admin_id).all()
        else:
            customers = []
    else:
        customers = []
    return render_template('customers.html', customers=customers)


@app.route('/image/<int:image_id>')
def serve_image(image_id):
    image = Image_DB.query.get_or_404(image_id)
    return Response(image.data, content_type=image.mimetype)


@app.route('/remove_image/<int:image_id>', methods=['POST'])
@admin_required
def remove_image(image_id):
    image_id = request.json['image_id']
    image = Image_DB.query.get(image_id)
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


def resize_image(image_data, max_size, max_width=800, max_height=800, target_aspect_ratio=4 / 5):
    image = Image.open(io.BytesIO(image_data))

    if len(image_data) <= 1024 * 1024:  # 1MB
        return image_data

    aspect_ratio = float(image.size[0]) / float(image.size[1])
    scale_factor = (max_size / (image.size[0] * image.size[1])) ** 0.5
    new_width = int(image.size[0] * scale_factor)
    new_height = int(image.size[1] * scale_factor)

    if new_width > max_width:
        new_width = max_width
        new_height = int(new_width / aspect_ratio)

    if new_height > max_height:
        new_height = max_height
        new_width = int(new_height * aspect_ratio)

    resized_image = image.resize((new_width, new_height), Image.ANTIALIAS)

    # Add black bars to maintain the target aspect ratio
    if aspect_ratio < target_aspect_ratio:
        new_width = int(new_height * target_aspect_ratio)
    else:
        new_height = int(new_width / target_aspect_ratio)

    padded_image = ImageOps.pad(resized_image, (new_width, new_height), color="black", centering=(0.5, 0.5))
    resized_image = padded_image

    image_bytes = io.BytesIO()
    resized_image.save(image_bytes, format=image.format)
    return image_bytes.getvalue()


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
            image_data = image_file.read()
            max_size = 512 * 1024  # 1MB

            if len(image_data) > max_size:
                image_data = resize_image(image_data, max_size)

            image_mimetype = image_file.mimetype
            new_image = Image_DB(title=image_title, data=image_data, mimetype=image_mimetype)
            db.session.add(new_image)
            db.session.commit()
            flash('Image uploaded successfully', 'success')
            return redirect(url_for('welcome'))
        else:
            flash('Invalid file type', 'danger')

    return render_template('welcome.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print('test')
    if 'admin_logged_in' in session:
        flash('You are already logged in!', 'info')
        return redirect(url_for('welcome'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        user = Admin.query.filter_by(username=username).first()
        print(user)

        if user and check_password_hash(user.password, password):
            print('test1')
            session['admin_logged_in'] = True
            session.permanent = True
            session['admin_username'] = user.username
            print(session['admin_username'])

            last_visited_page = session.get('last_visited_page', url_for('customers'))
            if last_visited_page.endswith(url_for('index')):
                last_visited_page = url_for('welcome')
            return redirect(last_visited_page)
        else:
            flash('Incorrect username or password! Hint: Ask Atif', 'danger')
            return redirect(url_for('login'))

    referrer = request.referrer
    if referrer and referrer != request.url:
        session['last_visited_page'] = referrer
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


@app.route('/get_admins', methods=['GET'])
def get_admins():
    admins = Admin.query.all()
    admin_list = [{"id": admin.id, "name": admin.username} for admin in admins]
    return jsonify(admin_list)


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
    session.pop('admin_logged_in', None)
    return redirect(url_for('welcome'))


if __name__ == '__main__':
    create_database()
    with app.app_context():
        db.create_all()
        add_predefined_admins()
    app.run(debug=True, host="0.0.0.0", port=5001)
