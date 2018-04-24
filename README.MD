# eQ Suggest API

EQ Suggest API provides a simple ReST service that enables a range of data
sets to be queried with arbitrary terms.  Given a term the API will return a
set of candidate matches that take an incomplete term, misspellings and typos
into account.  The API also exposes each data set as paginated resources.

You can either build and run a docker container or run in a virtual environment**.  First, clone the repo:

  ```bash
   $ git clone git@github.com:ONSdigital/eq-suggest-api.git
   ```
   
## Run a docker container
- Pull from docker hub and run: 
  ```bash
  $ docker run -p 5000:5000 onsdigital/eq-suggest-api
  ```
 
## Build and run a Docker container
- Install Docker for your system: https://www.docker.com/
- Build and run the Docker image (make sure you are in the directory of the cloned repo):
  ```bash
   $ docker build ../eq-suggest-api
     ...
     Step 11/11 : COPY . /usr/src/app
     ---> 00b93410be43
     Successfully built 00b93410be43
   $ docker run -p 5000:5000 00b93410be43
   ```

## Run in a virtual environment
- Make sure you have a working `pipenv` installation.
- Install dependencies, activate virtual environment and run:
  ```bash
   $ cd eq-suggest-api
   $ pipenv install --dev
     ...
   $ pipenv shell
     Spawning environment shell (/bin/bash). Use 'exit' to leave.
     ...
   $ FLASK_APP=application.py flask run
   [2018-04-10 14:05:11.419541] INFO: app: Logging configured
    * Serving Flask app "application"
    * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)   
  ```

## Usage
To browse the API navigate a browser to `http://localhost:5000`.  You will be redirected to the root of the API at `api/`.  The root resource (`Data sets`) is a collection of known data sets (i.e. the json file in `eq-suggest-api/data`), e.g:


### Data sets (root) resource 
```
GET /api
HTTP 200 OK
Content-Type: application/json
[
    ...
    {
        "source": "data/occupations.json",
        "size_bytes": 881200,
        "size": "881.2 kB",
        "timestamp_raw": 1522753154.0,
        "timestamp": "2018-04-03T10:59:14",
        "item_count": 32207,
        "url": "http://localhost:5000/api/occupations/",
        "name": "occupations"
    },
    ...
]
```

### Data set resource 
By default each contained resource will return a single resource, paginated across the entire list of data set items.  You can request a `Data set` resource from any starting point using the `start` query parameter.

```
GET /api/industries/
HTTP 200 OK
Content-Type: application/json

{
    "start": 1,
    "previous": null,
    "next": "http://localhost:5000/api/industries/?start=101",
    "matches": null,
    "items": [
        "6th form college",
        "A&E clothing retail",
        "A&E hospital",
        ...
        "Accountants in public practice",
        "Accountants management consultants"
    ],
    "count": 100
}
```

### Data set resource query
By specifying a query term using the `q` parameter, eq-suggest-api will return a list of candidate matches (if any).  Up to 10 candidate matches are returned.

```
GET /api/industries/?q=yellowcake
HTTP 200 OK
Content-Type: application/json

{
    "previous": null,
    "next": null,
    "start": null,
    "matches": [
        "yellowcake production",
        "yellowcake to uranium tetrafluoride and hexafluoride conversion manufacture"
    ],
    "items": null,
    "count": 2
}
```

### Notes
- The `start` and `q` parameters are ignored when requesting the root resource.
- The `start` and `q` parameters cannot be mixed, if the `q` parameter is specified then `start` is ignored.
- When a `Data set` resource is requested without the `q` parameter specified the returned resource will always have the `matches` attribute set to `null`.
- When a `Data set` resource is requested without without the `q` parameter specified and the returned resource is the first page, the `previous` attribute is set to `null`
- When a `Data set` resource is requested without without the `q` parameter specified and the returned resource is the last page, the `next` attribute is set to `null`
- When a `Data set` resource is requested with the `q` parameter specified the returned resource will always have the following attributes set `null`:
  - `previous`
  - `next`
  - `start`
  - `items`
