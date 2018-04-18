"""Suggester App test fixtures.

App local `pytest` fixtures.
"""
import pytest
import json


@pytest.fixture
def fake_data_set(tmpdir_factory):
    data_set_content = [
        "Bacon", "Eggs", "Beans", "Sausage", "Veggie Sausage", "Orange Juice",
        "Tomato Juice", "Milk", "Baked Beans", "Black Sausage", "Mushrooms",
        "Shitaki Mushrooms", "Fried Bread", "Fried Eggs", "Scrambled Eggs",
        "Poached Eggs", "Omelette", "Toast", "Raisin Toast", "Croissant"
    ]
    ds = tmpdir_factory.mktemp('data').join('dataset.json')
    ds.write('making sure file is created')
    with open(str(ds), 'w') as f:
        json.dump(data_set_content, f)
    return ds


@pytest.fixture
def fake_data_set_invalid(tmpdir_factory):
    data_set_content = "I am really not json"
    ds = tmpdir_factory.mktemp('data').join('invalid_dataset.json')
    ds.write(data_set_content)
    return ds
