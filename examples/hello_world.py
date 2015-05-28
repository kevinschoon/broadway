import asyncio

from broadway.actorref import Props
from broadway.actor import Actor
from broadway.actorsystem import ActorSystem


class Printer(Actor):
    """
    Simple Actor that prints a message and increments a counter
    """
    counter = 0

    @asyncio.coroutine
    def receive(self, message):
        self.counter += 1
        print(message + ' world ({})'.format(self.counter))

class Sender(Actor):
    """
    Simple Actor that sends 5 messages
    """
    def __init__(self, dummy):
        self.context.system.exec(self.send_five(dummy))

    @asyncio.coroutine
    def send_five(self, dummy):
        for count in range(1, 6):
            yield from dummy.tell("hello")
        yield from asyncio.sleep(0.1)
        yield from self.context.system.stop()


def main():
    s = ActorSystem()
    printer = s.actor_of(Printer)
    s.actor_of(Props(Sender, printer))

    s.run_until_stop(exit_after=True)

if __name__ == "__main__":
    main()
