from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(10), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    trips         = db.relationship('Trip', backref='driver', lazy=True)
    bookings      = db.relationship('Booking', backref='passenger', lazy=True)
    ride_requests = db.relationship('RideRequest', backref='passenger', lazy=True)


class Trip(db.Model):
    __tablename__   = 'trips'
    id              = db.Column(db.Integer, primary_key=True)
    driver_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    origin          = db.Column(db.String(50), nullable=False)
    destination     = db.Column(db.String(50), nullable=False)
    departure_time  = db.Column(db.String(5), nullable=False)
    total_seats     = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    price_per_seat  = db.Column(db.Float, nullable=False)
    status          = db.Column(db.String(20), default='active')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    bookings        = db.relationship('Booking', backref='trip', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id            = db.Column(db.Integer, primary_key=True)
    passenger_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id       = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    seats_booked  = db.Column(db.Integer, nullable=False)
    fare_paid     = db.Column(db.Float, nullable=False)
    status        = db.Column(db.String(20), default='confirmed')
    booked_at     = db.Column(db.DateTime, default=datetime.utcnow)


class RideRequest(db.Model):
    __tablename__  = 'ride_requests'
    id             = db.Column(db.Integer, primary_key=True)
    passenger_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    origin         = db.Column(db.String(50), nullable=False)
    destination    = db.Column(db.String(50), nullable=False)
    preferred_date = db.Column(db.String(20), nullable=False)
    preferred_time = db.Column(db.String(5), nullable=False)
    seats_needed   = db.Column(db.Integer, nullable=False)
    max_budget     = db.Column(db.Integer, nullable=False)
    status         = db.Column(db.String(20), default='open')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)