import asyncio
import random
from broadway.actor import Actor
from broadway.actorsystem import ActorSystem
from broadway.cell import Props


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
def task(a, b, c, echoer):
    for count in range(100):
        seed = random.random()
        if seed < 0.3:
            yield from a.tell("actor %s" % count)
        elif seed < 0.6:
            yield from c.tell("actor %s" % count)
        else:
            message = yield from echoer.ask("echo %s" % count)
            print(message)
        yield from asyncio.sleep(0.001)
    yield from system.stop()

if __name__ == "__main__":
    system = ActorSystem()
    a = system.actor_of(Props(DummyActor, "repeat"))
    b = system.actor_of(Props(DummyActor, "hello ", a))
    c = system.actor_of(Props(DummyActor, "bye   "))
    echoer = system.actor_of(Props(EchoActor), "echoer")

    coro=task(a, b, c, echoer)
    system.run_until_stop([coro], exit_after=True)
