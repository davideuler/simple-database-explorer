class entryExit(object):

    def __init__(self, f):
        self.f = f

    def __call__(self, *args):
        print "Entering", self.f.__name__
        if True:
            self.f(*args)
        print "Exited", self.f.__name__

@entryExit
def foo(a, b):
    print a, b

foo(1, 2)

