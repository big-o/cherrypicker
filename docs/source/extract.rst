.. role:: python(code)
    :language: python


==========
Extraction
==========

When you have navigated to the data node(s) you care about, you can extract
data from them into flat tables. These tables will always contain the values
you have requested in a :class:`list` or nested lists. Lists are used to
improve compatability with :mod:`pandas` and :mod:`numpy`.

Much like :doc:`filtering <filter>`, extraction differs depending on the
type of data node you are operating on:

* If the data is :class:`dict`-like, values will be extracted from all the keys
  provided into a flat list.

* If the data is :class:`list`-like, data extraction will be delegated to each
  item in the collection, and the results returned in another list.

Data is extracted with the square brackets (``[]``) operator. When you extract
data, the results are wrapped up in another :class:`CherryPicker` object (this
is to enable the chaining of operations). At any stage in your cherry picking,
you can get down to the raw data with the :meth:`CherryPicker.get()` operator:

.. code-block:: python

    >>> picker = CherryPicker(data)
    >>> picker[0]['id', 'city']
    <CherryPickerIterable(list, len=2)>
    >>> picker[0]['id', 'city'].get()
    [1, 'Amsterdam']

Note that you can also extract data as an attribute for convenience:

.. code-block:: python

    >>> picker = CherryPicker(data)
    >>> picker.id.get()
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...]
    >>> picker[0].id.get()
    1

Navigating lists
----------------

Lists (or any :class:`list`-like object) is a little more complicated than it
first seems. What if you want to get the first item of a list? Well that's
easy:

.. code-block:: python

    >>> picker = CherryPicker(mylist)
    >>> picker
    <CherryPickerIterable(list, len=105)>
    >>> picker[0]
    <CherryPickerMapping(dict)>

It's just like working with a normal list. Just provide the index of the item
you want and your cherry picker will get it for you. Slices are also accepted
if you want multiple items. If you want to drill down and extract items from
each item in the list, that's also easy enough:

.. code-block:: python

    >>> picker['city']
    <CherryPickerIterable(list, len=105)>

You can see here that this time the cherry picker has given you a list of
results. That's because it's extracted the *city* from each item in the list.
Cherry pickers are usually smart enough to know when you want to grab something
from the list itself vs. grab something from the items in the list.

But what if ``mylist`` was actually a list of lists, and you actually wanted
to get the first item of each list? Things aren't as clear now, because your
picker will assume that :python:`picker[0]` means grab the entire first item
only. In this case, you must give your picker an extra hint. For
:class:`list`-like objects, if you provide an :class:`int` or
:class:`slice`-like parameter, you can also provide an optional second boolean
parameter known as the *propagate* flag. If this flag is set to True, the
picker will apply the index to each child node, regardless of what type it is:

.. code-block:: python

    >>> mynestedlist = [['Alice', 20], ['Bob', 34], ...]
    >>> picker = CherryPicker(mynestedlist)
    >>> picker[0].get()
    ['Alice', 20]
    >>> picker[0, True].get()
    ['Alice', 'Bob', ...]

In the first command, the first item in the list (another list of length 2) is
obtained. In the second command, the *propagate* flag is set, so we instead
grab the first item of each child instead.
