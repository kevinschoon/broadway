import asyncio
from asyncio import coroutine
from broadway import *


class Printer(Actor):
    @coroutine
    def receive(self, message):
        print(message)

class Sender(Actor):
    def __init__(self, dummy):
        self.context.system.exec(self.send_100_to(dummy))

    @coroutine
    def send_100_to(self, dummy):
        for count in range(1, 101):
            yield from dummy.tell("actor %s" % count)
        yield from asyncio.sleep(0.1)
        yield from self.context.system.stop()


def main():
    s = ActorSystem()
    printer = s.actor_of(Printer)
    s.actor_of(Props(Sender, printer))

    s.run_until_stop(exit_after=True)

if __name__ == "__main__":
    main()