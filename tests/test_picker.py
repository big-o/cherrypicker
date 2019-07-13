from cherrypicker import CherryPicker
import json
import os


def abs_path(path):
    return os.path.join(os.path.dirname(__file__), path)

def test_mappable():
    data = json.load(open(abs_path('data/climate.json')))
    first = data[0]

    picker = CherryPicker(first)
    assert picker['id'].get() == first['id']
    assert picker['city', 'id'].get() == [first['city'], first['id']]
    assert tuple(picker['city', 'id']) == (first['city'], first['id'])


def test_iterable():
    data = json.load(open(abs_path('data/climate.json')))
    picker = CherryPicker(data)

    assert picker(country='Russia')['id'].get() == [53, 74]
    assert picker(country='Russia')[0]['id'].get() == 53

    russian = [['Moscow', 53], ['Saint Petersburg', 74]]
    assert picker(country='Russia')['city', 'id'].get() == russian
    assert list(picker(country='Russia')['city', 'id']) == russian

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
