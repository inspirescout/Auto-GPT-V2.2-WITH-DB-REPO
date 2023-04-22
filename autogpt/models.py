from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os
from autogpt.database import db
app = Flask(__name__)

# Set up SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unique_ids.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Add other user-related fields if necessary
    agents = db.relationship('Agent', backref='user', lazy=True)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unique_id = db.Column(db.String, nullable=False)
    ai_name = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)
    goals = db.Column(db.String, nullable=True)
    conversations = db.relationship('Conversation', backref='agent', lazy=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=False)
    prompt = db.Column(db.String, nullable=False)
    response = db.Column(db.String, nullable=False)
