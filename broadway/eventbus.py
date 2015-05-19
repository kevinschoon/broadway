import asyncio
from asyncio import coroutine
import random
from collections import namedtuple, defaultdict
from broadway.util import caller

Message = namedtuple('Message', ['channel', 'payload'])


class DummyLoader():
    def load(self, raw_data):
        return raw_data


class EventBus():
    def subscribe(self, channel, handlers):
        raise NotImplementedError()

    def unsubscribe(self, channel, handlers):
        raise NotImplementedError()

    @coroutine
    def publish(self, channel, payload):
        raise NotImplementedError()


class ActorEventBus(EventBus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribers = defaultdict(set)

    def subscribe(self, channel, actors):
        self._subscribers[channel] |= set(actors)
        return self

    def unsubscribe(self, channel, actors):
        if channel in self._subscribers:
            self._subscribers[channel] -= set(actors)
        return self

    @coroutine
    def publish(self, channel, payload):
        sender = caller()
        if channel in self._subscribers:
            for sub in self._subscribers[channel]:
                yield from sub.tell(payload, sender)


class BasicEventBus(EventBus):
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._loaders = {}
        self._bus = asyncio.Queue()
        self._subscribers = {}

    def backlog(self):
        return self._bus.qsize()

    def subscribe(self, channel, handlers, loader=None):
        if loader:
            self._loaders[channel] = loader
        channel_handlers = self._subscribers.setdefault(channel, [])
        channel_handlers += handlers
        return self

    def unsubscribe(self, channel, handlers):
        if channel in self._subscribers:
            self._subscribers[channel] -= handlers
        return self

    @coroutine
    def publish(self, channel, data):
        msg = Message(channel, data)
        yield from self._bus.put(msg)

    @coroutine
    def start(self):
        while True:
            msg = yield from self._bus.get()
            event = self._loaders.setdefault(msg.channel, DummyLoader()).load(msg.payload)
            if msg.channel in self._subscribers:
                for handler in self._subscribers[msg.channel]:
                    self.loop.create_task(handler(event))

    def run_forever(self):
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

if __name__ == "__main__":
    class Runner():
        def __init__(self, name):
            self.name = name
            self.count = 0

        @coroutine
        def process(self, event):
            self.count += 1
            print(self.name, event, self.count)

    @coroutine
    def hello_world(bus):
        while True:
            bus.publish("/hello" if random.random() < 0.5 else "/bye", "world")
            yield from asyncio.sleep(0.1)

    bus = BasicEventBus()\
        .subscribe("/hello", [Runner("hello").process])\
        .subscribe("/bye", [Runner("bye").process])

    asyncio.Task(bus.start())
    asyncio.Task(hello_world(bus))
    bus.run_forever()