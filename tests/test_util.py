from cherrypicker.util import *

import pytest


def test_orderedset():
    l = list(range(10))
    os = OrderedSet()
    repr(os)

    for i in l:
        os.add(i)
    repr(os)

    os2 = OrderedSet(l)
    assert os == l
    assert os == os2

    assert sorted(os) == sorted(l)
    assert list(reversed(os)) == list(reversed(l))
    assert len(os) == len(set(l))

    for i in l:
        assert i in os

    for i in l:
        os.add(i)
    assert sorted(os) == sorted(set(l))

    assert os.pop() == l[-1]
    assert sorted(os) == l[:-1]
    assert os != l

    for _ in range(len(os)):
        os.pop()

    with pytest.raises(KeyError):
        os.pop()

    assert 1 not in os

    os3 = OrderedSet(l)
    assert os3 == l

    os4 = OrderedSet(os2)
    assert os2 == os4

    d1 = {0: 1}
    d2 = {0: 1}

    os5 = OrderedSet(key=id)
    os5.add(d1)
    os5.add(d1)
    os5.add(d2)
    os5.add(d2)

    assert len(os5) == 2
