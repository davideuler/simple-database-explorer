class Foo:
    def __init__(self, name):
        self.name = name

    # decorator that will see the self.longcondition ???
    class canRun(object):
            def __init__(self, f):
                self.f = f
                self.o = object

            def __call__(self, *args):
                if self.longcondition(): # <-------- ???
                    self.f(*args)

    # this is suppose to be a very long condition :)
    def longcondition(self):
        return isinstance(self.name, str)

    @canRun # <------
    def run(self, times):
        for i in xrange(times):
            print "%s. run... %s" % (i, self.name)

f = Foo("sdf")
f.run(3)