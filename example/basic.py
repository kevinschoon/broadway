import asyncio
from asyncio import coroutine as coro
import random
from broadway.actor import Actor
from broadway.actorsystem import ActorSystem
from broadway.cell import Props


class DummyActor(Actor):
    def __init__(self, name, partner=None):
        super().__init__()
        self.name = name
        self.partner = partner

    @coro
    def receive(self, message):
        print(self.name, message)
        if self.partner:
            yield from self.partner.tell(message)

class EchoActor(Actor):
    def __init__(self, name, partner=None):
        super().__init__()
        self.name = name

    @coro
    def receive(self, message):
        yield from self.sender.tell("%s %s" % (self.name, message))

@coro
def task(forwardee, forwarder, dummy, echoer):
    for count in range(100):
        seed = random.random()
        if seed < 0.3:
            yield from forwarder.tell("actor %s" % count)
        elif seed < 0.6:
            yield from dummy.tell("actor %s" % count)
        else:
            message = yield from echoer.ask("actor %s" % count)
            print(message)
        yield from asyncio.sleep(0.001)
    yield from system.stop()

if __name__ == "__main__":
    system = ActorSystem()
    forwardee = system.actor_of(Props(DummyActor, "forwardee"))
    forwarder = system.actor_of(Props(DummyActor, "forwarder", forwardee))
    dummy     = system.actor_of(Props(DummyActor, "dummy    "))
    echoer    = system.actor_of(Props(EchoActor,  "echoer   "))

    coro = task(forwardee, forwarder, dummy, echoer)
    system.run_until_stop([coro], exit_after=True)
