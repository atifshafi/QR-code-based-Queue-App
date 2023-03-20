# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import create_engine
#
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'mysecretkey'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///queue.db'
#
# db = SQLAlchemy()
#
# class Image(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     url = db.Column(db.String(255), nullable=False)
#
# class Customer(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     phone = db.Column(db.String(20), nullable=False)
#     image_id = db.Column(db.Integer, nullable=True)
#
#     def __init__(self, name, phone):
#         self.name = name
#         self.phone = phone
#
#     def __repr__(self):
#         return '<Customer %r>' % self.name
#
#
# engine = create_engine('sqlite:///queue.db', echo=True)
# db.init_app(app)
# db.create_all(app=app)
#
#
