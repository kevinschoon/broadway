import asyncio
from asyncio import coroutine
import random
from broadway import *


class DummyActor(Actor):
    def __init__(self, name, partner=None):
        self.name = name
        self.partner = partner

    @coroutine
    def receive(self, message):
        delayed = random.random() / 100
        yield from asyncio.sleep(delayed)
        print("%s %s delayed %2.1f ms" % (self.name, message, delayed * 1000))
        if self.partner:
            yield from self.partner.tell(message)

@coroutine
def task(bus):
    for count in range(1, 101):
        if random.random() < 0.5:
            yield from bus.publish("/hello", "world %s" % count)
        else:
            yield from bus.publish("/bye", "world %s" % count)
        yield from asyncio.sleep(0.001)
    yield from asyncio.sleep(0.1)
    yield from system.stop()

if __name__ == "__main__":
    system = ActorSystem()
    hello = system.actor_of(Props(DummyActor, "hello"))
    salut = system.actor_of(Props(DummyActor, "salut"))
    bye = system.actor_of(Props(DummyActor, "bye"))

    bus = ActorEventBus()\
        .subscribe("/hello", [hello, salut])\
        .subscribe("/bye", [bye])
    system.run_until_stop(task(bus), exit_after=True)
