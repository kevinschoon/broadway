import logging
import asyncio
from asyncio import coroutine
from concurrent.futures import CancelledError
from broadway.message import Envelop
from broadway.actor import Actor
from broadway.actorref import ActorRefFactory, ActorRef, Props


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
        self._inbox = mailbox

        self.await_complete = None
        self.receive_timeout = None
        self.task = None
        self._resume = None
        self._sender = None

        self._self_ref = ActorRef(name, self)
        # TODO: need better actor supervision
        self._actor = self.new_actor()

    def new_actor(self):
        actor_class = self._props.actor_class
        args = self._props.args
        kwargs = self._props.kwargs
        if not issubclass(actor_class, Actor):
            raise TypeError("class in the proper is not instance of Actor")
        self.wrap_init_with_context(actor_class)
        actor = actor_class(*args, **kwargs)  #.with_context(self)
        return actor


    def wrap_init_with_context(self, actor_class):
        actor_base_class = actor_class
        context = self
        original_init = actor_base_class.__init__

        def init_wrapper(_self, *args, **kwargs):
            _self.context = context
            original_init(_self, *args, **kwargs)
        actor_base_class.__init__ = init_wrapper

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

    @coroutine
    def deliver(self, envelop: Envelop):
        yield from self._inbox.put(envelop)

    def run(self, loop):
        self.task = loop.create_task(self.start())
        return self

    @coroutine
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

    @coroutine
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

    @coroutine
    def stop(self):
        if self.await_complete and not (
                    self.await_complete.cancelled() or
                    self.await_complete.done()):
            yield from self._actor.post_stop()
            yield from self.await_complete
