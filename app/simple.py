"""Simple Guess module.

Builds a really simple index.
"""
import json

from collections import defaultdict

from logbook import Logger

import app.strategy as strategy

log = Logger(__name__)


STRATEGY_NAME = 'simple'


class Simple(strategy.Strategy):
    """Simple.

    Performs a simple lookup of a term.
    """
    MIN_N_GRAM_SIZE = 3

    def __init__(self, data_file, max_matches=10):
        """Constructor.

        :param (str) data_file: Path to the json file data file.
        :param (int) max_matches: Maximum matches to return, default is 10.
        """
        self.max_matches = max_matches
        self.index = None
        super().__init__(data_file, STRATEGY_NAME)

    def init(self):
        """Initialise.

        Calls base implementation to load or lazily build the index.
        """
        self.index = super().init()

    def candidates(self, query):
        """Get candidate matches.

        Main interface of the class, given a query returns a list of candidate
        matches.

        :param (str) query: Query string.
        :returns (list): List of candidate matches.
        """
        possibles = self.index.get(query.lower())
        if possibles:
            return list(self.index.get(query))[:self.max_matches]
        return []

    def build_index(self):
        """Build the search index.

        Normalises the data set to all lower case and using the global
        SUBSTITUTES list to remove/replace certain characters.  We then build
        the two pivotal structures used for the index: `token_to_item` and
        `n_gram_to_tokens`.

        Note we use the original item word or phrase in the lookup but use the
        normalised version to create the index tokens.
        """
        idx = defaultdict(set)
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise strategy.StrategyError(f'Failed to open data source: {e}')
        except json.decoder.JSONDecodeError:
            raise strategy.StrategyError(f'Data source is invalid: {e}')
        for item in data:
            norm_item = item.lower()
            for substitute in strategy.SUBSTITUTES:
                norm_item = norm_item.replace(substitute[0], substitute[1])
            for i in range(0, len(norm_item)):
                for string_size in range(Simple.MIN_N_GRAM_SIZE,
                                         len(norm_item) + 1):
                    n_gram = norm_item[i:string_size]
                    idx[n_gram].add(item)
        return idx
