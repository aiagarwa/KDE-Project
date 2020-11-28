import os
from flask import Flask, render_template, request, redirect
from SPARQLWrapper import SPARQLWrapper, JSON, N3
import rdflib

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, static_url_path='/assets')
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import dashboard
    app.register_blueprint(dashboard.bp)
    app.add_url_rule('/', endpoint='index')

    # a simple page that says hello
    @app.route('/')
    def index():
        return redirect('/competency-questions?id=1')

    @app.route('/competency-questions')
    def competency():
        # sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        # # sparql.setQuery("""
        # #     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        # #     SELECT ?label
        # #     WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }
        # # """)
        # sparql.setQuery("""
        #      select * where { 
        #          ?s ?p ?o .
        #      }
        # """)
        # sparql.setReturnFormat(JSON)
        # sparqlRes = sparql.query().convert()
        # print(sparqlRes)
        
        questionId = int(request.args['id'])
        if (not questionId):
            questionId = 1

        # n = rdflib.Namespace("http://www.semanticweb.org/kde/ontologies/sport-events")
        # print(n)

        # g = rdflib.ConjunctiveGraph('SPARQLStore')
        # g.open("http://dbpedia.org/sparql")
        # sparqlRes = g.query(
        #     """
        #     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        #     SELECT ?label
        #     WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label
        #     """
        # )


        queryString = "SELECT * WHERE { ?s ?p ?o. }"
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")

        sparql.setQuery(queryString)
        ret = sparql.query()
        print(ret)


        from rdflib.namespace import FOAF, NamespaceManager
        g = rdflib.Graph()
        g.load('flaskr/static/KDE_SE_RDF.ttl', format="turtle")
        n = rdflib.Namespace("http://www.semanticweb.org/kde/ontologies/sport-events#")
        g.bind('se', n)
        g.parse(data = '<urn:a> <urn:p> <urn:b>.', format='n3')
        sparqlRes = g.query(
            """
            select * where { 
                ?s ?p se:Player .
            }
            """
        )

        return render_template('dashboard/competency-questions.html', questionId=questionId, sparqlRes=sparqlRes)

    return app