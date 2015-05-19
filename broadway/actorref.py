import time
import asyncio
from asyncio import coroutine
from broadway.message import Envelop
from broadway.util import caller


class Props():
    def __init__(self, actor_class: type, *args, **kwargs):
        self.actor_class = actor_class
        self.args = args
        self.kwargs = kwargs


class ActorRef():
    def __init__(self, name, cell):
        self.name = name
        self.cell = cell

    @coroutine
    def tell(self, message: 'Any', sender=None):
        if not sender:
            sender = caller()
        yield from self.cell.deliver(Envelop(sender, message, time.time()))

    @coroutine
    def ask(self, message: 'Any') -> asyncio.Future:
        promise_actor_ref = PromiseActorRef()
        yield from self.tell(message, sender=promise_actor_ref)
        result = yield from promise_actor_ref.response
        return result


class PromiseActorRef(ActorRef):
    def __init__(self):
        super().__init__("name from actor", "maybe no cell")
        self.response = asyncio.Future()

    @coroutine
    def tell(self, message: 'Any', sender=None):
        self.response.set_result(message)


class ActorRefFactory():
    def actor_of(self, props: Props, actor_name=None):
        raise NotImplementedError()