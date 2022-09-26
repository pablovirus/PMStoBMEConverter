from functools import wraps

#Simple Verbose
def verbose(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f'Calling \'{func.__name__}\' with arguments {args} and {kwargs}')
        result = func(*args, **kwargs)
        print(f'     Got result {result}')
        return result
    return wrapper

#Debug
import logging
import importlib

importlib.reload(logging)
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
        level=logging.DEBUG, datefmt='%I:%M:%S',) #can add filename here as a kwarg

def debug(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        logging.debug(f"Invoking \'{fn.__name__}\'")
        logging.debug(f"    args: {args}")
        logging.debug(f"    kwargs: {kwargs}")
        result = fn(*args, **kwargs)
        logging.debug(f"    returned {result}")
        return result
    return wrapper