from jinja2 import Environment, FileSystemLoader
from typing import *
import os

if not os.path.exists("output"):
    os.mkdir("output")

env = Environment(loader=FileSystemLoader('../templates'))
tmpl = env.get_template('booking_page_fancy.html')
with open('output/booking.html', 'w') as f:
    print(tmpl.render(header=["A", "B", "| |", "C", "D"], flight={"rows": [
        {"elements": [
            {"caption": "A", "booked": False, "booking_id": 1},
            {"caption": "B", "booked": True, "booking_id": None},
            {"caption": "| |", "booked": True, "booking_id": 1},
            {"caption": "C", "booked": False, "booking_id": None},
            {"caption": "D", "booked": False, "booking_id": None}]},
        {"elements": [
            {"caption": "A", "booked": True, "booking_id": None},
            {"caption": "B", "booked": False, "booking_id": None},
            {"caption": "| |", "booked": True, "booking_id": None},
            {"caption": "C", "booked": False, "booking_id": None},
            {"caption": "D", "booked": False, "booking_id": None}]},
        {"elements": [
            {"caption": "A", "booked": False, "booking_id": None},
            {"caption": "B", "booked": False, "booking_id": None},
            {"caption": "| |", "booked": False, "booking_id": 1},
            {"caption": "C", "booked": False, "booking_id": None},
            {"caption": "D", "booked": False, "booking_id": None}]},
        {"elements": [
            {"caption": "A", "booked": False, "booking_id": None},
            {"caption": "B", "booked": True, "booking_id": 2},
            {"caption": "| |", "booked": True, "booking_id": 3},
            {"caption": "D", "booked": False, "booking_id": None},
            {"caption": "E", "booked": True, "booking_id": None}]}]}), file=f)
