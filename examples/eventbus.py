"""
Hello World EventBus example using the ActorSystem.
"""

import asyncio
import random

from broadway.actor import Actor
from broadway.actorsystem import ActorSystem
from broadway.actorref import Props
from broadway.eventbus import ActorEventBus


class DummyActor(Actor):
    """
    Simple actor that simulates a long running task.
    """
    def __init__(self, name, partner=None):
        self.name = name
        self.partner = partner

    @asyncio.coroutine
    def receive(self, message):
        delayed = random.random() / 100
        yield from asyncio.sleep(delayed)
        print("%s %s delayed %2.1f ms" % (self.name, message, delayed * 1000))
        if self.partner:
            yield from self.partner.tell(message)


@asyncio.coroutine
def task(event_bus):
    """
    Simulate messages being sent to the EventBus.
    :param event_bus: ActorEventBus
    :return: None
    """
    for count in range(1, 101):
        if random.random() < 0.5:
            yield from event_bus.publish("/channel_one", "%s" % count)
        else:
            yield from event_bus.publish("/channel_two", "%s" % count)

        yield from asyncio.sleep(0.001)

    yield from asyncio.sleep(0.1)
    yield from system.stop()

if __name__ == "__main__":

    system = ActorSystem()

    hello = system.actor_of(Props(DummyActor, "hello"))
    world = system.actor_of(Props(DummyActor, "world"))
    bye = system.actor_of(Props(DummyActor, "bye"))

    bus = ActorEventBus().subscribe("/channel_one", [hello])
    bus.subscribe("/channel_two", [world])
    #.subscribe("/bye", [bye])
    system.run_until_stop(task(bus), exit_after=True)