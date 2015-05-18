import asyncio
import random
from broadway.actor import Actor
from broadway.actorsystem import ActorSystem
from broadway.actorref import Props
from broadway.eventbus import ActorEventBus


class DummyActor(Actor):
    def __init__(self, name, partner=None):
        super().__init__()
        self.name = name
        self.partner = partner

    @asyncio.coroutine
    def receive(self, message):
        print(self.name, message)
        if self.partner:
            yield from self.partner.tell(message)

@asyncio.coroutine
def task(bus):
    for count in range(100):
        if random.random() < 0.5:
            yield from bus.publish("/hello", "world %s" % count)
        else:
            yield from bus.publish("/bye", "world %s" % count)
        yield from asyncio.sleep(0.001)
    yield from system.stop()

if __name__ == "__main__":
    system = ActorSystem()
    hello = system.actor_of(Props(DummyActor, "hello"))
    salut = system.actor_of(Props(DummyActor, "salut"))
    bye = system.actor_of(Props(DummyActor, "bye"))

    bus = ActorEventBus()\
        .subscribe("/hello", [hello, salut])\
        .subscribe("/bye", [bye])
    system.run_until_stop([task(bus)], exit_after=True)
