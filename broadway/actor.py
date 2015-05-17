import asyncio
from asyncio.tasks import Task
from concurrent.futures import CancelledError
import inspect
import logging
import sys
import time
from broadway.exception import ActorCreationFailureException
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
        try:
            if not sender:
                sender = caller()
            yield from self._deliver(Envelop(sender, message, time.time()))
        except AttributeError as e:
            print('Target does not have a _deliver method. Is it an actor?')
            raise

    @asyncio.coroutine
    def ask(self, message: 'Any') -> asyncio.Future:
        promise_actor = self.context.actor_of(PromiseActor)
        yield from self.tell(message, sender=promise_actor)
        return promise_actor.result

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
            self.await_complete.set_result(True)

    # @asyncio.coroutine
    # def _system_message_process(self, message):
    #     if isinstance(message,

    @asyncio.coroutine
    def _invoke(self, envelop):
        try:
            self.context.sender = envelop.sender
            yield from self.receive(envelop.message)
        except Exception as e:
            self._handle_invoke_failure(e)

    def _handle_invoke_failure(self, e):
        # TODO: might need better handling
        logging.error('{0}'.format(e))

    @asyncio.coroutine
    def stop(self):
        if self.await_complete and not (
                    self.await_complete.cancelled() or
                    self.await_complete.done()):
            yield from self.post_stop()
            yield from self.await_complete

    @asyncio.coroutine
    def post_stop(self):
        pass


class PromiseActor(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = asyncio.Future()

    @asyncio.coroutine
    def receive(self, message):
        self.result.set_result(message)
        yield from self.stop()


class DeadLetterActor(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = asyncio.Future()

    @asyncio.coroutine
    def receive(self, message):
        # TODO: we need to block mailbox
        pass


class ActorRefFactory():
    def actor_of(self, actor_class, actor_name=None, *args, **kwargs):
        raise NotImplementedError()


class ActorContext(ActorRefFactory):
    def __init__(self, system):
        super().__init__()
        self.system = system
        self.this = None
        self.sender = None
        self.receive_timeout = None

    def actor_of(self, actor_class, actor_name=None, *args, **kwargs):
        return self.system.actor_of(actor_class, actor_name, *args, **kwargs)


# TODO: eventually want to have actorRef expose instead of actor itself
class ActorRef():
    def __init__(self, name, actor, task):
        self.name = name
        self.actor = actor
        self.task = task


class ActorSystem():
    def __init__(self, loop=None):
        self._loop = loop if loop else asyncio.get_event_loop()
        self._registry = {}
        self._terminated = None
        self._other_tasks = set()
        self.settings = {}  # TODO: settings
        self.startTime = time.time() * 1000
        # TODO: address / actor hierarchy

    @property
    def uptime(self):
        return time.time() - self.startTime/1000

    def actor_of(self, actor_class, actor_name=None, *args, **kwargs):
        if not actor_name:
            actor_name = actor_class.__name__
            count = 0
            while actor_name in self._registry:
                actor_name = "{0}${1}".format(actor_class.__name__, count)
        elif actor_name in self._registry:
            raise ActorCreationFailureException("actor_name already exists")
        kwargs['loop'] = self._loop
        kwargs['context'] = ActorContext(self)
        actor = actor_class(*args, **kwargs)
        running_task = self._loop.create_task(actor.start())
        self._registry[actor_name] = ActorRef(actor_name, actor, running_task)
        # TODO: eventually want to have actorRef expose instead of actor itself
        return actor

    @asyncio.coroutine
    def stop(self):
        if self._terminated:
            self._terminated.set_result(True)
        else:
            raise Exception("system has never started")

    @asyncio.coroutine
    def _start(self):
        self._terminated = asyncio.Future()
        yield from self._terminated

    @asyncio.coroutine
    def cancel_all(self):
        futures = list(self._other_tasks)
        for task in futures:
            task.cancel()
        for actor_ref in self._registry.values():
            futures.append(actor_ref.task)
            actor_ref.task.cancel()

        yield from asyncio.wait(futures)

    def run_until_stop(self, coros, exit_after=False):
        try:
            for c in coros:
                task = self._loop.create_task(c)
                self._other_tasks.add(task)
            self._loop.run_until_complete(self._start())
            if exit_after:
                self._loop.run_until_complete(self.cancel_all())
                self._loop.stop()
                self._loop.close()
                sys.exit(0)
        except Exception as e:
            logging.error(e)
            self._loop.stop()
            self._loop.close()
            sys.exit(1)

