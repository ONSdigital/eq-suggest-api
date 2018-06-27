"""Strategy.

Base definitions for a search strategy.
"""
import os
import pickle


class StrategyError(Exception):
    """StrategyError

    Raised when search strategy error occurs.
    """
    pass


SUBSTITUTES = [
    ('(', ''), (')', ''), (',', ' '), ('\'', ''), ('"', ''),
    ('-', ' '), ('/', ' '), ('\\', ' '), ('_', ' '), (':', ' '),
    ('\u2019', ''), ('\u00e5', 'a'), ('\u00e2', 'a'), ('\u00e7', 'c'),
    ('\u00e9', 'e'), ('\u00e8', 'e')
]

INDEX_LOCATION = 'index'


class Strategy:
    """Strategy."""
    def __init__(self, data_file, strategy):
        """Constructor.

        :param (str) data_file: Path to the json file data source.
        :param (str) strategy: Name of strategy.
        """
        self.data_file = data_file
        self.strategy_name = strategy

    def init(self):
        """Initialise.

        Load the index.  If there is no index, then invokes the `build_index`
        implementation and stores the result.
        """
        idx_name = Strategy.index_name(self.data_file, self.strategy_name)
        idx = Strategy.load_index(idx_name)
        if not idx:
            idx = self.build_index()
            Strategy.store_index(idx_name, idx)
        return idx

    @staticmethod
    def load_index(idx_name):
        """Load the search index.

        Attempts top load the search index if it exists.
        :param (str) idx_name: Index file name.
        :returns: The deserialized index if it exists otherwise None.
        """
        try:
            with open(idx_name, 'rb') as f:
                idx = pickle.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            raise StrategyError(
                f'Failed to load index for data source {e}')
        else:
            return idx

    @staticmethod
    def index_name(path, strategy):
        """Build an index file name."""
        if not os.path.exists(INDEX_LOCATION):
            os.makedirs(INDEX_LOCATION)
        pth = os.path.join(INDEX_LOCATION,
                           path.split('.json')[0].replace('/', '_'))
        return f'{pth}_{strategy}.idx'

    @staticmethod
    def store_index(path, idx):
        try:
            with open(path, 'wb') as f:
                pickle.dump(idx, f, -1)
        except Exception as e:
            raise StrategyError(
                f'Failed to create index: {path} Reason: {e}')

    def build_index(self):
        """Build the index.

        Override this method to load the json data as specified by
        `self.data_file` and build your index structure.
        :returns: The freshly built index.
        """
        raise NotImplementedError()

    def candidates(self, query):
        """Get candidate matches.

        Override this method to provide the main interface of a search
        implementation. Given a query, your implementation should return
        a list of candidate matches.

        :param (str) query: Query string.
        :returns (list): List of candidate matches.
        """
        raise NotImplementedError()
