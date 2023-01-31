from frontend import db
from shared import Log
from functools import wraps

def return_id(func):
    def wrapper(*args, **kwargs) -> int:
        try:
            Log.debug(f"Returning id {element.id}")
            return element.id
        except Exception as e:
            Log.error(f"Error returning id. {kwargs}")
            #raise Exception(e, e.args)
    return wrapper


def commit(func):
    #@wraps(func)
    def wrapper(*args, **kwargs):
        try:
            element = func(*args, **kwargs)
            db.session.add(element)
            db.session.commit()
            Log.debug(f"Adding to database. element: {element}.")
        except Exception as e:
            Log.debug(f"Could not add to database. args: {args}, kwargs: {kwargs}.")
            #raise Exception(e, e.args)
    return wrapper()


def commit_all(func):
    def wrapper(elements, *args):
        try:
            db.session.add(func(elements, *args))
            db.session.commit()
            print(f"Adding to database. elements: {elements}, args: {args}.")
        except Exception as e:
            Log.debug(f"Could not add to database. elements: {elements}, args: {args}.")
            #raise Exception(e, e.args)
    return wrapper
