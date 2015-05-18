import asyncio
from asyncio import coroutine as coro


class Actor():
    def __init__(self):
        self.context = None

    def with_context(self, context):
        self.context = context
        return self

    @coro
    def receive(self, message: 'Any'):
        pass

    @coro
    def pre_start(self):
        pass

    @coro
    def post_stop(self):
        pass

    @property
    def sender(self):
        return self.context.sender


class DeadLetterActor(Actor):
    @coro
    def receive(self, message):
        # TODO: we need to block mailbox
        pass
