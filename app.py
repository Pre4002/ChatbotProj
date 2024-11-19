from flask import Flask, request, jsonify, session, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(100), nullable=False)
    ticket_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Status can be 'Pending', 'Completed', or 'Canceled'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed passwords


with app.app_context():
    db.create_all()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Updated hash method

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if email exists
        user = User.query.filter_by(email=email).first()

        if user:
            # If email exists, check if password is correct
            if check_password_hash(user.password, password):
                # Correct password
                session['user_id'] = user.id
                session['email'] = user.email  # Store email in the session
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                # Incorrect password
                flash('Incorrect password. Please try again.', 'error')
        else:
            # Email not found
            flash('No account found with that email address.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    return render_template('index.html', email=session['email'])



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/events')
def events():
    return render_template('events.html')


@app.route('/gallery')
def gallery():
    return render_template('gallery.html')


@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/bookticket', methods=['GET', 'POST'])
def bookticket():
    if request.method == 'POST':
        visitor_name = request.form['visitor_name']
        ticket_type = request.form['ticket_type']
        ticket_quantity = int(request.form['ticket_quantity'])
        slot = request.form['slot']

        # Create tickets
        tickets = []
        for _ in range(ticket_quantity):
            new_ticket = Ticket(visitor_name=visitor_name, ticket_type=ticket_type, status='Completed')
            db.session.add(new_ticket)
            db.session.flush()  # Generate ticket IDs before committing
            tickets.append(new_ticket.id)

        db.session.commit()

        # Redirect to confirmation page with ticket details
        return redirect(url_for('ticketconfirm', visitor_name=visitor_name, ticket_quantity=ticket_quantity, ticket_ids=','.join(map(str, tickets)), slot=slot))

    return render_template('bookticket.html')

@app.route('/ticketconfirm')
def ticketconfirm():
    # Fetch query parameters from the URL
    visitor_name = request.args.get('visitor_name')
    ticket_quantity = request.args.get('ticket_quantity')
    ticket_ids = request.args.get('ticket_ids').split(',')
    slot = request.args.get('slot')

    return render_template('ticketconfirm.html', visitor_name=visitor_name, ticket_quantity=ticket_quantity, ticket_ids=ticket_ids, slot=slot)


@app.route('/previous_bookings', methods=['POST'])
def previous_bookings():
    data = request.get_json()
    visitor_name = session.get('visitor_name')
    
    if not visitor_name:
        return jsonify({'message': 'Please provide your name first.'}), 400

    previous_tickets = Ticket.query.filter(
        Ticket.visitor_name == visitor_name,
        Ticket.status.in_(['Completed', 'Canceled'])
    ).all()

    if previous_tickets:
        bookings = [
            f"Ticket ID {ticket.id}, Ticket Type: {ticket.ticket_type}, Status: {ticket.status}"
            for ticket in previous_tickets
        ]
        return jsonify({'previousBookings': bookings})
    else:
        return jsonify({'previousBookings': []})




@app.route('/get_ticket', methods=['POST'])
def get_ticket():
    data = request.get_json()
    ticket_id = data.get('ticket_id', '')

    if not ticket_id:
        return jsonify({'message': 'Ticket ID is required.'}), 400

    try:
        ticket_id = int(ticket_id)
    except ValueError:
        return jsonify({'message': 'Invalid Ticket ID format. Please provide a numeric Ticket ID.'}), 400

    ticket = Ticket.query.get(ticket_id)
    if ticket:
        return jsonify({
            'ticket_id': ticket.id,
            'visitor_name': ticket.visitor_name,
            'ticket_type': ticket.ticket_type,
            'status': ticket.status
        })
    else:
        return jsonify({'message': 'Ticket not found.'}), 404

@app.route('/cancel_ticket', methods=['POST'])
def cancel_ticket():
    data = request.get_json()
    ticket_id = data.get('ticket_id', '')

    if not ticket_id:
        return jsonify({'message': 'Ticket ID is required.'}), 400

    try:
        ticket_id = int(ticket_id)
    except ValueError:
        return jsonify({'message': 'Invalid Ticket ID format. Please provide a numeric Ticket ID.'}), 400

    ticket = Ticket.query.get(ticket_id)
    if ticket:
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({'message': f'Ticket ID {ticket_id} canceled successfully!'})
    else:
        return jsonify({'message': 'Ticket not found. Please check the ticket ID and try again.'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
