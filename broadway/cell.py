from asyncio import coroutine as coro
import asyncio
from concurrent.futures import CancelledError
import logging
from broadway.actorref import ActorRefFactory, ActorRef, Props
from broadway.message import Envelop


class ActorContext():
    def __init__(self):
        super().__init__()
        self.receive_timeout = None

    @property
    def name(self):
        raise NotImplementedError()

    @property
    def system(self):
        raise NotImplementedError()

    @property
    def props(self):
        raise NotImplementedError()

    @property
    def this(self):
        raise NotImplementedError()

    @property
    def sender(self):
        raise NotImplementedError()


class ActorCell(ActorContext, ActorRefFactory):
    def __init__(self, system, name, props, mailbox):
        super().__init__()
        self._system = system
        self._name = name
        self._props = props
        self._self_ref = ActorRef(name, self)
        self._sender = None
        # TODO: need better actor supervision
        self._actor = self.new_actor()

        self._loop = system._loop
        self._inbox = mailbox
        self.task = None
        self.await_complete = None
        self.receive_timeout = None
        self._resume = None

    def new_actor(self):
        actor_class = self._props.actor_class
        args = self._props.args
        kwargs = self._props.kwargs
        actor = actor_class(*args, **kwargs).with_context(self)
        return actor

    # region properties
    @property
    def system(self):
        return self._system

    @property
    def name(self):
        return self._name

    @property
    def props(self):
        return self._props

    @property
    def this(self):
        return self._self_ref

    @property
    def sender(self):
        return self._sender

    @property
    def suspend(self):
        self._resume = asyncio.Future()

    @property
    def resume(self):
        if self._resume:
            self._resume.set_result(True)
    # endregion

    def actor_of(self, props: Props, actor_name=None):
        return self.system.actor_of(props, actor_name)

    @coro
    def deliver(self, envelop: Envelop):
        yield from self._inbox.put(envelop)

    def run(self, loop):
        self.task = loop.create_task(self.start())
        return self

    @coro
    def start(self):
        try:
            self.await_complete = asyncio.Future()
            yield from self._actor.pre_start()
            while True:
                if self._resume:
                    yield from self._resume
                envelop = yield from self._inbox.get()
                yield from self._invoke(envelop)
        except CancelledError:
            logging.info("task successfully cancelled")
        finally:
            # Signal that the loop has finished.
            if not (self.await_complete.cancelled() or self.await_complete.done()):
                self.await_complete.set_result(True)

    # @asyncio.coroutine
    # def _system_message_process(self, message):
    #     if isinstance(message,

    @coro
    def _invoke(self, envelop):
        try:
            if envelop.sender:
                self._sender = envelop.sender
            else:
                self._sender = self.system.dead_letters
            yield from self._actor.receive(envelop.message)
        except CancelledError as e:
            raise e
        except Exception as e:
            self._handle_invoke_failure(e)

    def _handle_invoke_failure(self, e):
        # TODO: need better handling
        # TODO: maybe with decorator support
        logging.exception('Unhandled exception during actor invocation')

    @coro
    def stop(self):
        if self.await_complete and not (
                    self.await_complete.cancelled() or
                    self.await_complete.done()):
            yield from self._actor.post_stop()
            yield from self.await_complete
