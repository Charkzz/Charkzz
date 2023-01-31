from jinja2 import Environment, FileSystemLoader
from frontend.dbinit import make_user
import matplotlib.pyplot as plt
from typing import *
import os

if not os.path.exists("output"):
    os.mkdir("output")

env = Environment(loader=FileSystemLoader('../templates'))
tmpl = env.get_template('admin.html')

# mocks
current_user: Dict[str, any] = {"id": 1, "admin": True}  # admin
seats_booked = ["1A", "1B", "1C", "2A", "2B", "2C"]
seats_unbooked = ["2B", "3B", "4C", "9A", "6B", "7C", "8B"]

# pie chart data
num_available_seats = len(seats_booked)
num_non_available_seats = len(seats_unbooked)
perc_available_seats = num_available_seats / (num_available_seats + num_non_available_seats) * 100
perc_non_available_seats = num_non_available_seats / (num_available_seats + num_non_available_seats) * 100

labels = ["available seats", "non-available seats"]
sizes = [perc_available_seats, perc_non_available_seats]

# pie chart
fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, autopct="%1.1f%%", shadow=True, startangle=90)
ax1.axis("equal")
chart_path = f"pie_chart_user{current_user['id']}.svg"
plt.savefig("output/" + chart_path)

with open('output/admin.html', 'w') as f:
    print(tmpl.render(chart_path=chart_path,
                      users=[make_user(1, email="admin@example.com", is_admin="True"), make_user(2), make_user(3), make_user(4)],
                      seats_booked=seats_booked,
                      seats_unbooked=seats_unbooked), file=f)
