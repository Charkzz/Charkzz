from frontend import db
from shared import Log
from typing import *


def commit(element: db.Model) -> int:
    try:
        Log.debug(f"Adding to {type(element)} element to database.")
        db.session.add(element)
        #db.session.commit()
        Log.debug(f"Success!")
    except Exception as e:
        Log.debug(f"Failure!")
        raise e

def commit_all(elements: List[db.Model]):
    def wrapper(elements, *args):
        try:
            Log.debug(f"Adding elements to database. elements: {[type(x) for x in elements]}")
            db.session.add_all(elements)
            #db.session.commit()
            Log.debug(f"Success!")
        except Exception as e:
            Log.debug(f"Failure!")
            raise e
    return wrapper
