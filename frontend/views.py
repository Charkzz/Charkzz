from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from frontend.models import *
from frontend import db
import json
from shared import Log
from frontend.dbinit import make_user

# TODO: error handling, particularly for anything interacting with database

views = Blueprint('views', __name__)

header2 = ["", "A", "B", "| |", "C", "D"]

TestFlight = {"rows": [
        {"elements": [
            {"caption": "A", "booked": False, "booking_id": 1, "seat_str": "1A", "seat_id": 1, "seat_class": 1},
            {"caption": "B", "booked": True, "booking_id": None, "seat_str": "1B", "seat_id": 2, "seat_class": 2},
            {"caption": None, "booked": True, "booking_id": 1, "seat_str": "-", "seat_id": 3, "seat_class": 1},
            {"caption": "C", "booked": False, "booking_id": None, "seat_str": "1C", "seat_id": 4, "seat_class": 1},
            {"caption": "D", "booked": False, "booking_id": None, "seat_str": "1D", "seat_id": 5, "seat_class": 0}]},
        {"elements": [
            {"caption": "A", "booked": True, "booking_id": None, "seat_str": "2A", "seat_id": 6, "seat_class": 1},
            {"caption": "B", "booked": False, "booking_id": None, "seat_str": "2B", "seat_id": 7, "seat_class": 1},
            {"caption": None, "booked": True, "booking_id": None, "seat_str": "-", "seat_id": 8, "seat_class": 1},
            {"caption": "C", "booked": False, "booking_id": None, "seat_str": "2C", "seat_id": 9, "seat_class": 1},
            {"caption": "D", "booked": False, "booking_id": None, "seat_str": "3C", "seat_id": 11, "seat_class": 1}]},
        {"elements": [
            {"caption": "A", "booked": False, "booking_id": None, "seat_str": "3A", "seat_id": 22, "seat_class": 1},
            {"caption": "B", "booked": False, "booking_id": None, "seat_str": "3B", "seat_id": 33, "seat_class": 2},
            {"caption": None, "booked": True, "booking_id": 1, "seat_str": "-", "seat_id": 44, "seat_class": 1},
            {"caption": "C", "booked": False, "booking_id": None, "seat_str": "3C", "seat_id": 55, "seat_class": 3},
            {"caption": "D", "booked": False, "booking_id": None, "seat_str": "3D", "seat_id": 66, "seat_class": 1}]},
        {"elements": [
            {"caption": "A", "booked": False, "booking_id": None, "seat_str": "4A", "seat_id": 77, "seat_class": 1},
            {"caption": "B", "booked": True, "booking_id": 2, "seat_str": "4B", "seat_id": 88, "seat_class": 1},
            {"caption": None, "booked": True, "booking_id": 3, "seat_str": "-", "seat_id": 99, "seat_class": 2},
            {"caption": "D", "booked": False, "booking_id": None, "seat_str": "4C", "seat_id": 23, "seat_class": 1},
            {"caption": "E", "booked": True, "booking_id": None, "seat_str": "4D", "seat_id": 24, "seat_class": 3}]}]}

@views.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.id == 1:
        Log.debug("User with id 1 is treated as admin. Rendering admin page.")
        return render_template("admin.html", user=current_user,
                               users=User.query.all(), seats_booked=["1A", "2B"], flight=TestFlight, header_caption=header2)
    else:
        flash('You are not an admin!', category="error")
        Log.debug("User other than id 1 requested admin page, forbidden.")
        return render_template("home.html", user=current_user)


@views.route('/book_a_seat', methods=['GET', 'POST'])
@login_required
def book_a_seat():
    Log.debug("Seat booking endpoint adressed.")
    if request.method == 'POST':
        Log.debug("POST request")
        seat_number = request.form.get('seat_number')

        booked = Seat.query.filter_by(number=seat_number, booked=True).first()
        if booked:
            flash('Seat already booked', category='error')
        else:
            new_booking = Seat(number=seat_number, booked=True, user_id=current_user.id)
            db.session.add(new_booking)
            db.session.commit()
            flash('Booking successful', category='success')
    Log.debug("returning rendering of booking page")
    return render_template("booking_page_fancy.html", user=current_user, flight=TestFlight, header_caption=header2)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    Log.debug("/ endpoint addressed")

    # if request.method == 'POST':
    Log.debug("returning rendering of home page")
    return render_template("home.html", user=current_user)

@views.route('/help', methods=['GET', 'POST'])
def help():
    Log.debug("/help endpoint addressed")

    Log.debug("returning rendering of home page")
    return render_template("help.html", user=current_user)


# @views.route('/delete-note', methods=['POST'])
# def delete_note():
#     note = json.loads(request.data)
#     noteId = note['noteId']
#     note = Note.query.get(noteId)
#     if note:
#         if note.user_id == current_user.id:
#             db.session.delete(note)
#             db.session.commit()
#
#     return jsonify({})


@views.route('/book', methods=['POST'])
def request_confirmation():
    data = json.loads(request.data)
    seat = data['seat']
    note = Booking.query.get(seat)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    return jsonify({})


@views.route('/book', methods=['POST'])
def book():
    data = json.loads(request.data)
    seatId = data['seatId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    # TODO: redirect to confirmation page, only when confirmed make booking (Juan), return rednering of response page with result
    # return  render_template("booking_response.html", user=current_user)
    return jsonify({})
