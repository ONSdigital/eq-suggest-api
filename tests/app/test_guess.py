import mock
import pytest

import collections

import app.strategy as strategy
from app.guess import Guess, PhraseLookup


def test_guess():
    g = Guess('/foo/bar')
    assert g.data_file == '/foo/bar'
    assert g.max_matches == 10
    assert isinstance(g.token_to_item, collections.defaultdict)
    assert not len(g.token_to_item)
    assert isinstance(g.n_gram_to_tokens, collections.defaultdict)
    assert not len(g.n_gram_to_tokens)
    assert g.lookup is None


def test_guess_max():
    g = Guess('/foo/bar', max_matches=99)
    assert g.max_matches == 99


def test_guess_init(monkeypatch, fake_data_set):
    fake_lookup = PhraseLookup()
    fake_index = {'n_gram_to_tokens': [1, 2, 3],
                  'token_to_item': [4, 5, 6],
                  'lookup': fake_lookup}
    fake_build_index = mock.Mock(return_value=fake_index)
    monkeypatch.setattr(Guess, 'build_index', fake_build_index)
    g = Guess(fake_data_set.strpath)
    g.init()
    fake_build_index.assert_called()
    assert g.lookup is fake_index['lookup']
    assert g.token_to_item is fake_index['token_to_item']
    assert g.n_gram_to_tokens is fake_index['n_gram_to_tokens']


def test_guess_init_no_file():
    g = Guess('foo/bar.json')
    with pytest.raises(strategy.StrategyError) as e:
        g.init()
        assert 'Failed to open data source' in e


def test_guess_init_bad_file(fake_data_set_invalid):
    g = Guess(fake_data_set_invalid.strpath)
    with pytest.raises(strategy.StrategyError) as e:
        g.init()
        assert 'Data source is invalid' in e


def test_guess_build_index(fake_data_set):
    g = Guess(fake_data_set.strpath)
    g.init()
    assert len(g.token_to_item)
    expected = {'Eggs', 'Fried Eggs', 'Scrambled Eggs', 'Poached Eggs'}
    assert set(g.token_to_item['eggs']) - expected == set()
    assert len(g.n_gram_to_tokens)
    assert g.n_gram_to_tokens['toa'] == {'toast'}
    assert g.n_gram_to_tokens['toas'] == {'toast'}
    assert g.n_gram_to_tokens['toast'] == {'toast'}


def test_guess_tokens_from_ngrams(fake_data_set):
    g = Guess(fake_data_set.strpath)
    g.init()
    expected = {'toast', 'eggs', 'sausage'}
    result = g._tokens_from_ngrams(['toa', 'egg', 'saus', 'sausag', 'sausage'])
    assert set(result) - expected == set()


def test_guess_ranking_initial(fake_data_set):
    g = Guess(fake_data_set.strpath)
    g.init()
    result = g._ranking_initial(['toast', 'eggs', 'sausage'])
    mapped = {score[0]: score[1] for score in result}
    # Exact matches
    assert mapped['Toast'] == 1.0
    assert mapped['Eggs'] == 1.0
    assert mapped['Sausage'] == 1.0
    # Not exact matches
    assert mapped['Raisin Toast'] < 1.0
    assert mapped['Fried Eggs'] < 1.0
    assert mapped['Black Sausage'] < 1.0
    assert 'Beans' not in mapped


def test_guess_ranking_combined(fake_data_set):
    g = Guess(fake_data_set.strpath)
    g.init()
    scores = g._ranking_initial(['toast'])
    ranked = g._ranking_combined(scores, 1)
    # Exact match so highest rank
    assert ranked['Toast'] == 1.0
    # Not exact match
    assert ranked['Raisin Toast'] < 1.0
    assert len(ranked) == 2


def test_guess_filtered_results(fake_data_set):
    g = Guess(fake_data_set.strpath)
    g.init()
    scores = g._ranking_initial(['veggie', 'sausage'])
    ranked = g._ranking_combined(scores, 1)
    results = g._filtered_results(ranked)
    assert results[0] == 'Veggie Sausage'
    for result in results[1:]:
        assert ranked[result] > 0.4


def test_guess_filtered_results_above_threshold(fake_data_set_too_many_chiefs):
    g = Guess(fake_data_set_too_many_chiefs.strpath)
    g.SCORE_THRESHOLD = 0.2  # Drop threshold to include plenty of results
    g.init()
    scores = g._ranking_initial(['chief', 'executive', 'officer'])
    ranked = g._ranking_combined(scores, 1)
    results = g._filtered_results(ranked)
    scores_list = list(scores)
    above_threshold = [s[0] for s in scores_list if s[1] >= g.SCORE_THRESHOLD]
    # Make sure conditions for test are correct
    assert len(above_threshold) > 10
    # Test that the results are a subset of the above threshold items
    assert set(results) <= set(above_threshold)
    print(scores_list, len(above_threshold))


def test_guess_filtered_results_below_threshold(fake_data_set_large):
    g = Guess(fake_data_set_large.strpath)
    g.init()
    scores = g._ranking_initial(['islands'])
    ranked = g._ranking_combined(scores, 1)
    results = g._filtered_results(ranked)
    scores_list = list(scores)
    # Make sure conditions for test are correct
    above_threshold = [s for s in scores_list if s[1] >= 0.4]
    below_threshold = [s for s in scores_list if s[1] < 0.4]
    assert len(above_threshold) < 10
    assert len(below_threshold) > 1
    # Test that the results back-fill with low ranked items happened
    below_th_but_included = (set([s[0] for s in scores_list if s[1] < 0.4]) &
                             set(results)
                             )
    assert len(below_th_but_included) == 10 - len(above_threshold)


def test_guess_filtered_results_no_possibles(fake_data_set_large):
    g = Guess(fake_data_set_large.strpath)
    g.init()
    scores = g._ranking_initial(['virgin'])
    ranked = g._ranking_combined(scores, 1)
    results = g._filtered_results(ranked)
    scores_list = list(scores)
    # Make sure conditions for test are correct
    below_threshold = [s for s in scores_list if s[1] < 0.4]
    assert len(below_threshold) == len(scores_list)
    # Test that the results consist entirely of low ranked items
    below_th_but_included = (set([s[0] for s in scores_list if s[1] < 0.4]) &
                             set(results)
                             )
    assert len(below_th_but_included) == len(below_threshold)


def test_guess_candidates(monkeypatch, fake_data_set):
    g = Guess(fake_data_set.strpath)
    fake_method = mock.Mock(return_value=['eggs', 'fried'])
    g.init()
    monkeypatch.setattr(g.lookup, 'lookup_phrase', fake_method)
    results = g.candidates('foo')
    fake_method.assert_called_with('foo')
    assert 'Fried Eggs' in results


def test_phrase_lookup_edits_single():
    # Check just a few of each edit type
    term = 'word'
    single_edits = PhraseLookup._single_edits(term)
    # Deletes
    assert {'wor', 'wrd', 'ord'} <= single_edits
    assert {'w9ord', 'worzd', 'words'} <= single_edits
    # Overall, for a word of length n there will be n deletions,
    # and 36(n + 1) insertions. Expect n duplicates that appear in the set
    # once. Note that 36 == len(a-z0-9)
    n = len(term)
    total = n + (36*(n+1))
    set_total = total - n
    assert set_total == len(single_edits)


def test_phrase_lookup_edits_double():
    term = 'word'
    edits = PhraseLookup._single_edits(term)
    double_edits = PhraseLookup._double_edits(term)
    expected = set(e2 for e1 in edits for e2 in PhraseLookup._single_edits(e1))
    assert double_edits - expected == set()


def test_phrase_lookup_known(fake_data_set_data):
    p = PhraseLookup()
    p.prime(fake_data_set_data)
    assert {'bacon', 'eggs'} - p._known({'bacon', 'eggs', 'hamster'}) == set()


def test_phrase_lookup_phrase(fake_data_set_data):
    p = PhraseLookup()
    p.prime(fake_data_set_data)
    result = p.lookup_phrase('bacn erggs to0ast')
    assert 'bacon' in result
    assert 'eggs' in result
    assert 'toast' in result
