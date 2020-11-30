## Create local triplestore

We have been using GraphDB Free for this project. A local instance can be created with the following steps:
1. Install [GraphDB Free](https://www.ontotext.com/products/graphdb/graphdb-free/) on your local machine
2. Run GraphDB Workbench and open it with your web browser (default URL is `http://localhost:7200/`)
3. Go to Setup > Repositories > Create new repository
4. Give a name to the repository, select Ruleset `OWL-Max (Optimized)`, enter Base URL `http://www.semanticweb.org/kde/ontologies/sport-events#` and click Create repository
5. Go to Import > RDF and click on Upload RDF Files
6. Upload our triplestore into this repository: `data/triplestore.ttl`
7. Click on Import button of the uploaded file, leave parameters as default and click on Import button
8. Go to Setup > Repositories and click on the Link icon to copy the URL of the previously created repository
9. Use this URL as FLASK_TRIPLESTORE_URL environment variable (see below)

## Run the web application

This application runs using Python Flask.

```
$> cd web-application
$> pip install -r requirements.txt # Install Python dependencies
$> export FLASK_APP=flaskr
$> export FLASK_ENV=development
$> export FLASK_TRIPLESTORE_URL=<URL of the local triplestore>
$> flask run
```
Open local link given by Flask in your web browser.

Note: depending on your Python environment, you may need to run `$> pip3 install -r requirements.txt` instead of `$> pip install -r requirements.txt`.

## Run the Widoco documentation in standalone

### Using Python local server

```
$> cd documentation
$> python -m http.server 8000
```
Open http://127.0.0.1:8000/index-en.html in your web browser.

### Using PHP local server

```
$> cd documentation
$> php -S localhost:8000
```
Open http://127.0.0.1:8000/index-en.html in your web browser.