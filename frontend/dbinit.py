from flask_sqlalchemy import SQLAlchemy
from frontend.models import User, Airport, Flight, Plane, PlaneModel
from datetime import datetime, timedelta
from shared import Log
from werkzeug.security import generate_password_hash
from flask import url_for


def make_user(i: int, is_admin: bool = False, email: str = ""):
    if email == "":
        email = f"user{i}@example.com"
    password = generate_password_hash("123456", method='sha256')
    return User(**{"id": i,
                   "email": email,
                   "password": password,
                   "first_name": "Bester",
                   "last_name": f"User{i}",
                   "admin": is_admin})


def make_airport_1():
    return Airport(**{"acronym": "BER", "name": "Berlin"})


def make_airport_2():
    return Airport(**{"acronym": "GOT", "name": "Goettingen"})


def make_plane_1():
    return Plane(**{"plane_model_id": 1})


def make_flight(i: int = 1,
                origin: Airport = make_airport_1(),
                destination: Airport = make_airport_2()):
    dtime: datetime = datetime.utcnow() + timedelta(hours=5)
    atime: datetime = dtime + timedelta(hours=10)
    return Flight(**{"id": i,
                     "plane_id": 1,
                     "origin_id": 1,
                     "destination_id": 2,
                     "departure_time": dtime,
                     "arrival_time": atime})


def populate_database(db: SQLAlchemy):
    Log.debug("Starting to populate database")
    # users
    Log.debug("Adding users...")
    db.session.add(make_user(1, email="admin@example.com", is_admin=True))
    db.session.add(make_user(2))
    db.session.add(make_user(3))
    db.session.add(make_user(4))
    db.session.commit()
    Log.debug("Committed database changes.")
    # airports
    Log.debug("Adding airports...")
    ap1 = Airport.commit_airport(acronym="KAF", name="KaufLand")
    ap2 = Airport.commit_airport(acronym="GOE", name="Goettingen")
    ap3 = Airport.commit_airport(acronym="SHA", name="ShangHai")
    Log.debug("Committed database changes.")
    # plane model
    Log.debug("Adding plane models...")
    plane_model1 = PlaneModel.populate_from_file(
        '/home/sbrt/code/python/python_course/plane-seat-booking/frontend/data/chartIn1.txt')
    plane_model2 = PlaneModel.populate_from_file(
        '/home/sbrt/code/python/python_course/plane-seat-booking/frontend/data/chartIn2.txt')
    plane_model3 = PlaneModel.populate_from_file(
        '/home/sbrt/code/python/python_course/plane-seat-booking/frontend/data/chartIn3.txt')
    plane_model4 = PlaneModel.populate_from_file(
        '/home/sbrt/code/python/python_course/plane-seat-booking/frontend/data/chartIn4.txt')
    # plane
    Log.debug("Adding planes...")
    # db.session.add(make_plane_1())
    plane1 = plane_model2.commit_new_plane("CharkzWon")
    plane2 = plane_model2.commit_new_plane("CharkzToo(frustrated)")
    plane2 = plane_model2.commit_new_plane("CharkzThree")
    Log.debug("Committed database changes.")
    # flights
    Log.debug("Adding flights...")
    fl1 = plane1.commit_new_flight(origin_id=ap1.id,
                                   destination_id=ap2.id,
                                   departure_time=datetime.utcnow() + timedelta(hours=5),
                                   arrival_time=datetime.utcnow() + timedelta(hours=10))
    fl2 = plane2.commit_new_flight(origin_id=ap3.id,
                                   destination_id=ap2.id,
                                   departure_time=datetime.utcnow() + timedelta(hours=1),
                                   arrival_time=datetime.utcnow() + timedelta(hours=3))
    fl3 = plane2.commit_new_flight(origin_id=ap1.id,
                                   destination_id=ap3.id,
                                   departure_time=datetime.utcnow() + timedelta(hours=9),
                                   arrival_time=datetime.utcnow() + timedelta(hours=50))
    Log.debug("Committed database changes.")
    # seats
    Log.debug("Adding seats...")
    fl1.commit_seats()
    fl2.commit_seats()
    fl3.commit_seats()
    Log.debug("Committed database changes.")
    Log.debug("Finished init database.")
