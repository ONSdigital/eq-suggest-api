"""Suggester Api."""

import sys

from logbook import Logger, StreamHandler

from flask import request, redirect, url_for
from flask_api import FlaskAPI, exceptions

from . import guess
from . import registry


app = FlaskAPI(__name__)
app.logger.propagate = True
del app.logger.handlers[:]
StreamHandler(sys.stdout).push_application()
log = Logger(__name__)
log.info('Logging configured')


PAGE_SIZE = 100


@app.route('/', methods=['GET'])
def root():
    """Root.

    Redirects to /api and the top level resource.
    """
    return redirect(url_for('data_sets'))


@app.route('/api', methods=['GET'])
def data_sets():
    """List of available data sets.

    This is the entry point resource and provides a list of available data
    sets that can be searched by the suggester service.

    To use the service, specify a URL with the desired data set name and a
    query parameter to search the data set.  Up to 10 'fuzzy' matches are
    returned. For example try: GET api/occupations/?q=yeoman warder
    """
    all_data_sets = registry.get_data_sets()
    keys = sorted(all_data_sets.keys())
    response = []
    for k in keys:
        item = all_data_sets[k]
        item['url'] = request.host_url.rstrip('/') + url_for('data_set', key=k)
        item['name'] = k
        response.append(item)
    return response


@app.route('/api/<key>/', methods=['GET'])
def data_set(key):
    """Data set content.

    Resource containing data set content. If the 'q' query parameter is
    specified a list of up to 10 data set items that 'fuzzily' match the query
    parameter are returned. This means a query string can be a misspelling;
    suggester will use Bayesian probabilities to have a good guess at candidate
    matches. If no 'q' query parameter is specified a all data set content is
    returned (paginated).
    """
    all_data_sets = registry.get_data_sets()
    if key not in all_data_sets:
        raise exceptions.NotFound()
    source = all_data_sets[key]['source']
    query = request.args.get('q')
    if query:
        matches = _get_suggestions(source, query)
        return dict(previous=None, next=None, start=None,
                    matches=matches, items=None, count=len(matches))
    else:
        start = int(request.args.get('start', 1),)
        url = request.host_url.rstrip('/') + url_for('data_set', key=key)
        return _paginate(registry.get_data_set_content(source),
                         url, start)


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


def _get_suggestions(data_set_source, query):
    """Get suggestions.

    Get suggestions for a given query string.

    :param (str) data_set_source: Data set to query.
    :param (str) query: Query string.
    :returns (list): List of 10 candidates
    """
    g = guess.Guess(data_set_source)
    g.init()
    return g.candidates(query)[:10]


def _paginate(data, url, start):
    """Paginate data set content.

    :param (dict) data: The data set content.
    :param (str) url: URL to resource used to be used in perv/next properties.
    :param (int) start: Page position.
    :returns (dict): Paginated resource content.
    """
    qty = len(data)
    if start > qty or start < 1:
        raise exceptions.NotFound()
    response = dict(start=start)
    if start == 1:
        response['previous'] = None
    else:
        previous_pos = max(1, start - PAGE_SIZE)
        response['previous'] = url + f'?start={previous_pos}'
    next_pos = min(qty, start + PAGE_SIZE)
    if next_pos >= qty:
        response['next'] = None
    else:
        response['next'] = url + f'?start={next_pos}'
    start_idx = start - 1
    response['matches'] = None
    page = data[start_idx:start_idx + PAGE_SIZE]
    response['items'] = page
    response['count'] = len(page)
    return response
