.. CherryPicker documentation master file, created by
   sphinx-quickstart on Sun Jul 14 02:01:33 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. role:: python(code)
    :language: python

============
CherryPicker
============

*Flatten complex data.*

:mod:`cherrypicker` aims to make common ETL tasks (filtering data and
restructuring it into flat tables) easier, by taking inspiration from jQuery
and applying it in a Pythonic way to generic data objects.

.. code-block:: bash

    pip install cherrypicker

:mod:`cherrypicker` provides a chainable filter and extraction interface to
allow you to easily pick out objects from complex structures and place them in
a flat table. It fills a similar role to jQuery in JavaScript, enabling you to
navigate complex structures without the need for lots of complex nested for
loops or list comprehensions.

Behold...

.. code-block:: python

    >>> from cherrypicker import CherryPicker
    >>> import json
    >>> with open('climate.json', 'r') as fp:
    ...     data = json.load(fp)
    >>> picker = CherryPicker(data)
    >>> picker['id', 'city'].get()
    [[1, 'Amsterdam'], [2, 'Athens'], [3, 'Atlanta GA'], ...]

This example is equivalent to the list comprehension
:python:`[[item['id'], item['city']] for item in data]`. :mod:`cherrypicker`
really starts to become useful when you combine it with filtering:

.. code-block:: python

    >>> picker(city='B*')['id', 'city'].get()
    [[6, 'Bangkok'], [7, 'Barcelona'], [8, 'Beijing'], ...]

The equivalent list comprehension would be:
:python:`[[item['id'], item['city']] for item in data if item['city'].startswith('B')]`.
As you can see, :class:`CherryPicker` does filtering and extraction with
chained operations rather than list comprehensions. :doc:`Filtering <filter>`
is done with parentheses ``()`` and :doc:`extraction <extract>` is done with
square brackets ``[]``. Chaining can make it easier to build complex
operations:

.. code-block:: python

    >>> picker(city='B*')['info'](
    ...     population=lambda n: n > 2000000,
    ...     area=lambda a: a < 2000
    ... )['area', 'population'].get()
    [[1568, 8300000], [891, 3700000], [203, 2800000]]

Note that the above example searches for a population > 2000000 *and* an area
of < 2000. If you wanted to search for population > 2000000 *or* an area of
< 2000, simply add an extra ``how='any'`` parameter along with your predicates:

.. code-block:: python

    >>> picker(city='B*')['info'](
    ...     population=lambda n: n > 2000000,
    ...     area=lambda a: a < 2000
    ...     how='any'
    ... )['area', 'population'].get()
    [[1568, 8300000], [102, 1615000], [16808, 21540000], ...]

This job is already getting too unwieldy for list comprehensions; to achieve
the example above in another way we may wish to use a for loop:

.. code-block:: python

    table = []
    for item in data:
        if item['city'].startswith('B'):
            info = item['info']
            if info['population'] > 2000000 or info['area'] < 2000:
                table.append(info['area'], info['population'])

Without :mod:`cherrypicker`, the amount of code we need to write increases
pretty rapidly! There are many different types of filtering predicate you can
use with :mod:`cherrypicker`, including exact matches, wildcards, regex and
custom functions. Read all about them in the :doc:`filter` documentation.

Of course, it would be nice if we could extract data in the example above from
both the base level and the ``info`` sub-level of each item and put them into a
flat table, ready to load into your favourite data analysis package. We can do
this in :mod:`cherrypicker` with :meth:`cherrypicker.CherryPickerMapping.flatten`.
Let's say that each item in our data list has a city name and a list of average
low/high temperatures for each month of the year:

.. code-block:: python

    [
        {
            "id": 1,
            "city": "Amsterdam",
            "country": "Netherlands",
            "monthlyAvg": [
                {
                    "high": 7,
                    "low": 3,
                    "dryDays": 19,
                    "snowDays": 4,
                    "rainfall": 68
                },
                {
                    "high": 6,
                    "low": 3,
                    "dryDays": 13,
                    "snowDays": 2,
                    "rainfall": 47
                },
                ...
            ]
        }
    ]

By flattening the data before filtering/extracting, we can get the name and
monthly temperatures alongside each other:

.. code-block:: python

    >>> picker.flatten(
    ...     monthlyAvg_0_high=lambda tmp: tmp > 30
    ... )['city', 'monthlyAvg_0_high'].get()
    [['Bangkok', 33], ['Brasilia', 31], ['Ho Chi Minh City', 33], ...]

.. code-block:: python

    >>> picker.flatten(
    ...     monthlyAvg_0_high=lambda tmp: tmp < 0
    ... )['city', 'monthlyAvg_0_high'].get()
    [['Calgary', -1], ['Montreal', -4], ['Moscow', -4], ...]

One final point to note is that :mod:`cherrypicker` understands data by looking
at its *interfaces* rather than its *types*. This means that it isn't just
limited to JSON data: as long as it can act like a dict or list, you can start
cherrypicking from it!

Parallel Processing
-------------------

As well as making complex queries easier, :class:`CherryPicker` also allows you
to easily use parallel processing to crunch through large datasets quickly:

.. code-block:: python

    >>> picker = CherryPicker(data, n_jobs=4)
    >>> picker(city='B*')['id', 'city'].get()

Everything is the same as before, except you supply an `n_jobs` parameter to
specify the number of CPUs you wish to use (a value of `-1` will mean all CPUs
are used).

Note that for small datasets, you will probably get better performance without
parallel processing, as the benefits of using multiple CPUs will be outweighed
by the overhead of setting up multiple processes. For large datasets with long
lists though, parallel processing can significantly speed up your operations.

* :doc:`filter`
* :doc:`extract`
* :doc:`api`

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Contents

   filter
   extract
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
