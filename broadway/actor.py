from asyncio import coroutine


class Actor():
    context = None

    @coroutine
    def receive(self, message: 'Any'):
        pass

    @coroutine
    def pre_start(self):
        pass

    @coroutine
    def post_stop(self):
        pass

    @property
    def sender(self):
        return self.context.sender


class DeadLetterActor(Actor):
    @coroutine
    def receive(self, message):
        # TODO: we need to block mailbox
        pass
