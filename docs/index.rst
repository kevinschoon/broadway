Broadway -  A Python Implementation of The Actor Model
======================================================

Broadway is a Python implementation of the `actor model <https://en.wikipedia.org/wiki/Actor_model>`_ programming paradigm,
and is implemented with Python 3.4's `Asyncio <https://docs.python.org/3/library/asyncio.html>`_, Broadway is also
heavily inspired by the Scala framework `Akka <http://akka.io/>`_.

Hello World
-----------

.. literalinclude:: ../examples/hello_world.py

.. code-block:: bash

    $ python examples/hello_world.py
    hello world (1)
    hello world (2)
    hello world (3)
    hello world (4)
    hello world (5)


User Guide
==========

.. toctree::
    :maxdepth: 2

    guide/concepts
    guide/examples
    guide/install


API Documentation
=================

.. toctree::
    :maxdepth: 4

    api/broadway

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`