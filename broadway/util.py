import inspect


def caller():
    stack = inspect.stack()
    outer_caller = stack[1][0].f_locals["self"]
    return outer_caller