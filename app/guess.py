"""Lookup module."""
import json
import re
import string

from collections import defaultdict


class GuessError(Exception):
    """Guess error.

    Raised when Guess operation errors occur.
    """
    pass


SUBSTITUTES = [
    ('(', ''), (')', ''), (',', ' '), ('\'', ''), ('"', ''), ('\u2019', ''),
    ('\u00e5', 'a'), ('\u00e2', 'a'), ('\u00e7', 'c'), ('\u00e9', 'e'),
    ('\u00e8', 'e')
]


class Guess:
    """Guess.

    Guess a data item match from a simple data source using a given phrase and
    Bayesian probabilities.  The data source should be a simple json file
    containing a single list of strings.

    Something about cleaned data set and charset ...
    ...

    """
    MIN_N_GRAM_SIZE = 3
    CHARSET = string.ascii_lowercase + string.digits + 'ÉéåÅÇç’-,()'  # Take out all, should be normalised out?

    def __init__(self, source):
        """Constructor.

        :param (str) source: Path to the json file data source.
        """
        self.source_file = source
        self.data = []
        self.token_to_item_name = defaultdict(list)
        self.n_gram_to_tokens = defaultdict(set)
        self.pl = PhraseLookup()

    def init(self):
        """Initialise instance.

        Load the specified data source and build mappings to tokens to
        normalised item names, and also build n-grams and map to tokens.

        :raises: GuessError
        """
        try:
            with open(self.source_file, 'r') as f:
                self.data = json.load(f)
                assert isinstance(self.data, list)
        except FileNotFoundError as e:
            raise GuessError(f'Failed to open data source {e}')
        except AssertionError:
            raise GuessError('Data source is not a list')
        self.pl.prime(self.data)
        for item in self.data:
            # TODO Need some others "," "'". Need to cope with "é"
            norm_item = item.lower().replace("(", "").replace(")", "")
            tokens = norm_item.split()
            for token in tokens:
                self.token_to_item_name[token].append(norm_item)
                for string_size in range(Guess.MIN_N_GRAM_SIZE, len(token) + 1):
                    n_gram = token[:string_size]
                    self.n_gram_to_tokens[n_gram].add(token)

    def _get_real_tokens_from_possible_n_grams(self, tokens):
        real_tokens = []
        for token in tokens:
            token_set = self.n_gram_to_tokens.get(token, set())
            real_tokens.extend(list(token_set))
        return real_tokens

    def _get_scored_items_uncollapsed(self, real_tokens):
        scores = []
        for token in real_tokens:
            possibles = self.token_to_item_name.get(token, [])
            for item in possibles:
                score = float(len(token)) / len(item.replace(" ", ""))
                scores.append((item, score))
        return scores

    @staticmethod
    def _combined_scores(scores, num_tokens):
        collapsed_item_to_score = defaultdict(int)
        collapsed_item_to_occurrence = defaultdict(int)
        for item, score in scores:
            collapsed_item_to_score[item] += score
            collapsed_item_to_occurrence[item] += 1
        for item in collapsed_item_to_score.keys():
            collapsed_item_to_score[item] *= (
                    collapsed_item_to_occurrence[item] / float(num_tokens))
        return collapsed_item_to_score

    @staticmethod
    def _filtered_results(scores):
        min_results = 3
        max_results = 10
        score_threshold = 0.4
        scores_list = list(scores)
        max_possibles = scores_list[:max_results]
        if scores and scores_list[0][1] == 1.0:
            return [scores_list[0][0]]

        possibles_within_thresh = [
            tuple_obj for tuple_obj in scores
            if tuple_obj[1] >= score_threshold
        ]
        min_possibles = (possibles_within_thresh
                         if len(possibles_within_thresh) > min_results
                         else max_possibles[:min_results]
                         )
        return [tuple_obj[0] for tuple_obj in min_possibles]

    def candidates(self, query):
        tokens = self.pl.lookup_phrase(query)
        real_tokens = self._get_real_tokens_from_possible_n_grams(tokens)
        scores = self._get_scored_items_uncollapsed(real_tokens)
        collapsed_item_to_score = self._combined_scores(scores, len(tokens))
        scores = collapsed_item_to_score.items()
        scores_list = list(scores)
        scores_list.sort(key=lambda t: t[1], reverse=True)
        return self._filtered_results(scores)


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
        for substitute in SUBSTITUTES:
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

        :param (str) word: Word to generate single edits for.
        :returns (set): The set of all single edits.
        """
        charset = string.ascii_lowercase + string.digits
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [a + b[1:] for a, b in splits if b]
        transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
        replaces = [a + c + b[1:] for a, b in splits for c in charset if b]
        inserts = [a + c + b for a, b in splits for c in charset]
        return set(deletes + transposes + replaces + inserts)

    @staticmethod
    def _double_edits(word):
        """Set of double edits.

        Using single edit misspellings returns a set of words that are two
        edits away.

        :param (str) word: Word to generate edits for.
        :returns (set): The set of all double edits.
        """
        return set(e2 for e1 in PhraseLookup._single_edits(word)
                   for e2 in PhraseLookup._single_edits(e1))

    def _known(self, words):
        """Set of known words.

        Given a set of words, returns the subset that are in the model, i.e.
        known words.

        :param (set) words: A list of words.
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
                      self._known(self._double_edits(word)) or
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
