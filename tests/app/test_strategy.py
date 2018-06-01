import mock
import os
import pickle
import pytest

import app.strategy as strategy


def test_strategy_base():

    class MyStrategy(strategy.Strategy):
        pass

    s = MyStrategy('/foo/bar', 'my_strat')
    assert s.data_file == '/foo/bar'
    assert s.strategy_name == 'my_strat'
    with pytest.raises(NotImplementedError):
        s.build_index()
    with pytest.raises(NotImplementedError):
        s.candidates('foo')


def test_strategy_instance(monkeypatch, fake_strategy):
    fake_index = [1, 2, 3]
    mock_load = mock.Mock(return_value=fake_index)
    mock_store = mock.Mock(return_value=None)
    monkeypatch.setattr(strategy.Strategy, 'load_index', mock_load)
    monkeypatch.setattr(strategy.Strategy, 'store_index', mock_store)
    s = fake_strategy('data_set', 'strat')
    idx = s.init()
    assert idx == fake_index
    fake_strategy.load_index.assert_called_with('index/data_set_strat.idx')
    assert fake_strategy.store_index.called is False


def test_strategy_instance_build(monkeypatch, fake_strategy, fake_data_set):
    fake_index = [1, 2, 3, 4]
    mock_load = mock.Mock(return_value=None)
    mock_store = mock.Mock(return_value=None)
    mock_build = mock.Mock(return_value=fake_index)
    monkeypatch.setattr(strategy.Strategy, 'load_index', mock_load)
    monkeypatch.setattr(strategy.Strategy, 'store_index', mock_store)
    monkeypatch.setattr(strategy.Strategy, 'build_index', mock_build)
    s = fake_strategy('data_set', 'strat')
    idx = s.init()
    assert idx == fake_index
    fake_strategy.load_index.assert_called_with('index/data_set_strat.idx')
    fake_strategy.store_index.assert_called_with('index/data_set_strat.idx',
                                                 fake_index)


def test_index_name(tmpdir_factory):
    loc = tmpdir_factory.mktemp('my_index_location')
    strategy.INDEX_LOCATION = str(loc)
    idx_path = strategy.Strategy.index_name('data_set', 'strat')
    assert idx_path == strategy.INDEX_LOCATION + '/data_set_strat.idx'


def test_index_name_dir_creation(tmpdir_factory):
    loc = tmpdir_factory.mktemp('root_location')
    strategy.INDEX_LOCATION = os.path.join(str(loc), 'index')
    idx_path = strategy.Strategy.index_name('data_set', 'strat')
    assert os.path.exists(strategy.INDEX_LOCATION)
    assert idx_path == strategy.INDEX_LOCATION + '/data_set_strat.idx'


def test_load_no_index():
    assert strategy.Strategy.load_index('foo') is None


def test_load_bad_index(tmpdir_factory):
    index_file = tmpdir_factory.mktemp('index').join('bad.idx')
    index_file.write('not a pickle file')
    with pytest.raises(strategy.StrategyError):
        strategy.Strategy.load_index(str(index_file))


def test_load_stored_index(tmpdir_factory):
    index = [1, 2, 3]
    index_file = tmpdir_factory.mktemp('index').join('lovely.idx')
    strategy.Strategy.store_index(str(index_file), index)
    assert strategy.Strategy.load_index(str(index_file)) == index


def test_store_index_raises(monkeypatch):
    monkeypatch.setattr(pickle, 'dump', mock.Mock(side_effect=RuntimeError))
    with mock.patch(
            'builtins.open', mock.mock_open(read_data='foo')) as mock_file:
        with pytest.raises(strategy.StrategyError):
            strategy.Strategy.store_index('idx_file', [1, 2, 3])
        mock_file.assert_called_with('idx_file', 'wb')
