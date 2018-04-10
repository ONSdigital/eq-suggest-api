#!/usr/bin/env python
"""eq-suggest-api entry point.

EQ Suggest API provides a simple ReST service that enables a range of data
sets to be queried with arbitrary terms.  Given a term the API will return a
set of candidate matches that take an incomplete term, misspellings and typos
into account.  The API also exposes each data set as paginated resources.
"""
from app import app

if __name__ == '__main__':
    app.run(debug=True)
