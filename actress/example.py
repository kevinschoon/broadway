import asyncio
import random
from actress.actor import Actor, ActorSystem

__author__ = 'leonmax'

class DummyActor(Actor):
    def __init__(self, myname, partner=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.myname = myname
        self.partner = partner

    @asyncio.coroutine
    def receive(self, message):
        print(self.myname, message)
        if self.partner:
            yield from self.tell(self.partner, "repeat " + message)

@asyncio.coroutine
def initialize(a, b, c):
    count = 0
    while True:
        count += 1
        msg = "hello %s" % count
        if random.random() > 0.5:
            yield from system.tell(a, msg)
        else:
            yield from system.tell(c, msg)
        yield from asyncio.sleep(0.1)

if __name__ == "__main__":

    system = ActorSystem()
    a = system.act_of("a", DummyActor, "a")
    b = system.act_of("b", DummyActor, "b")
    c = system.act_of("c", DummyActor, "c", b)
    system.init(
        initialize(a, b, c)
    ).run()