from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Trip, Booking, RideRequest
from algorithms import dijkstra, match_trips, compute_fare, CITIES

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email     = request.form['email']
        password  = request.form['password']
        role      = request.form['role']
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))
        user = User(
            full_name     = full_name,
            email         = email,
            password_hash = generate_password_hash(password),
            role          = role
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user     = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'driver':
        trips = Trip.query.filter_by(driver_id=current_user.id).all()
        ride_requests = RideRequest.query.filter_by(status='open').all()
        return render_template('dashboard_driver.html', trips=trips, ride_requests=ride_requests)
    else:
        bookings      = Booking.query.filter_by(passenger_id=current_user.id).all()
        ride_requests = RideRequest.query.filter_by(passenger_id=current_user.id).all()
        return render_template('dashboard_passenger.html', bookings=bookings, ride_requests=ride_requests)

@app.route('/post-trip', methods=['GET', 'POST'])
@login_required
def post_trip():
    if current_user.role != 'driver':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        origin         = request.form['origin']
        destination    = request.form['destination']
        departure_time = request.form['departure_time']
        total_seats    = int(request.form['total_seats'])
        path, distance = dijkstra(origin, destination)
        if not path:
            flash('No route found between selected cities.')
            return redirect(url_for('post_trip'))
        price = compute_fare(distance, total_seats)
        trip = Trip(
            driver_id       = current_user.id,
            origin          = origin,
            destination     = destination,
            departure_time  = departure_time,
            total_seats     = total_seats,
            available_seats = total_seats,
            price_per_seat  = price
        )
        db.session.add(trip)
        db.session.commit()
        flash('Trip posted successfully.')
        return redirect(url_for('dashboard'))
    return render_template('post_trip.html', cities=CITIES)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        origin         = request.form['origin']
        destination    = request.form['destination']
        preferred_time = request.form['preferred_time']
        seats_needed   = int(request.form['seats_needed'])
        max_budget     = int(request.form['max_budget'])
        path, distance = dijkstra(origin, destination)
        if not path:
            flash('No route found between selected cities.')
            return redirect(url_for('search'))
        raw_trips = Trip.query.filter_by(origin=origin, destination=destination, status='active').all()
        available_trips = [{
            'id':              t.id,
            'driver_id':       t.driver_id,
            'driver_name':     User.query.get(t.driver_id).full_name,
            'origin':          t.origin,
            'destination':     t.destination,
            'departure_time':  t.departure_time,
            'total_seats':     t.total_seats,
            'available_seats': t.available_seats,
            'price_per_seat':  t.price_per_seat
        } for t in raw_trips]
        results = match_trips(origin, destination, preferred_time, seats_needed, max_budget, available_trips, distance)
        return render_template('results.html', results=results, path=path, distance=distance,
            seats_needed=seats_needed, origin=origin, destination=destination)
    return render_template('search.html', cities=CITIES)

@app.route('/book/<int:trip_id>', methods=['POST'])
@login_required
def book(trip_id):
    seats_needed = int(request.form['seats_needed'])
    fare         = int(request.form['fare'])
    trip = Trip.query.get_or_404(trip_id)
    if trip.available_seats < seats_needed:
        flash('Not enough seats available.')
        return redirect(url_for('search'))
    booking = Booking(
        passenger_id = current_user.id,
        trip_id      = trip_id,
        seats_booked = seats_needed,
        fare_paid    = fare
    )
    trip.available_seats -= seats_needed
    if trip.available_seats == 0:
        trip.status = 'full'
    db.session.add(booking)
    db.session.commit()
    flash('Booking confirmed!')
    return redirect(url_for('dashboard'))

@app.route('/request-ride', methods=['GET', 'POST'])
@login_required
def request_ride():
    if current_user.role != 'passenger':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        origin         = request.form['origin']
        destination    = request.form['destination']
        preferred_date = request.form['preferred_date']
        preferred_time = request.form['preferred_time']
        seats_needed   = int(request.form['seats_needed'])
        max_budget     = int(request.form['max_budget'])
        if origin == destination:
            flash('Origin and destination cannot be the same.')
            return redirect(url_for('request_ride'))
        ride_request = RideRequest(
            passenger_id   = current_user.id,
            origin         = origin,
            destination    = destination,
            preferred_date = preferred_date,
            preferred_time = preferred_time,
            seats_needed   = seats_needed,
            max_budget     = max_budget
        )
        db.session.add(ride_request)
        db.session.commit()
        flash('Ride request posted successfully. Drivers will be notified.')
        return redirect(url_for('dashboard'))
    return render_template('request_ride.html', cities=CITIES)

@app.route('/accept-request/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    if current_user.role != 'driver':
        return redirect(url_for('dashboard'))
    ride_req = RideRequest.query.get_or_404(request_id)
    path, distance = dijkstra(ride_req.origin, ride_req.destination)
    if not path:
        flash('No route found for this request.')
        return redirect(url_for('dashboard'))
    fare = compute_fare(distance, ride_req.seats_needed)
    trip = Trip(
        driver_id       = current_user.id,
        origin          = ride_req.origin,
        destination     = ride_req.destination,
        departure_time  = ride_req.preferred_time,
        total_seats     = ride_req.seats_needed,
        available_seats = 0,
        price_per_seat  = fare
    )
    db.session.add(trip)
    db.session.flush()
    booking = Booking(
        passenger_id = ride_req.passenger_id,
        trip_id      = trip.id,
        seats_booked = ride_req.seats_needed,
        fare_paid    = fare
    )
    ride_req.status = 'accepted'
    db.session.add(booking)
    db.session.commit()
    flash('Ride request accepted. Trip and booking created automatically.')
    return redirect(url_for('dashboard'))

@app.route('/cancel-request/<int:request_id>', methods=['POST'])
@login_required
def cancel_request(request_id):
    ride_req = RideRequest.query.get_or_404(request_id)
    if ride_req.passenger_id != current_user.id:
        flash('Unauthorised action.')
        return redirect(url_for('dashboard'))
    ride_req.status = 'cancelled'
    db.session.commit()
    flash('Ride request cancelled.')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)