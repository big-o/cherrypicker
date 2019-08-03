Cherrypicker
------------

*Flatten complex data.*

``cherrypicker`` aims to make common ETL tasks (filtering data and
restructuring it into flat tables) easier, by taking inspiration from jQuery
and applying it in a Pythonic way to generic data objects.

.. code-block:: bash

    pip install cherrypicker

``cherrypicker`` provides a chainable filter and extraction interface to
allow you to easily pick out objects from complex structures and place them in
a flat table. It fills a similar role to jQuery in JavaScript, enabling you to
navigate complex structures without the need for lots of complex nested for
loops or list comprehensions.

Examples
++++++++

.. code-block:: python

    >>> from cherrypicker import CherryPicker
    >>> import json
    >>> with open('climate.json', 'r') as fp:
    ...     data = json.load(fp)
    >>> picker = CherryPicker(data)

.. code-block:: python

    >>> picker['id', 'city'].get()
    [[1, 'Amsterdam'], [2, 'Athens'], [3, 'Atlanta GA'], ...]

.. code-block:: python

    >>> picker(city='B*')['info'](
    ...     population=lambda n: n > 2000000,
    ...     area=lambda a: a < 2000
    ... )['area', 'population'].get()
    [[1568, 8300000], [891, 3700000], [203, 2800000]]

More complex filtering and flattening of nested structures is possible. Learn
more in the documentation: https://cherrypicker.readthedocs.io.
