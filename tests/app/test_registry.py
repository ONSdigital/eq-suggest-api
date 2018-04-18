from mock import Mock

import app.registry


def test_get_data_sets(monkeypatch):
    mock_glob = Mock(return_value=['data/schema1.json', 'data/schema2.json'])
    monkeypatch.setattr(app.registry.glob, 'glob', mock_glob)

    def fake_summary(path):
        return {'source': path}

    monkeypatch.setattr(app.registry, '_summary', fake_summary)
    data_sets = app.registry.get_data_sets()
    assert len(data_sets) == 2
    assert 'schema1' in data_sets
    assert 'schema2' in data_sets


def test_get_data_set_content(fake_data_set):
    ds = app.registry.get_data_set_content(fake_data_set)
    assert isinstance(ds, list)
    assert len(ds) == 20
    assert {'Bacon', 'Eggs', 'Baked Beans'}.issubset(set(ds))


def test_get_data_set_content_invalid(fake_data_set_invalid, loghandler):
    ds = app.registry.get_data_set_content(fake_data_set_invalid)
    assert isinstance(ds, list)
    assert not ds
    records = [r for r in loghandler.records]
    expected = f'Failed to get data set content for {fake_data_set_invalid}'
    assert records[0].level_name == 'ERROR'
    assert expected in records[0].message


def test_summary(fake_data_set):
    summary = app.registry._summary(fake_data_set)
    assert summary['source'] == fake_data_set
    assert summary['item_count'] == 20


def test_summary_non_existent():
    summary = app.registry._summary('foo/bar')
    assert summary['source'] == 'foo/bar'
    assert summary['error'] == 'Invalid path, cannot status data'


def test_summary_invalid(fake_data_set_invalid, loghandler):
    summary = app.registry._summary(fake_data_set_invalid)
    assert summary['source'] == fake_data_set_invalid
    assert summary['item_count'] == 0
    records = [r for r in loghandler.records]
    expected = (f'Failed to determine number of data set items for '
                f'{fake_data_set_invalid}')
    assert records[0].level_name == 'ERROR'
    assert expected in records[0].message
