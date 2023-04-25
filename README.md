# QR Code Based Queue App

A web application for managing queues using QR codes. This app is built using Python Flask and SQLAlchemy for the backend, with a MySQL database. Users can join the queue by providing their name and phone number. They will then receive an SMS with their estimated wait time.

## Features

- Customers can join a queue by providing their name and phone number
- Admins can view and manage the queue
- SMS notifications for customers when they join the queue and when their turn is near
- Admins can send custom messages to customers in the queue
- Admins can upload images for the welcome page

## Installation

### Requirements

- Python 3.7+
- MySQL

### Steps

1. Clone the repository:

git clone https://github.com/atifshafi/QR-code-based-Queue-App.git


2. Change to the project directory:

cd QR-code-based-Queue-App

3. Create a virtual environment and activate it:

python3 -m venv venv
source venv/bin/activate


4. Install the required packages:

pip install -r requirements.txt


5. Set up environment variables:

- Create a `.env` file in the project directory.
- Add the following variables and set their values accordingly:

```
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=mysql://user:password@host/db_name
```


6. Create a MySQL database and user for the app, and grant the user necessary privileges.

7. Run the application:

python app.py


The application will be accessible at `http://0.0.0.0:5001`.

## Usage

1. Open the app in your web browser.
2. To join the queue, enter your name and phone number, and select the desired admin.
3. You will receive an SMS with your estimated wait time.
4. Admins can log in to manage the queue, send custom messages, and upload images.

## Contributing

Please feel free to submit issues or pull requests to help improve this project.

## License

This project is open-source and available under the MIT License.
