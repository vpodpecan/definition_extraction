## Definition extraction service


### About

This repository contains the code for definition extraction in Slovene language.
It was developed as a part of the [RSDO project](https://www.cjvt.si/rsdo/en/project/).

The code can be used as a command line tool as well as a web service which accepts POST requests at `DefExAPI/definition_sentence_extraction/` with the following two form parameters:

  - conllu_file [mandatory]: a text file containing CoNLL-U data
  - terms [optional]: a string containing a list of lemmatized terms in JSON format such as:

    ```{"lemmatized_terms": ["first term", "second term", ...]}```

**Important**: because the service expects a file, the POST request's `Content-Type` cannot be `application/json` but `multipart/form-data`.
As a result, the terms parameter must be a string in the POST request form data and should contain valid JSON.



### Requirements

-  docker
-  docker-compose


When using it as a commnad line utility (without docker) the requirements are as follows:

- python 3.6+
- Perl 5 (other versions may also work)
- python packages listed in requirements.txt



### Installation

The following command

```sh
$ docker-compose up --build
```

will build the images and run the container. The application is now available for testing at [http://localhost:5005](http://localhost:5005).

### Deployment

The `docker-compose.prod.yml` configuration file is ready to be used in production.
By default, the application is served on port 8080 but this can be changed if needed.
The size limit for the file upload in the nginx configuration is currently set to 128 MB.

```sh
$ docker-compose -f docker-compose.prod.yml up --build -d
```



### How to use

#### Web service

The service exposes its documentation using Swagger and offers a web interface for testing:
the default URLs are [http://localhost:5005/](http://localhost:5005/) in the development version and [http://localhost:8080/](http://localhost:8080/)
in the production version.


As an alternative, you can use `curl` to call or test the service. Here is an example of a valid call to the service running on localhost at port 5005 and its result.
Note that the POST request submits a form containing terms JSON string and a local conllu file,
and expects a JSON-formatted result.

**Request:**

```bash
curl -X 'POST' \
  'http://localhost:5005/DefExAPI/definition_sentence_extraction' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'terms={"lemmatized_terms": ["neto masa", "bruto masa", "pasiven prevozen sredstvo"]}' \
  -F 'conllu_file=@rsdo5bimcla.conllu'
```

**Result:**


```json
{
  "definition_candidates": [
    "Neto masa je masa blaga brez embalaže .",
    "Bruto masa je skupna masa blaga z vso embalažo , razen zabojnikov in druge prevozne opreme .",
    "Pasivno prevozno sredstvo je sredstvo , ki se ob prehodu zunanje meje Unije prevaža z aktivnim prevoznim sredstvom , kot je določeno v PE 7 / 14 „ Identiteta aktivnega prevoznega sredstva ob prehodu meje “ ."
  ]
}
```

#### Command line utility

The following command will run the extractor on the given CoNLL-U file

```sh
python extract_defsent.py <conllu file>
```



###  Authors

Definition extractor wrapper, service code, and docker: [Vid Podpečan](vid.podpecan@ijs.si)

Definition extractor in Perl: [Senja Pollak](senja.pollak@ijs.si)


### License

MIT
