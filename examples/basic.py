import asyncio
from asyncio import coroutine as coro
import random
from broadway import Actor, Props, ActorSystem


class DummyActor(Actor):
    def __init__(self, name, partner=None):
        super().__init__()
        self.name = name
        self.partner = partner

    @coro
    def receive(self, message):
        delayed = random.random() / 100
        yield from asyncio.sleep(delayed)
        print("%s %s delayed %2.1f ms" % (self.name, message, delayed * 1000))
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
def task(system, forwarder, dummy, echoer):
    for count in range(1, 101):
        seed = random.random()
        if seed < 0.3:
            yield from forwarder.tell("actor %s" % count)
        elif seed < 0.6:
            yield from dummy.tell("actor %s" % count)
        else:
            message = yield from echoer.ask("actor %s" % count)
            print(message)
        yield from asyncio.sleep(0.001)
    yield from asyncio.sleep(0.1)
    yield from system.stop()


def main():
    system = ActorSystem()
    forwardee = system.actor_of(Props(DummyActor, "forwardee"))
    forwarder = system.actor_of(Props(DummyActor, "forwarder", forwardee))
    dummy     = system.actor_of(Props(DummyActor, "dummy    "))
    echoer    = system.actor_of(Props(EchoActor,  "echoer   "))

    coro = task(system, forwarder, dummy, echoer)
    system.run_until_stop([coro], exit_after=True)

if __name__ == "__main__":
    main()