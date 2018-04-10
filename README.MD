# eQ Suggest API

EQ Suggest API provides a simple ReST service that enables a range of data
sets to be queried with arbitrary terms.  Given a term the API will return a
set of candidate matches that take an incomplete term, misspellings and typos
into account.  The API also exposes each data set as paginated resources.

**This is currently a spike.  You can either build an run a docker image or run in a virtual environment**.

## Build and run a Docker container
- Install Docker for your system: https://www.docker.com/
- Clone the repo, build and run the Docker image:
  ```bash
   $ git clone git@github.com:ONSdigital/eq-suggest-api.git
     ...
   $ docker build eq-suggest-api
     ...
     Step 11/11 : COPY . /usr/src/app
     ---> 00b93410be43
     Successfully built 00b93410be43
   $ docker run -p 5000:5000 00b93410be43
   ```
- Optionally tag and push the image.

## Run locally in a virtual environment
- Clone the repo:
  ```bash
   $ git clone git@github.com:ONSdigital/eq-suggest-api.git
    ```

- Install dependencies, activare virtual environment and run:
  ```bash
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
To browse the API navigate a browser to `http://localhost:5000`.  You will be redirected to the root of the API at `api/`.  The root resource (Data sets) is a collection of known data sets, e.g:


### Data sets (root) resource 
```
GET /api
HTTP 200 OK
Content-Type: application/json
[
    {
        "source": "data/counties_english.json",
        "size_bytes": 496,
        "size": "496 Bytes",
        "timestamp_raw": 1522857781.0,
        "timestamp": "2018-04-04T16:03:01",
        "item_count": 37,
        "url": "http://localhost:5000/api/counties_english/",
        "name": "counties_english"
    },
    ...
]
```

### Data set resource 
By default each contained resource will return a single resource, paginated across the entire list of data set items.

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
