import functools
from threading import Thread


def new_thread(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        Thread(target=func, args=args, kwargs=kwargs).start()

    return wrapper


def new_thread_daemon(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()

    return wrapper
