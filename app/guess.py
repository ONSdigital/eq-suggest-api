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


class Guess:
    """Guess.

    Guess a data item match from a simple data source using a given phrase and
    Bayesian probabilities.  The data source should be a simple json file
    containing a single list of strings.
    """
    MIN_N_GRAM_SIZE = 3
    CHARSET = string.ascii_lowercase + string.digits + 'ÉéåÅÇç’-,()'

    def __init__(self, source):
        """Constructor.

        :param (str) source: Path to the json file data source.
        """
        self.source_file = source
        self.data = []
        self.token_to_item_name = defaultdict(list)
        self.n_gram_to_tokens = defaultdict(set)
        self.fuzzer = Fuzzer(self.CHARSET)

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
        self.fuzzer.prime(self.data)
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
        tokens = self.fuzzer.correct_phrase(query)
        real_tokens = self._get_real_tokens_from_possible_n_grams(tokens)
        scores = self._get_scored_items_uncollapsed(real_tokens)
        collapsed_item_to_score = self._combined_scores(scores, len(tokens))
        scores = collapsed_item_to_score.items()
        scores_list = list(scores)
        scores_list.sort(key=lambda t: t[1], reverse=True)
        return self._filtered_results(scores)


class Fuzzer:
    """Fuzzer.

    Creates variations to check against.
    """
    def __init__(self, charset):
        self.nwords = None
        self.charset = charset

    def prime(self, data):
        self.nwords = self.train(self.words(' '.join(data)))

    def words(self, all_text):
        """

        :param (str) all_text:
        :returns: All matches
        """
        return re.findall('[a-z0-9]+', all_text.lower())

    def train(self, features):
        model = defaultdict(int)
        for f in features:
            model[f] += 1
        return model

    def _edits1(self, word):
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [a + b[1:] for a, b in splits if b]
        transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
        replaces = [a + c + b[1:] for a, b in splits for c in self.charset if b]
        inserts = [a + c + b for a, b in splits for c in self.charset]
        return set(deletes + transposes + replaces + inserts)

    def _known_edits2(self, word):
        return set(e2 for e1 in self._edits1(word) for e2 in self._edits1(e1)
                   if e2 in self.nwords)

    def _known_substr(self, words):
        return set(w for w in words if w in self.nwords)

    def _known(self, words):
        return set(w for w in words if w in self.nwords)

    def correct_token(self, token):
        candidates = (self._known([token]) or self._known(self._edits1(token)
                      or self._known_edits2(token)))
                       # self._known_substr(token)))
        if candidates:
            return max(candidates, key=self.nwords.get)
        return 'None'

    def correct_phrase(self, text):
        tokens = text.split()
        return [self.correct_token(token) for token in tokens]
