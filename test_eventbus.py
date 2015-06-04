__author__ = 'kevinschoon@gmail.com'

import asyncio
import unittest
import uuid

from broadway import Actor, ActorSystem, ActorEventBus, Props

MESSAGE_COUNT = 10000


class SimpleActor(Actor):

    def __init__(self, count):
        self.messages = list()
        self.count = count

    @asyncio.coroutine
    def receive(self, message: 'Any'):
        self.messages.append(message)
        if len(self.messages) == self.count:
            yield from self.context.system.stop()


class PublishActor(Actor):

    def __init__(self, event_bus, count):
        self.messages = list()
        self.event_bus = event_bus
        self.count = count
        self.context.system.exec(self.publish)

    @asyncio.coroutine
    def publish(self):
        for message in range(0, self.count):
            msg = uuid.uuid4()
            self.messages.append(msg)
            yield from self.event_bus.publish('/simple', msg)


class TestEventBus(unittest.TestCase):
    def setUp(self):
        self.bus = ActorEventBus()
        self.system = ActorSystem()
        self.receiver = self.system.actor_of(Props(SimpleActor, MESSAGE_COUNT))
        self.publisher = self.system.actor_of(Props(PublishActor, self.bus, MESSAGE_COUNT))

    def test_publish(self):
        self.bus.subscribe(channel='/simple', actors=[self.receiver, self.publisher])
        self.system.run_until_stop(exit_after=False)
        r_msg = self.receiver.cell._actor.messages
        p_msg = self.publisher.cell._actor.messages
        msg = frozenset(r_msg).intersection(p_msg)
        self.assertEquals(len(r_msg), MESSAGE_COUNT)
        self.assertEquals(len(p_msg), MESSAGE_COUNT)
        self.assertEquals(len(msg), MESSAGE_COUNT)

