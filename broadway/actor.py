import asyncio
from concurrent.futures import CancelledError
import inspect
import logging
import time
from broadway.context import Props
from broadway.message import Envelop


def caller():
    stack = inspect.stack()
    outer_caller = stack[1][0].f_locals["self"]
    return outer_caller


class Actor():
    def __init__(self, loop, context, max_inbox_size=0):
        self._loop = loop
        self._max_inbox_size = max_inbox_size
        self._inbox = asyncio.Queue(maxsize=self._max_inbox_size,
                                    loop=self._loop)
        self.await_complete = None
        self.context = context
        context.this = self
        self._resume = None

    @asyncio.coroutine
    def receive(self, message: 'Any'):
        pass

    @asyncio.coroutine
    def tell(self, message: 'Any', sender=None):
        if not sender:
            sender = caller()
        yield from self._deliver(Envelop(sender, message, time.time()))

    @asyncio.coroutine
    def ask(self, message: 'Any') -> asyncio.Future:
        promise_actor = self.context.actor_of(Props(PromiseActor))
        yield from self.tell(message, sender=promise_actor)
        result = yield from promise_actor.response
        return result

    @asyncio.coroutine
    def _deliver(self, envelop: Envelop):
        yield from self._inbox.put(envelop)

    @asyncio.coroutine
    def pre_start(self):
        pass

    @asyncio.coroutine
    def suspend(self):
        self._resume = asyncio.Future()

    @asyncio.coroutine
    def resume(self):
        if self._resume:
            self._resume.set_result(True)

    @asyncio.coroutine
    def start(self):
        try:
            self.await_complete = asyncio.Future()
            yield from self.pre_start()
            while True:
                if self._resume:
                    yield from self._resume
                envelop = yield from self._inbox.get()
                yield from self._invoke(envelop)
        except CancelledError as e:
            logging.info("task successfully cancelled")
        finally:
            # Signal that the loop has finished.
            if not (self.await_complete.cancelled() or
                self.await_complete.done()):
                self.await_complete.set_result(True)

    # @asyncio.coroutine
    # def _system_message_process(self, message):
    #     if isinstance(message,

    @asyncio.coroutine
    def _invoke(self, envelop):
        try:
            self.context.sender = envelop.sender
            yield from self.receive(envelop.message)
        except CancelledError as e:
            raise e
        except Exception as e:
            self._handle_invoke_failure(e)

    def _handle_invoke_failure(self, e):
        # TODO: need better handling
        logging.exception('Unhandled exception during actor invocation')

    @asyncio.coroutine
    def stop(self):
        if self.await_complete and not (
                    self.await_complete.cancelled() or
                    self.await_complete.done()):
            yield from self.post_stop()
            yield from self.await_complete

    @asyncio.coroutine
    def terminate(self):
        self.context.system.terminate(self)

    @asyncio.coroutine
    def post_stop(self):
        pass


class PromiseActor(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response = asyncio.Future()

    @asyncio.coroutine
    def receive(self, message):
        self.response.set_result(message)
        yield from self.stop()
        # TODO: need to terminate completely


class DeadLetterActor(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = asyncio.Future()

    @asyncio.coroutine
    def receive(self, message):
        # TODO: we need to block mailbox
        pass
