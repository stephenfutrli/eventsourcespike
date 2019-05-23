import functools

@functools.singledispatch
def some_fun(arg):
    """docstring for some_fun"""
    raise NotImplementedError

@some_fun.register(int)
def _(arg: int):
    print('I got integer here!')

@some_fun.register(str)
def _(arg: str):
    print('Hey, you gave me str!')

some_fun(1)
some_fun('2')
