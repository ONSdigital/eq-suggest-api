"""Suggester App test fixtures.

App local `pytest` fixtures.
"""
import mock
import pytest
import json

import app.strategy as strategy


@pytest.fixture
def fake_strategy():

    class FakeStrategy(strategy.Strategy):

        def candidates(self, query):
            return mock.Mock()

    return FakeStrategy


@pytest.fixture
def fake_data_set(tmpdir_factory):
    """Fake suggest api data set.

    Temp-file that contains the 'breakfast' data set.
    """
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
def fake_data_set_data(fake_data_set):
    """Fake suggest api data set data.

    Uses fake_data_set file fixture to generate the data.
    """
    with open(fake_data_set) as f:
        return json.load(f)


@pytest.fixture
def fake_data_set_large(tmpdir_factory):
    """Large fake suggest api data set.

    Temp-file that contains the larger, more complicated, unicode containing
    'territories' data set.
    """
    data_set_content = ["Anguilla", "Antarctica", "Aruba", "Ascension Island",
                        "Bailiwick of Guernsey", "Bailiwick of Jersey",
                        "Baker Island", "Bermuda", "Bonaire", "Bouvet Island",
                        "British Antarctic Territory", "Cayman Islands",
                        "Ceuta", "Collectivity of Saint Martin",
                        "Commonwealth of Puerto Rico",
                        "Commonwealth of the Northern Mariana Islands",
                        "Cook Islands", "Country of Cura\u00e7ao",
                        "Emirate of Abu Dhabi", "Emirate of Ajman",
                        "Emirate of Dubai", "Emirate of Fujairah",
                        "Emirate of Ras al-Khaimah", "Emirate of Sharjah",
                        "Emirate of Umm al-Quwain", "Falkland Islands",
                        "Faroe Islands", "French Guiana", "French Polynesia",
                        "French Southern Territories", "Gibraltar", "Greenland",
                        "Guadeloupe", "Hong Kong Special Administrative Region",
                        "Howland Island", "Isle of Man", "Jarvis Island",
                        "Johnston Atoll", "Kingman Reef",
                        "Macao Special Administrative Region", "Martinique",
                        "Mayotte", "Melilla", "Midway Islands", "Montserrat",
                        "Navassa Island", "New Caledonia", "Niue",
                        "Palmyra Atoll",
                        "Pitcairn, Henderson, Ducie and Oeno Islands",
                        "R\u00e9union", "Saba", "Saint Barth\u00e9lemy",
                        "Saint Helena", "Saint Pierre and Miquelon",
                        "Sint Eustatius", "Sint Maarten",
                        "South Georgia and the South Sandwich Islands",
                        "Sovereign Base Areas of Akrotiri and Dhekelia",
                        "Svalbard and Jan Mayen", "Taiwan",
                        "Territory of American Samoa",
                        "Territory of Christmas Island", "Territory of Guam",
                        "Territory of Heard Island and McDonald Islands",
                        "Territory of Norfolk Island",
                        "Territory of the Cocos (Keeling) Islands",
                        "Territory of the Wallis and Futuna Islands",
                        "The British Indian Ocean Territory",
                        "The Occupied Palestinian Territories",
                        "The Virgin Islands", "Tokelau", "Tristan da Cunha",
                        "Turks and Caicos Islands",
                        "Virgin Islands of the United States", "Wake Island",
                        "Western Sahara", "\u00c5land Islands"]
    ds = tmpdir_factory.mktemp('data').join('dataset.json')
    ds.write('making sure file is created')
    with open(str(ds), 'w') as f:
        json.dump(data_set_content, f)
    return ds


@pytest.fixture
def fake_data_set_too_many_chiefs(tmpdir_factory):
    """Large fake suggest api data set.

    Temp-file that contains a data set with items that will be similarly
    ranked.
    """
    data_set_content = ["Chief executive", "Chief executive (advertising)",
                        "Chief executive (agricultural research)",
                        "Chief executive (building society)",
                        "Chief executive (charitable organisation)",
                        "Chief executive (computer software development)",
                        "Chief executive (health authority: hospital service)",
                        "Chief executive (hospital)",
                        "Chief executive (housing association)",
                        "Chief executive (insurance)",
                        "Chief executive (IT recruitment)",
                        "Chief executive (local government)",
                        "Chief executive (management consulting)",
                        "Chief executive (National Assembly for Wales)",
                        "Chief executive (property development)",
                        "Chief executive (rural community council)",
                        "Chief executive (supermarket chain)",
                        "Chief executive (theatre production)",
                        "Chief executive (trade association)",
                        "Chief executive officer",
                        "Chief executive officer (government)",
                        "Chief executive officer (PO)"]
    ds = tmpdir_factory.mktemp('data').join('dataset.json')
    ds.write('making sure file is created')
    with open(str(ds), 'w') as f:
        json.dump(data_set_content, f)
    return ds


@pytest.fixture
def fake_data_set_invalid(tmpdir_factory):
    """Invalid fake suggest api data set.

    Temp-file that contains non-json data.
    """
    data_set_content = "I am really not json"
    ds = tmpdir_factory.mktemp('data').join('invalid_dataset.json')
    ds.write(data_set_content)
    return ds
