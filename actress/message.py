import time


class Envelop(object):
    def __init__(self, sender, message):
        self.sender = sender
        self.message = message
        self.timestamp = time.time()

    def __repr__(self):
        return 'Envelop(sender={0}, message={1})'.format(self.sender, self.message)

class Stop(Envelop):
    pass

class Poison(Envelop):
    pass