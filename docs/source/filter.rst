=========
Filtering
=========

:class:`CherryPicker` objects navigate your data by the following rules:

* If it implements the :class:`collections.abc.Mapping` interface, treat it
  like a :class:`dict`;
* Otherwise if it implements the :class:`collections.abc.Iterable` interface,
  treat it like a :class:`list`;
* Otherwise it is treated as a leaf node (*i.e.* an end point).

You apply filters to your data by providing *predicates* in parentheses after
you have navigated to the data you want, for example:

.. code-block:: python

    >>> picker = CherryPicker(data)
    >>> picker(name='Alice')
    <CherryPickerIterable(list, len=1)>

...applied the predicate ``name='Alice'`` to the root data node. There were
twelve items in the data that matched this filter. To see the actual data that
was extracted, use the :meth:`cherrypicker.CherryPicker.get` method:

.. code-block:: python

    >>> picker(name='Alice').get()
    [{'name': 'Alice', 'age': 20}]

Filters behave slightly differently depending on what type of data you have at
the point you apply them:

* If the data is :class:`dict`-like, each predicate will be applied to the
  value obtained by the key matching the predicate parameter. In the example
  above, the value for the key ``name`` will be checked, and if it is
  ``'Alice'``, the filter has passed and the object will be returned. If the
  filter fails, the default item (which defaults to a leaf containing ``None``)
  is returned instead.

* If the data is :class:`list`-like, the filter will be applied to each child.
  A new :class:`list`-like node will be returned containing only the matching
  items.

Combining predicates
--------------------

Multiple predicates can be applied in a single filter. The *how* parameter
determines the logic used to combine them. If *how* is ``'all'`` (which is the
default), all predicates must match. If *how* is ``'any'``, only one predicate
needs to match for the filter to pass.

Types of predicate
------------------

The value supplied for each predicate term determines the kind of test that is
performed:

* If the predicate is a string, one of the following checks will be done:

  - If *allow_wildcards=True* and the string contains a wildcard character as
    defined by :meth:`fnmatch.fnmatchcase`, then a wildcard match is performed.
  - If *case_sensitive=False*, a case-insensitive string comparison will be
    made.
  - If *regex=True* then the string will be compiled into a regular expression.
    A :meth:`re.fullmatch` test will be performed. If *case_sensitive* is also
    *False*, the regex test will be case-insensitive.
  - Otherwise, only an exact match is accepted.

* If the predicate is a compiled regular expression pattern, a
  :meth:`re.fullmatch` test will be performed.

* If the predicate is a callable function or lambda, the function will be
  applied to the value being tested. This function should take in a single
  parameter (the value) and return something that evaluates to ``True`` or
  ``False``.

API
---

.. automethod:: cherrypicker.CherryPickerTraversable.filter
    :noindex:
