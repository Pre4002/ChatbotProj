from flask import Flask, request, jsonify, session, render_template,url_for,flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.secret_key = 'your_secret_key'  # Required for session management
db = SQLAlchemy(app)

# Model for the ticket
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(100), nullable=False)
    ticket_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Status can be 'Pending', 'Completed', or 'Canceled'

# Create the database if it doesn't exist
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/chatbot', methods=['GET'])
def chatbot():
    return render_template('chatbot.html')
    data = request.get_json()
    user_message = data.get('message', '').lower()
    state = session.get('state', 'waiting')

    response = ''
    next_state = None

    # Chatbot states for booking tickets
    if 'book' in user_message:
        session['state'] = 'awaiting_name'
        response = "Sure, I can help you book a ticket. Please provide your name and ticket type."
        next_state = 'awaiting_name'

    elif state == 'awaiting_name':
        session['visitor_name'] = user_message.title()
        session['state'] = 'awaiting_ticket_type'
        response = f"Thank you, {session['visitor_name']}. Now, please provide the type of ticket you need (adult, child, senior)."
        next_state = 'awaiting_ticket_type'

    elif state == 'awaiting_ticket_type':
        ticket_type = user_message.lower()
        valid_ticket_types = ['adult', 'child', 'senior']
        if ticket_type in valid_ticket_types:
            new_ticket = Ticket(visitor_name=session['visitor_name'], ticket_type=ticket_type)
            db.session.add(new_ticket)
            db.session.commit()
            session.pop('state', None)  # Clear the session state after booking
            response = f'Thank you, {session["visitor_name"]}. Your {ticket_type} ticket has been successfully booked.'
            return jsonify({'response': response, 'ticket_id': new_ticket.id})
        else:
            response = 'Invalid ticket type. Please provide one of the following: adult, child, or senior.'

    # Chatbot states for canceling tickets
    elif 'cancel' in user_message:
        session['state'] = 'awaiting_ticket_id'
        response = "Please provide your ticket ID to cancel your booking."
        next_state = 'awaiting_ticket_id'

    elif state == 'awaiting_ticket_id':
        try:
            ticket_id = int(user_message)
        except ValueError:
            response = 'Invalid Ticket ID format. Please provide a numeric Ticket ID.'
            return jsonify({'response': response})

        ticket = Ticket.query.get(ticket_id)
        if ticket:
            db.session.delete(ticket)
            db.session.commit()
            session.pop('state', None)  # Clear the session state after cancellation
            response = f'Ticket ID {ticket_id} canceled successfully!'
        else:
            response = 'Ticket not found. Please check the ticket ID and try again.'

    # Handling requests to view current booking
    elif 'current booking' in user_message or 'current' in user_message:
        visitor_name = session.get('visitor_name')
        if not visitor_name:
            response = "Please provide your name first."
            session['state'] = 'awaiting_name'
        else:
            ticket = Ticket.query.filter_by(visitor_name=visitor_name, status='Pending').first()
            if ticket:
                response = f"Your current booking: Ticket ID {ticket.id}, Ticket Type: {ticket.ticket_type}, Status: {ticket.status}."
            else:
                response = 'No active current bookings found.'

    # Handling requests to view previous bookings
    elif 'previous bookings' in user_message or 'previous' in user_message:
        visitor_name = session.get('visitor_name')
        if not visitor_name:
            response = "Please provide your name first."
            session['state'] = 'awaiting_name'
        else:
            previous_tickets = Ticket.query.filter(
                Ticket.visitor_name == visitor_name,
                Ticket.status.in_(['Completed', 'Canceled'])
            ).all()

            if previous_tickets:
                response = "Your previous bookings:\n"
                for ticket in previous_tickets:
                    response += f"Ticket ID {ticket.id}, Ticket Type: {ticket.ticket_type}, Status: {ticket.status}\n"
            else:
                response = 'No previous bookings found.'

    # Default response handling
    else:
        if 'hi' in user_message:
            response = "How can I help you?"
        elif 'museum' in user_message:
            response = "The museum is open from 9 AM to 5 PM. We have various exhibits including art, history, and science."
        elif 'ticket' in user_message:
            response = "To book a ticket, please provide your name and the type of ticket you need."
        elif 'details' in user_message:
            response = "Could you specify what details you need? For example, exhibit details, ticket prices, or opening hours."
        elif 'hours' in user_message:
            response = "The museum is open from 9 AM to 5 PM every day except Mondays."
        elif 'price' in user_message:
            response = "Ticket prices are $10 for adults, $7 for children, and $8 for seniors. Special rates may apply for group bookings."
        else:
            response = "I'm not sure how to help with that. Can you please provide more details or ask about something specific?"

    return jsonify({'response': response, 'nextState': next_state})

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


@app.route('/book_ticket', methods=['POST'])
def book_ticket():
    data = request.get_json()
    visitor_name = data.get('visitor_name', '')
    ticket_type = data.get('ticket_type', '').lower()

    valid_ticket_types = ['adult', 'child', 'senior']
    if visitor_name and ticket_type in valid_ticket_types:
        new_ticket = Ticket(visitor_name=visitor_name, ticket_type=ticket_type)
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify({
            'message': 'Ticket booked successfully!',
            'ticket_id': new_ticket.id  # Include the ID of the newly created ticket
        })
    else:
        return jsonify({'message': 'Failed to book ticket. Please provide valid details.'}), 400

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
