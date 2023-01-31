from typing import *
from flask_login import UserMixin
from enum import Enum
import functools as ft
import re
from shared import Log
from frontend import db
import datetime


class ElementType(Enum):
    EMPTY = "e"
    HALLWAY = "h"
    SEAT = "s"
    KITCHEN = "k"
    BATHROOM = "b"
    COCKPIT = "c"


# Enums
class SeatType(Enum):
    WINDOW = "window"
    MIDDLE = "middle"
    AISLE = "aisle"


class SeatClass(Enum):
    EMERGENCY = "0"
    FIRST = "1"
    BUSINESS = "2"
    ECONOMY = "3"


class SeatClassPrice(Enum):
    EMERGENCY = 200
    FIRST = 1000
    BUSINESS = 500
    ECONOMY = 50


class SeatTypePrice(Enum):
    WINDOW = 200
    MIDDLE = 0
    AISLE = 100


corridor_symbol: str = "h"
default_plane_model_id = 1
corridor_pattern = re.compile('\\| \\|')
whitespaces_pattern = re.compile("\\s+")
seat_pattern = re.compile("[A-W,Y-Z]+")
booked_pattern = re.compile("X")
seat_type_pattern = re.compile("[" + "".join([x.value for x in SeatType]) + "]")
element_type_pattern = re.compile("[" + "".join([x.value for x in ElementType]) + "]")
seat_class_pattern = re.compile("[" + "".join([x.value for x in SeatClass]) + "]")
row_filter_pattern = re.compile("^[0-9]+\\s+")
header_pattern = re.compile("^\\s+[A-Z]*")


class Airport(db.Model):
    __tablename__ = "airport"
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    acronym = db.Column(db.String(5), unique=True, nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # relationships
    # flights_departing = db.relationship("Flight", back_populates="origin")
    # flights_arriving = db.relationship("Flight", back_populates="destination")

    @staticmethod
    def commit_airport(acronym: str, name: str) -> "Airport":
        airport = Airport(acronym=acronym, name=name)
        db.session.add(airport)
        db.session.commit()
        return airport


# DB model classes
class User(db.Model, UserMixin):
    __tablename__ = "user"
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    # optional with default
    admin = db.Column(db.Boolean(), default=False)
    # relationships
    bookings = db.relationship('Booking', back_populates="user")

    # db.Model parent class constructor takes kwargs argument
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # do custom initialization here

    @staticmethod
    def commit_user(email: str, password: str, first_name: str, last_name: str, admin=False) -> "Airport":
        user = User(email=email, password=password, first_name=first_name, last_name=last_name, admin=admin)
        db.session.add(user)
        db.session.commit()
        return user


class Row(db.Model):
    __tablename__ = "row"
    __table_args__ = (db.UniqueConstraint('plane_model_id', 'index', name='_row_uc'),)
    id = db.Column(db.Integer, primary_key=True)
    # must be initialized
    index = db.Column(db.Integer, nullable=False)
    plane_model_id = db.Column(db.Integer, db.ForeignKey('plane_model.id'))
    # optional with default
    emergency_exit = db.Column(db.Boolean, default=False)
    wings = db.Column(db.Boolean, default=False)
    # relationships
    plane_model = db.relationship('PlaneModel', back_populates="rows")
    elements = db.relationship("Element", back_populates="row")

    def __init__(self, **kwargs):
        # do custom initialization here
        # db.Model parent class constructor takes kwargs argument
        super(Row, self).__init__(**kwargs)

    @staticmethod
    def aisles_from_string(row_string: str) -> List[List[Union[str]]]:
        try:
            row_string = row_string.strip()
            aisles: List[List[str]] = [whitespaces_pattern.split(aisle) for aisle in corridor_pattern.split(row_string)]
            n = len(aisles)
            m = len(aisles[0])
            # symmetrisches flugzeug und keine expliziten korridore => mittlerer korridor
            if n == 1 and m % 2 == 0:
                Log.debug(f"No explicit aisles, and even number of seats in row_string '{row_string}'."
                          f"Assuming center corridor. aisles: {aisles}.")
                return [aisles[0][:m // 2], aisles[0][m // 2:]]
            elif n == 1:
                Log.error(f"No aisles and unenven number of seats in row_string '{row_string}'."
                          f"Cannot place corridor. aisles: {aisles}.")
                raise ValueError
            else:
                Log.debug(f"Explicit aisles found in row_string '{row_string}'. aisles: {aisles}.")
                return aisles
        except Exception as e:
            raise e

    @staticmethod
    def seat_string_array_from_aisles(array: List[List[str]]) -> List[str]:
        return ft.reduce(lambda x, y: x + [corridor_symbol] + y, array)

    @staticmethod
    def seat_string_array_from_string(row_string: str) -> List[str]:
        return Row.seat_string_array_from_aisles(Row.aisles_from_string(row_string))

    @staticmethod
    def seat_types_from_string(row_string: str) -> List[SeatType]:
        seat_types = [SeatType.WINDOW]
        aisles = Row.aisles_from_string(row_string)
        for i, aisle in enumerate(aisles):
            for j, seat in enumerate(aisle):
                if (i == 0 and j == 0) or (i == (len(aisles) - 1) and j == (len(aisle) - 1)):
                    # window seat
                    pass
                elif j == 0 or j == (len(aisle) - 1):
                    # aisle seat
                    seat_types += [SeatType.AISLE]
                else:
                    # middle
                    seat_types += [SeatType.MIDDLE]
            if i < len(aisles) - 1:
                seat_types += [None]
            else:
                seat_types += [SeatType.WINDOW]

        return seat_types

    @staticmethod
    def commit_from_string(row_string: str,
                           index: int,
                           header: List[str],
                           plane_model_id=default_plane_model_id,
                           seat_class=SeatClass.ECONOMY) -> "Row":
        try:
            Log.debug(f"Starting to build element list for row {index}")
            # delete row index from row_string
            row_string = re.sub(row_filter_pattern, "", row_string)
            # create row
            row = Row(index=index, plane_model_id=plane_model_id)
            db.session.add(row)
            db.session.commit()
            # add elements and seats
            seats = Row.seat_string_array_from_string(row_string)
            seat_types = Row.seat_types_from_string(row_string)
            Log.debug(f"seat_types: {seat_types}")
            Log.debug(f"seats: {seats}")
            Log.debug(f"header: {header}")
            if len(seats) != len(header):
                Log.debug(f"'{row_string}'")
                Log.error(
                    f"Row {index} has invalid row_string '{row_string}'\n"
                    f"(seats: '{seats}', seat_types: '{seat_types}', header: '{header}'")
                raise IOError(
                    f"Row {index} has invalid row_string '{row_string}'\n"
                    f"(seats: '{seats}', seat_types: '{seat_types}', header: '{header}'")
            for col_index, element_string in enumerate(seats):
                element: Element = Element.make_from_string(element_string=element_string,
                                                            row_index=index,
                                                            col_index=col_index,
                                                            plane_model_id=plane_model_id)
                db.session.add(element)
                db.session.commit()
                # TODO: hacky, don't db.sessionunderstand why element.id can be None
                if element.type == ElementType.SEAT and element.id:
                    seat = SeatModel.make(element_id=element.id,
                                          seat_type=seat_types[col_index],
                                          seat_class=seat_class)
                    db.session.add(seat)
                    db.session.commit()
            Log.debug(f"Finished building element list for row {index}")
        except Exception as e:
            Log.error(f"Failed in building row elements for row {index}")
            raise e
        try:
            Log.debug(f"Committing element list for row {index} to database.")
            Log.debug("Success!")
        except Exception as e:
            Log.debug("Failure!")
            raise e
        return row

    # def __str__(self):
    #     # TODO: this is infinite loop, handle case of no aisle (i.e. len(self.seat_aisles) == 1)
    #     aisles = list(self.seat_aisles())
    #     if len(aisles) == 1:
    #         return " ".join(aisles[0].elements)
    #     aisle_strings: List[str] = [' '.join(str(aisle)) for aisle in self.seat_aisles()]
    #     return '| |'.join(aisle_strings)

    # def __getitem__(self, val):
    #     return self.elements.__getitem__(val)


class Element(db.Model):
    __tablename__ = 'element'
    __table_args__ = (db.UniqueConstraint('plane_model_id', 'row_index', 'col_index', name='_element_uc'),)
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    plane_model_id = db.Column(db.Integer, db.ForeignKey('plane_model.id'), nullable=False)
    row_index = db.Column(db.Integer, db.ForeignKey('row.index'), nullable=False)
    col_index = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum(ElementType), nullable=False)
    # relationships
    plane_model = db.relationship('PlaneModel', back_populates="elements")
    seat_model = db.relationship("SeatModel", uselist=False, back_populates="element")
    row = db.relationship("Row", back_populates="elements", foreign_keys=[row_index])

    def __init__(self, **kwargs):
        # do custom initialization here
        try:
            # TODO: check if error is thrown, if not all non-nullable parameters are present
            super(Element, self).__init__(**kwargs)
        except Exception as e:
            Log.error("PlaneModel Element instantiation failed.")
            raise e

    @staticmethod
    # @commit
    def make(row_index: int, col_index: int, element_type: ElementType, plane_model_id=default_plane_model_id):
        try:
            return Element(row_index=row_index,
                           col_index=col_index,
                           type=element_type,
                           plane_model_id=plane_model_id)
        except Exception as e:
            raise e

    @staticmethod
    def make_from_string(row_index: int, col_index: int, element_string: str, plane_model_id=default_plane_model_id):
        try:
            booked = False
            # element is free seat with class annotation
            if seat_class_pattern.match(element_string):
                element_type = ElementType.SEAT
                Log.debug(f"Seat class {element_string}: {row_index}.{col_index} ")
            # element is a free seat without class annotation
            elif seat_pattern.match(element_string):
                element_type = ElementType.SEAT
                Log.debug(f"Seat: {row_index}.{col_index}")
            # TODO: this is hacky, but was required due to chartln2
            # booked seat
            elif booked_pattern.match(element_string):
                element_type = ElementType.SEAT
                booked = True
                Log.debug(f"Booked seat: {row_index}.{col_index}")
            # element is not a seat
            elif element_type_pattern.match(element_string):
                element_type = ElementType(element_string).name
                Log.debug(f"Element {element_string}: {row_index}.{col_index}")
            else:
                raise IOError(f"Unknown element character '{element_string}' encountered at {row_index}.{col_index}.")

            elem = Element.make(row_index=row_index,
                                col_index=col_index,
                                element_type=element_type,
                                plane_model_id=plane_model_id)
            return elem
        except Exception as e:
            raise e


class SeatModel(db.Model):
    __tablename__ = "seat_model"
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    element_id = db.Column(db.Integer, db.ForeignKey('element.id'), unique=True, nullable=False)
    type = db.Column(db.Enum(SeatType), nullable=False)
    # optional with default
    seat_class = db.Column(db.Enum(SeatClass), default=SeatClass.ECONOMY)
    # relationships
    element = db.relationship("Element", back_populates="seat_model", foreign_keys=[element_id])
    seats = db.relationship('Seat', back_populates="seat_model")

    def __init__(self, **kwargs):
        # do custom initialization here
        # db.Model parent class constructor takes kwargs argument
        super(SeatModel, self).__init__(**kwargs)

    @staticmethod
    def make(element_id: int, seat_type: SeatType, seat_class: SeatClass.ECONOMY):
        try:
            return SeatModel(element_id=element_id,
                             type=seat_type,
                             seat_class=seat_class)
        except Exception as e:
            raise e

    # TODO!!!! check if still working
    # TODO: Eventuell Horner-Schema
    def column_as_letter(self):
        count_z = (self.element.col_index // 26)
        if self.element.col_index - count_z * 26 != 0:
            letter = chr((self.element.col_index - count_z * 26) % 26 + ord('A') - 1)
        else:
            letter = ""
        return str(count_z * "Z" + letter)

    def seat_string(self):
        x = str(self.element.row_index)
        y = self.column_as_letter()
        return str(x + y)


class Seat(db.Model):
    __tablename__ = "seat"
    __table_args__ = (db.UniqueConstraint('flight_id', 'seat_model_id', name='_seat_uc'),)
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    seat_model_id = db.Column(db.Integer, db.ForeignKey('seat_model.id'))
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'))
    # optional with default
    price = db.Column(db.Float, default=5)
    # relationships
    seat_model = db.relationship('SeatModel', back_populates="seats", foreign_keys=[seat_model_id])
    flight = db.relationship('Flight', back_populates="seats", foreign_keys=[flight_id])
    booking = db.relationship('Booking', back_populates="seat", uselist=False)

    def __init__(self, **kwargs):
        # do custom initialization here
        # db.Model parent class constructor takes kwargs argument
        super(Seat, self).__init__(**kwargs)

    # TODO: not working, why does seat_model not have any properties?
    def __str__(self):
        # TODO (low): use Position.getColumnLetter to replace self.letter
        return 'X' if self.booked else self.seat_model

    # TODO!!!
    def book(self) -> bool:
        pass

    def booked(self) -> bool:
        return True if self.booking else False

    # TODO: Eventuell Horner-Schema
    # def column_as_letter(self):
    #     count_Z = (self.column // 26)
    #     if (self.column - count_Z * 26 != 0):
    #         letter = chr((self.column - count_Z * 26) % 26 + ord('A') - 1)
    #     else:
    #         letter = ""
    #     return str(count_Z * "Z" + letter)
    #
    #
    # def seat_string(self):
    #     x = str(self.row)
    #     y = self.column_as_letter()
    #     return str(x + y)


class Plane(db.Model):
    __tablename__ = "plane"
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    plane_model_id = db.Column(db.Integer, db.ForeignKey('plane_model.id'))
    name = db.Column(db.String(40), unique=True)
    # relationships
    plane_model = db.relationship('PlaneModel', back_populates="planes")
    flights = db.relationship('Flight', back_populates="plane")

    def __init__(self, **kwargs):
        # do custom initialization here
        super(Plane, self).__init__(**kwargs)

    def commit_new_flight(self,
                          origin_id: int,
                          destination_id: int,
                          departure_time: datetime,
                          arrival_time: datetime) -> "Flight":
        flight = Flight(plane_id=self.id,
                        origin_id=origin_id,
                        destination_id=destination_id,
                        departure_time=departure_time,
                        arrival_time=arrival_time)
        db.session.add(flight)
        db.session.commit()
        return flight


class PlaneModel(db.Model):
    __tablename__ = "plane_model"
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    header_string = db.Column(db.String, nullable=False)
    # relationships
    planes = db.relationship('Plane', back_populates="plane_model")
    elements = db.relationship('Element', back_populates="plane_model")
    rows = db.relationship('Row', back_populates="plane_model")

    def __init__(self, **kwargs):
        # do custom initialization here
        super(PlaneModel, self).__init__(**kwargs)

    def seat_models(self) -> List[SeatModel]:
        return [element.seat_model for element in self.elements if element.type == ElementType.SEAT]

    def header(self) -> List[str]:
        return Row.seat_string_array_from_string(self.header_string)

    @staticmethod
    def populate_from_file(file: str) -> "PlaneModel":
        try:
            try:
                file = open(file)
            except IOError as e:
                Log.error(f"{file} does not exist.")
                raise e
            header_string = file.readline()
            if not header_pattern.match(header_string):
                Log.error(f"PlaneModel file {file} is missing header row. Will not parse.")
                return
            header_string = header_string.strip()
            Log.debug(f"Header: {header_string}")
            header = Row.seat_string_array_from_string(header_string)
            model = PlaneModel(header_string=header_string)
            db.session.add(model)
            db.session.commit()
            index = 1
            for line in file.readlines():
                try:
                    Row.commit_from_string(row_string=line, header=header, index=index, plane_model_id=model.id)
                except Exception as e:
                    Log.error(f"Error creating row {index} (0 is header).")
                    raise e
                index += 1
            db.session.commit()
        except IOError as e:
            Log.error(f"Cannot read plane model {file}.")
            raise e
        return model

    def commit_new_plane(self, name) -> Plane:
        plane = Plane(plane_model_id=self.id, name=name)
        db.session.add(plane)
        db.session.commit()
        return plane


class Flight(db.Model):
    __tablename__ = "flight"
    # must be initialized
    id = db.Column(db.Integer, primary_key=True)
    plane_id = db.Column(db.Integer, db.ForeignKey('plane.id'), nullable=False)
    origin_id = db.Column(db.Integer, db.ForeignKey('airport.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('airport.id'), nullable=False)
    departure_time = db.Column(db.DateTime(), nullable=False)
    arrival_time = db.Column(db.DateTime(), nullable=False)
    # relationships
    seats = db.relationship('Seat', back_populates="flight")
    bookings = db.relationship('Booking', back_populates="flight")
    plane = db.relationship('Plane', back_populates="flights", foreign_keys=[plane_id])

    def __init__(self, **kwargs):
        # do custom initialization here
        # db.Model parent class constructor takes kwargs argument
        super(Flight, self).__init__(**kwargs)

    @classmethod
    def calculate_price(cls, seat_model: SeatModel) -> float:
        if seat_model.seat_class == SeatClass.EMERGENCY:
            class_price = SeatClassPrice.EMERGENCY.value
        elif seat_model.seat_class == SeatClass.BUSINESS:
            class_price = SeatClassPrice.BUSINESS.value
        elif seat_model.seat_class == SeatClass.FIRST:
            class_price = SeatClassPrice.FIRST.value
        else:
            class_price = SeatClassPrice.ECONOMY.value

        if seat_model.type == SeatType.WINDOW:
            type_price = SeatTypePrice.WINDOW.value
        elif seat_model.type == SeatType.MIDDLE:
            type_price = SeatTypePrice.MIDDLE.value
        else:
            type_price = SeatTypePrice.AISLE.value
        return type_price + class_price

    def commit_seats(self):
        plane_model: PlaneModel = self.plane.plane_model
        for seat_model in plane_model.seat_models():
            self.commit_seat(seat_model_id=seat_model.id, price=self.calculate_price(seat_model))

    def commit_seat(self, seat_model_id: int, price: float = 50) -> "Seat":
        seat = Seat(seat_model_id=seat_model_id, flight_id=self.id, price=price)
        db.session.add(seat)
        db.session.commit()
        return seat

    # def commit_seats_from_file(self, path):
    #     try:
    #         file = open(path)
    #     except IOError as e:
    #         Log.error(f"{path} does not exist.")
    #         raise e
    #     header_string = file.readline()
    #     if not header_pattern.match(header_string):
    #         Log.error(f"File {path} is missing header row. Will not parse.")
    #         return
    #     header_string = header_string.strip()
    #     Log.debug(f"Header: {header_string}")
    #     header = Row.seat_string_array_from_string(header_string)
    #     model = PlaneModel(header_string=header_string)
    #     db.session.add(model)
    #     db.session.commit()
    #     index = 1
    #     for line in file.readlines():
    #         try:
    #             Row.commit_from_string(row_string=line, header=header, index=index, plane_model_id=model.id)
    #         except Exception as e:
    #             Log.error(f"Error creating row {index} (0 is header).")
    #             raise e
    #         index += 1
    #     db.session.commit()
    #     except IOError as e:
    #         Log.error(f"Cannot read plane model {file}.")
    #         raise e

    def __str__(self):
        return '\n'.join([str(x) for x in self.plane])

    # def __getitem__(self, val):
    #     # TODO: error handling not enough rows! logging (Leonie)
    #     # Problem:
    #     # myplane = Plane()
    #     # myplane[5]
    #     try:
    #         self.rows[val]
    #     except IndexError:
    #         Log.error("not enough rows")
    #         return self.rows.__getitem__(val)


class Booking(db.Model):
    __tablename__ = "booking"
    __table_args__ = (db.UniqueConstraint('flight_id', 'seat_id', name='_booking_uc'),)
    # must be initialized
    booking_id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # relationships
    flight = db.relationship('Flight', back_populates="bookings", foreign_keys=[flight_id])
    seat = db.relationship('Seat', back_populates="booking", foreign_keys=[seat_id])
    user = db.relationship('User', back_populates="bookings", foreign_keys=[user_id])
