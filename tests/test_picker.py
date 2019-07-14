from cherrypicker import CherryPicker
import json
import os
import pytest
import re


def abs_path(path):
    return os.path.join(os.path.dirname(__file__), path)


def test_mappable():
    data = json.load(open(abs_path('data/climate.json')))
    first = data[0]

    picker = CherryPicker(first, on_error='raise')
    assert not picker.is_leaf
    assert picker['id'].is_leaf

    keys = list(first.keys())
    vals = list(first.values())
    items = list(first.items())
    assert all([k in keys for k in picker.keys()])
    assert all([v in vals for v in picker.values()])
    assert all([i in items for i in picker.items()])

    assert picker(city=first['city']).get() == first
    assert picker(city=123).get() == None
    assert picker['id'].get() == first['id']
    assert picker['city', 'id'].get() == [first['city'], first['id']]
    assert tuple(picker['city', 'id']) == (first['city'], first['id'])


def test_iterable():
    data = json.load(open(abs_path('data/climate.json')))
    picker = CherryPicker(data, on_error='raise')

    assert not picker.is_leaf
    assert sorted(picker.keys()) == ['city', 'country', 'id', 'monthlyAvg']

    assert picker(country='Russia')['id'].get() == [53, 74]
    assert picker(country='Russia')[0]['id'].get() == 53
    assert picker(country='Russia', id=53)[0]['id'].get() == 53
    assert picker(country='Russia', id=53, how='any')[0]['id'].get() == 53

    russian = [['Moscow', 53], ['Saint Petersburg', 74]]
    assert picker(country='Russia')['city', 'id'].get() == russian
    assert list(picker(country='Russia')['city', 'id']) == russian

    # Propagation hack
    data = [dict([(int(k), v) for k, v in d.items()])
            for d in json.load(open(abs_path('data/numbers.json')))]
    picker = CherryPicker(data, on_error='raise')

    assert picker[0].get() == data[0]
    assert picker[0, True].get() == [data[0][0], None]


def test_predicates_callable():
    data = json.load(open(abs_path('data/climate.json')))
    picker = CherryPicker(data, on_error='raise')

    big_ids = [
        ['Albuquerque NM', 101],
        ['Vermont IL', 102],
        ['Nashville TE', 103],
        ['St. Louis MO', 104],
        ['Minneapolis MN', 105]
    ]
    assert picker(id=lambda i: i > 100)['city', 'id'].get() == big_ids
    assert list(picker(id=lambda i: i > 100)['city', 'id']) == big_ids
    assert list(picker(id=lambda i: i > 100)[:-2]['city', 'id']) == big_ids[:-2]
    assert list(picker(id=lambda i: i > 100)['city', 'id'][:-2]) == big_ids[:-2]


def test_predicates_string():
    data = json.load(open(abs_path('data/climate.json')))
    picker = CherryPicker(data, on_error='raise')

    assert picker(city='Amsterdam')['city'].get() == ['Amsterdam']
    assert picker(city='Amsterdam')[0]['city'].get() == 'Amsterdam'
    assert picker(city='Amsterdam')['city'][0].get() == 'Amsterdam'

    a_cities = [
        'Amsterdam',
        'Athens',
        'Atlanta GA',
        'Auckland',
        'Austin TX',
        'Albuquerque NM'
    ]

    assert picker(city='A*')['city'].get() == a_cities
    assert picker(city='A*', allow_wildcards=False)['city'].get() == []
    assert picker(city='A*D')['city'].get() == []
    assert picker(city='A*D',
                  case_sensitive=False)['city'].get() == ['Auckland']
    assert picker(city='A*d')['city'].get() == ['Auckland']
    assert picker(city='Auckland',
                  allow_wildcards=False)['city'].get() == ['Auckland']
    assert picker(city='A*d', allow_wildcards=False)['city'].get() == []

    assert picker(city='A.*')['city'].get() == []
    assert picker(city='A.*', regex=True)['city'].get() == a_cities
    assert picker(city=re.compile(r'A.*'))['city'].get() == a_cities
    assert picker(city=re.compile(r'A.*D'))['city'].get() == []
    assert picker(city=re.compile(r'A.*D'),
                  case_sensitive=False)['city'].get() == []
    assert picker(city=re.compile(r'A.*D', re.I))['city'].get() == ['Auckland']


def test_misc():
    data = json.load(open(abs_path('data/climate.json')))
    picker = CherryPicker(data, on_error='raise', on_missing='raise')

    mappable = picker[0]
    iterable = picker[:1]
    leaf = mappable['id']

    # Test no errors get raised here.
    repr(mappable)
    repr(mappable)
    repr(iterable)
    repr(iterable)
    repr(leaf)
    repr(leaf)

    with pytest.raises(ValueError):
        picker(city='A*', how=None)

    with pytest.raises(AttributeError):
        picker(notanode=123)

    with pytest.raises(type(re.error(''))):
        picker(city='(abc', regex=True)

    def err(x):
        raise ValueError()

    with pytest.raises(ValueError):
        picker(city=err)

    picker = CherryPicker(data, on_error='ignore', on_missing='ignore')
    # Invalid regex always raises.
    with pytest.raises(type(re.error(''))):
        picker(city='(abc', regex=True)

    # Comparisons that raise evaluate to false by default.
    assert picker(city=err).get() == []

    picker = CherryPicker(data, on_error='raise', on_missing='ignore')
    assert picker(notanode=123).get() == []
