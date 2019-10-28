from cherrypicker import CherryPicker
from cherrypicker.exceptions import *
import json
import os
import pytest
import re


def abs_path(path):
    return os.path.join(os.path.dirname(__file__), path)


n_jobs = [None, 1, 2, -1]


def test_mappable():
    with pytest.raises(ValueError):
        run_map_tests(0)

    for n in n_jobs:
        run_map_tests(n)


def run_map_tests(n_jobs=None):
    data = json.load(open(abs_path("data/climate.json")))
    first = data[0]

    picker = CherryPicker(first, n_jobs=n_jobs, on_error="raise")
    assert not picker.is_leaf
    assert picker["id"].is_leaf

    keys = list(first.keys())
    vals = list(first.values())
    items = list(first.items())
    assert all([k in keys for k in picker.keys()])
    assert all([v in vals for v in picker.values()])
    assert all([i in items for i in picker.items()])

    assert picker(city=first["city"]).get() == first
    assert picker(city=123).get() == None
    assert picker["id"].get() == first["id"]
    assert picker["city", "id"].get() == [first["city"], first["id"]]
    assert tuple(picker["city", "id"]) == (first["city"], first["id"])

    picker = CherryPicker(first, n_jobs=n_jobs, on_missing="raise")
    assert picker["id"].get() == first["id"]
    assert picker["city", "id"].get() == [first["city"], first["id"]]


def test_flatten():
    for n in n_jobs:
        run_flatten_tests(n)


def run_flatten_tests(n_jobs=None):
    data = json.load(open(abs_path("data/climate.json")))
    first = data[0]

    flat_keys = ["id", "city", "country"]

    for month in range(12):
        flat_keys.append("monthlyAvg_{}_high".format(month))
        flat_keys.append("monthlyAvg_{}_low".format(month))
        flat_keys.append("monthlyAvg_{}_dryDays".format(month))
        flat_keys.append("monthlyAvg_{}_snowDays".format(month))
        flat_keys.append("monthlyAvg_{}_rainfall".format(month))

    fpicker = CherryPicker(first, n_jobs=n_jobs)
    picker = CherryPicker(data, n_jobs=n_jobs)
    assert list(fpicker.flatten.keys()) == flat_keys
    assert list(fpicker.flatten().keys()) == flat_keys

    assert list(picker.flatten[0].keys()) == flat_keys
    assert list(picker.flatten()[0].keys()) == flat_keys


def test_iterable():
    with pytest.raises(ValueError):
        run_iter_tests(0)

    for n in n_jobs:
        run_iter_tests(n)


def run_iter_tests(n_jobs=None):
    data = json.load(open(abs_path("data/climate.json")))
    picker = CherryPicker(data, n_jobs=n_jobs, on_error="raise")

    assert not picker.is_leaf
    assert sorted(picker.keys()) == ["city", "country", "id", "monthlyAvg"]

    assert picker(country="Russia")["id"].get() == [53, 74]
    assert picker(country="Russia").id.get() == [53, 74]
    with pytest.raises(AttributeError):
        picker(country="Russia").notanattr
        picker(country="Russia")[0].notanattr
        picker(country="Russia")[0]["id"].notanattr
    assert picker(country="Russia")[0]["id"].get() == 53
    assert picker(country="Russia", id=53)[0]["id"].get() == 53
    assert picker(country="Russia", id=53, how="any")[0]["id"].get() == 53

    russian = [["Moscow", 53], ["Saint Petersburg", 74]]
    assert picker(country="Russia")["city", "id"].get() == russian
    assert list(picker(country="Russia")["city", "id"]) == russian

    # Propagation hack
    data = [
        dict([(int(k), v) for k, v in d.items()])
        for d in json.load(open(abs_path("data/numbers.json")))
    ]
    picker = CherryPicker(data, n_jobs=n_jobs, on_missing="ignore")

    assert picker[0].get() == data[0]
    assert picker[0, False].get() == data[0]
    assert picker[0:2].get() == data[0:2]
    assert picker[0, True].get() == [data[0][0], None]

    picker = CherryPicker(data, n_jobs=n_jobs, on_missing="raise")
    with pytest.raises(IndexError):
        picker[len(data)]


def test_predicates_callable():
    data = json.load(open(abs_path("data/climate.json")))
    picker = CherryPicker(data, on_error="raise")

    big_ids = [
        ["Albuquerque NM", 101],
        ["Vermont IL", 102],
        ["Nashville TE", 103],
        ["St. Louis MO", 104],
        ["Minneapolis MN", 105],
    ]
    assert picker(id=lambda i: i > 100)["city", "id"].get() == big_ids
    assert list(picker(id=lambda i: i > 100)["city", "id"]) == big_ids
    assert list(picker(id=lambda i: i > 100)[:-2]["city", "id"]) == big_ids[:-2]
    assert list(picker(id=lambda i: i > 100)["city", "id"][:-2]) == big_ids[:-2]


def test_predicates_string():
    data = json.load(open(abs_path("data/climate.json")))
    picker = CherryPicker(data, on_error="raise")

    assert picker(city="Amsterdam")["city"].get() == ["Amsterdam"]
    assert picker(city="Amsterdam")[0]["city"].get() == "Amsterdam"
    assert picker(city="Amsterdam")["city"][0].get() == "Amsterdam"

    a_cities = [
        "Amsterdam",
        "Athens",
        "Atlanta GA",
        "Auckland",
        "Austin TX",
        "Albuquerque NM",
    ]

    assert picker(city="A*")["city"].get() == a_cities
    assert picker(city="A*", allow_wildcards=False)["city"].get() == []
    assert picker(city="A*D")["city"].get() == []
    assert picker(city="A*D", case_sensitive=False)["city"].get() == ["Auckland"]
    assert picker(city="A*d")["city"].get() == ["Auckland"]
    assert picker(city="Auckland", allow_wildcards=False)["city"].get() == ["Auckland"]
    assert picker(city="A*d", allow_wildcards=False)["city"].get() == []

    assert picker(city="A.*")["city"].get() == []
    assert picker(city="A.*", regex=True)["city"].get() == a_cities
    assert picker(city=re.compile(r"A.*"))["city"].get() == a_cities
    assert picker(city=re.compile(r"A.*D"))["city"].get() == []
    assert picker(city=re.compile(r"A.*D"), case_sensitive=False)["city"].get() == []
    assert picker(city=re.compile(r"A.*D", re.I))["city"].get() == ["Auckland"]


def test_misc():
    data = json.load(open(abs_path("data/climate.json")))
    picker = CherryPicker(data, on_error="raise", on_missing="raise")

    mappable = picker[0]
    iterable = picker[:1]
    leaf = mappable["id"]

    # Test no errors get raised here.
    repr(mappable)
    repr(mappable)
    repr(iterable)
    repr(iterable)
    repr(leaf)
    repr(leaf)

    with pytest.raises(ValueError):
        picker(city="A*", how=None)

    with pytest.raises(AttributeError):
        picker(notanode=123)

    with pytest.raises(type(re.error(""))):
        picker(city="(abc", regex=True)

    def err(x):
        raise ValueError()

    with pytest.raises(ValueError):
        picker(city=err)

    picker = CherryPicker(data, on_error="ignore", on_missing="ignore")
    # Invalid regex always raises.
    with pytest.raises(type(re.error(""))):
        picker(city="(abc", regex=True)

    # Comparisons that raise evaluate to false by default.
    assert picker(city=err).get() == []

    picker = CherryPicker(data, on_error="raise", on_missing="ignore")
    assert picker(notanode=123).get() == []


def test_leaf():
    data = json.load(open(abs_path("data/climate.json")))
    picker = CherryPicker(data, on_error="raise", on_missing="raise")
    leaf = picker[0]["city"]

    assert leaf.get() == data[0]["city"]
    with pytest.raises(LeafError):
        assert leaf["city"]

    picker = CherryPicker(data, on_leaf="ignore")
    leaf = picker[0]["city"]

    assert leaf[0] == data[0]["city"][0]

    assert not picker[0].is_leaf

    picker = CherryPicker(data, leaf_types=(dict,))
    assert picker[0].is_leaf
    picker = CherryPicker(data, leaf_types=dict)
    assert picker[0].is_leaf

    picker = CherryPicker(data, leaf_types=(lambda lf: "city" in lf,))
    assert picker[0].is_leaf
    picker = CherryPicker(data, leaf_types=lambda lf: "city" in lf)
    assert picker[0].is_leaf

    with pytest.raises(ValueError):
        picker = CherryPicker(data, leaf_types=(0,))
    with pytest.raises(ValueError):
        picker = CherryPicker(data, leaf_types=0)

    def argh(x):
        raise Exception()

    # Errors in leaf functions should be silently resolved to false.
    picker = CherryPicker(data, leaf_types=(str, bytes, argh))
    assert not picker[0].is_leaf

    picker = CherryPicker(data, leaf_types=None)
    assert not picker[0]["city"].is_leaf


def test_parents():
    data = json.load(open(abs_path("data/climate.json")))
    picker = CherryPicker(data)

    with pytest.raises(AttributeError):
        picker.parent()

    with pytest.raises(AttributeError):
        picker.parents()

    assert picker[0].parent() == picker
    assert picker[0].parent() == picker[0].parents()

    assert picker["monthlyAvg"][0].parents().get() == picker["monthlyAvg"].get()
    assert picker["monthlyAvg"][0, True].parents().get() == picker["monthlyAvg"].get()
    assert picker[0]["monthlyAvg"].parent()["city"].get() == picker[0]["city"].get()
