"""Guess search strategy.

There are three structures that form the index used when making a guess:

`token_to_item`: A mapping of all known words in the data set to a
list of phrases in the data set that contain that word, e.g:
token_to_item = {
  'town': [
    'town hall superintendent', 'town planner', 'town planning assistant'
  ],
  "hall": [
    "town hall superintendent"
  ],
  ...
}

`n_gram_to_tokens`: A mapping of edge n-grams to sets of known words in
the data set that relate to the n-gram, e.g:

n_gram_to_tokens = {
  "invest":
    {"investigator', 'investigation', 'investigating', 'investment',
     'investigations', 'investor', 'investments'},
  "investi":
    {'investigator', 'investigation', 'investigating', 'investigations'},
  ...
}

Additionally, `PhraseLookup` used so that the tokens in a query can be
transformed into likely known words in the data set before performing an
index check.
"""
import json
import re
import string

from collections import defaultdict

import logbook

import app.strategy as strategy

log = logbook.Logger(__name__)

STRATEGY_NAME = 'guess'


class Guess(strategy.Strategy):
    """Guess search strategy.

    Guess a word or phrase occurrence in simple data source using a given word
    or phrase.  The data source should be a simple json file containing a
    single list of strings.
    """
    MIN_N_GRAM_SIZE = 3
    SCORE_THRESHOLD = 0.4

    def __init__(self, data_file, max_matches=10):
        """Constructor.

        :param (str) data_file: Path to the json file data file.
        :param (int) max_matches: Maximum matches to return, default is 10.
        """
        self.max_matches = max_matches
        self.token_to_item = defaultdict(list)
        self.n_gram_to_tokens = defaultdict(set)
        self.lookup = None
        super().__init__(data_file, STRATEGY_NAME)

    def init(self):
        """Initialise.

        Calls base implementation to load or lazily build the indexes.
        """
        idx = super().init()
        self.lookup = idx['lookup']
        self.token_to_item = idx['token_to_item']
        self.n_gram_to_tokens = idx['n_gram_to_tokens']

    def build_index(self):
        """Build the search index.

        Normalises the data set to all lower case and using the global
        SUBSTITUTES list to remove/replace certain characters.  We then build
        the two pivotal structures used for the index: `token_to_item` and
        `n_gram_to_tokens`.

        Note we use the original item word or phrase in the lookup but use the
        normalised version to create the index tokens.
        """
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise strategy.StrategyError(f'Failed to open data source: {e}')
        except json.decoder.JSONDecodeError as e:
            raise strategy.StrategyError(f'Data source is invalid: {e}')
        token_to_item = defaultdict(list)
        n_gram_to_tokens = defaultdict(set)
        for item in data:
            norm_item = item.lower()
            for substitute in strategy.SUBSTITUTES:
                norm_item = norm_item.replace(substitute[0], substitute[1])
            tokens = norm_item.split()
            for token in tokens:
                token_to_item[token].append(item)
                for string_size in range(Guess.MIN_N_GRAM_SIZE, len(token) + 1):
                    n_gram = token[:string_size]
                    n_gram_to_tokens[n_gram].add(token)
        lookup = PhraseLookup()
        lookup.prime(data)
        idx = {'n_gram_to_tokens': n_gram_to_tokens,
               'token_to_item': token_to_item,
               'lookup': lookup}
        return idx

    def _tokens_from_ngrams(self, tokens):
        """Tokens from n-grams.

        Treat the provided list of tokens as n-grams and lookup mapped real
        tokens in `n_gram_to_tokens`.

        :param (list) tokens: List of tokens treated as n-grams.
        :returns (list): A token set from the index that matches the requests.
        """
        token_set = set()
        for token in tokens:
            token_set |= self.n_gram_to_tokens.get(token, set())
        return list(token_set)

    def _ranking_initial(self, real_tokens):
        """Initial ranking by matching length to token.

        The closer in length a possible match in the token to item lookup is,
        the higher its score, i.e. 20/20 is score of 1.0 compared to 10/20 is
        a score of 0.5.  This provides a basic ranking.

        :param (list) real_tokens: Tokens used to lookup possible matches.
        :returns (list): List of tuples (possible-match, score)
        """
        scores = []
        for token in real_tokens:
            possibles = self.token_to_item.get(token, [])
            for item in possibles:
                score = len(token) / len(item.replace(' ', ''))
                scores.append((item, score))
        return scores

    @staticmethod
    def _ranking_combined(scores, num_tokens):
        """Combine ranks weighted on occurrence.

        :param (list) scores: List of (possible-match, score) tuples.
        :param (int) num_tokens: The number of original tokens that were input.
        :returns (defaultdict): Map of rankings (possible-match->score)
          with ranks based on initial ranking and occurrences.
        """
        ranked_items = defaultdict(int)
        item_to_occurrence = defaultdict(int)
        for item, score in scores:
            ranked_items[item] += score
            item_to_occurrence[item] += 1
        for item in ranked_items:
            ranked_items[item] *= (item_to_occurrence[item] / num_tokens)
        return ranked_items

    def _filtered_results(self, scores):
        """Filter results.

        Filter results to maximum number of highest ranked matches.

        :param (defaultdict) scores: Map of rankings (possible-match->score).
        :returns (list): Up to `self.max_matches` highest ranking results.
        """
        scores_list = list(scores.items())
        scores_list.sort(key=lambda t: t[1], reverse=True)
        possibles_in_threshold = [match for match in scores_list
                                  if match[1] >= self.SCORE_THRESHOLD
                                  ]
        if not possibles_in_threshold:
            # Nothing in threshold so slice highest of whatever there is
            possibles_in_threshold = scores_list[:self.max_matches]
        elif len(possibles_in_threshold) > self.max_matches:
            # Too many in threshold so take a slice
            possibles_in_threshold = possibles_in_threshold[:self.max_matches]
        else:
            # Not enough in threshold so back-fill
            spare = scores_list[len(possibles_in_threshold):self.max_matches]
            possibles_in_threshold = possibles_in_threshold + spare
        return [match[0] for match in possibles_in_threshold]

    def candidates(self, query):
        """Get candidate matches.

        Main interface of the class, given a query returns a list of candidate
        matches.

        :param (str) query: Query string.
        :returns (list): List of candidate matches.
        """
        tokens = self.lookup.lookup_phrase(query.lower())
        real_tokens = self._tokens_from_ngrams(tokens)
        scores = self._ranking_initial(real_tokens)
        ranked_items = self._ranking_combined(scores, len(tokens))
        return self._filtered_results(ranked_items)


class PhraseLookup:
    """PhraseLookup.

    Given a data set creates a model of known words and the probability of
    their occurrence in a supplied the data set. When a phrase is checked
    against the model each word in the phrase is checked against a range of
    'edits' to establish a likely match for each word in the phrase supplied.
    """
    def __init__(self):
        self.model = None

    def prime(self, data):
        """Prime the model.

        Given a data set, build a normalised model that records the count of
        each word in the data set.  When determining candidates for a lookup
        we use the word with the highest probability of being the match.

        :param (list) data: A simple list of words or phrases.
        """
        self.model = self._build_model(self._words(data))

    @staticmethod
    def _words(data):
        """Build word list.

        Takes all the phrases in the data set and creates a normalised word
        list.

        :param (list) data: Input data set.
        :returns (list): Normalised list of data set words.
        """
        all_text = ' '.join(data).lower()
        for substitute in strategy.SUBSTITUTES:
            all_text = all_text.replace(substitute[0], substitute[1])
        return re.findall('[a-z0-9]+', all_text)

    @staticmethod
    def _build_model(word_list):
        """Build model.

        Build the probabilities from a supplied word list.

        :param (list) word_list: List of know words.
        :returns (collections.defaultdict): Map of word counts.
        """
        model = defaultdict(int)
        for word in word_list:
            model[word] += 1
        return model

    @staticmethod
    def _single_edits(word):
        """Set of single edits.

        Given a word, return a set of edited versions that are one edit
        away. These include single character deletions, transpositions,
        replacements and inserts. Due to the likelihood of duplicates we
        return a set.

        Optionally add other misspellings like this:
        transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
        replaces = [a + c + b[1:] for a, b in splits for c in charset if b]
        return set(deletes + transposes + replaces + inserts)

        :param (str) word: Word to generate single edits for.
        :returns (set): The set of all single edits.
        """
        charset = string.ascii_lowercase + string.digits
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [a + b[1:] for a, b in splits if b]
        inserts = [a + c + b for a, b in splits for c in charset]
        return set(deletes + inserts)

    def _known(self, words):
        """Set of known words.

        Given a set of words, returns the subset that are in the model, i.e.
        known words.

        :param (set) words: A set of words.
        :returns (set): The subset of words that are known to the model.
        """
        return set(w for w in words if w in self.model)

    def _lookup_word(self, word):
        """Lookup word.

        Given a word, use the model to find the most likely candidate match.

        :param (str) word: Word to look up.
        :returns (str): Either a known word from the model determined from the
          single or double edits else the supplied word.
        """
        candidates = (self._known({word}) or
                      self._known(self._single_edits(word)) or
                      {word})
        return max(candidates, key=self.model.get)

    def lookup_phrase(self, phrase):
        """Look up phrase.

        Given a phrase, lookup each word in the phrase.

        :param (str) phrase: Phrase to look up.
        :returns (list): List containing each candidate match for word in
          supplied phrase, or the original word in the supplied phrase if no
          candidate was found.
        """
        words = phrase.split()
        return [self._lookup_word(word) for word in words]
