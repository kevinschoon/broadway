import asyncio
import random
from broadway.actor import Actor
from broadway.actorsystem import ActorSystem
from broadway.cell import Props
from broadway.eventbus import ActorEventBus

__author__ = 'leonmax'

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

class EchoActor(Actor):
    @asyncio.coroutine
    def receive(self, message):
        yield from self.sender.tell(message)

@asyncio.coroutine
def task(bus, a, b, c, echoer):
    count = 0
    while count < 60:
        count += 1
        if count <= 20:
            if random.random() < 0.5:
                yield from a.tell("actor %s" % count)
            else:
                yield from c.tell("actor %s" % count)
        elif count <= 40:
            if random.random() < 0.5:
                yield from bus.publish("/hello", "eventbus %s" % count)
            else:
                yield from bus.publish("/bye", "eventbus %s" % count)
        else:
            message = yield from echoer.ask("echo %s" % count)
            print(message)
        yield from asyncio.sleep(0.01)
    yield from system.stop()

if __name__ == "__main__":

    system = ActorSystem()
    a = system.actor_of(Props(DummyActor, "repeat"))
    b = system.actor_of(Props(DummyActor, "hello ", a))
    c = system.actor_of(Props(DummyActor, "bye   "))
    echoer = system.actor_of(Props(EchoActor), "echoer")

    bus = ActorEventBus()
    bus.subscribe("/hello", [b])
    bus.subscribe("/bye", [c])
    coro=[task(bus, a, b, c, echoer)]
    system.run_until_stop(coro, exit_after=True)
