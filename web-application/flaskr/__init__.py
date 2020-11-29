import os
from flask import Flask, render_template, request, redirect
from SPARQLWrapper import SPARQLWrapper, JSON

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, static_url_path='/assets')
    app.config.from_pyfile('settings.py')

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

    # from . import dashboard
    # app.register_blueprint(dashboard.bp)
    app.add_url_rule('/', endpoint='index')

    @app.route('/')
    def index():
        return render_template('home.html')

    @app.route('/reports')
    def reports():
        return render_template('reports.html')
    
    @app.route('/help')
    def help():
        return render_template('help.html')

    @app.route('/run-queries', methods=['GET','POST'])
    def runQueries():
        # Custom SPARQL query
        if request.method == 'POST' and "sparql" in request.form:
            customQuery = request.form["sparql"]
        else:
            customQuery = None

        # Pre-defined queries that answer competency questions
        if ("id" in request.args):
            questionId = int(request.args['id'])
        else:
            questionId = None

        if (not customQuery and (not questionId or questionId < 1 or questionId > 11)):
            questionId = 1
        
        if questionId == 1:
            q = """
select ?c where {
    ?s se:hasNationality ?c .
    {
        select ?s where {
            ?s se:Goals ?o .
        }
        ORDER BY DESC(?o) LIMIT 1
    }
}"""
        elif questionId == 2:
            q = """
select ?player ?playerLabel ?team ?teamLabel where {
    ?player se:hasNationality ?team . {
        select ?team where {
            ?team se:Points ?o .
        }
        ORDER BY DESC(?o) LIMIT 1
    }
    ?player rdfs:label ?playerLabel .
    ?team rdfs:label ?teamLabel .
}"""
        elif questionId == 3:
            q = """
select ?team (COUNT(?team) as ?numberOfTime) ?teamLabel  where {
    ?match se:RoundNumber ?round .
    ?match se:hasAwayTeam ?awayTeam .
    ?match se:hasHomeTeam ?homeTeam .
    ?match se:HomeTeamScore ?homeScore .
    ?match se:AwayTeamScore ?awayScore . 
    BIND(
        IF(?homeScore > ?awayScore, ?homeTeam,
            IF(?homeScore < ?awayScore, ?awayTeam,"Draw")) AS ?team) .

    filter(?team != "Draw" && ( ?round = "1" || ?round = "2"  || ?round ="3")) .
    ?team rdfs:label ?teamLabel .
}
group by ?team ?teamLabel
order by desc(?numberOfTime) limit 3"""
        elif questionId == 4:
            q = """
select ?players ?playersLabel where {
    ?matches rdf:type se:Match ;
        se:RoundNumber "Semi Finals" ;
        se:hasAwayTeam|se:hasHomeTeam ?teams .

    ?players rdf:type se:Player ;
            se:playsInTeam ?teams;
            rdfs:label ?playersLabel;
            se:hasRole <http://www.semanticweb.org/kde/ontologies/sport-events/Goalkeeper> .
}"""
        elif questionId == 5:
            q = """
SELECT (COUNT(DISTINCT(?Club)) AS ?count) WHERE {
    ?player se:hasNationality ?team.
    ?team rdfs:label "Spain".
    ?player se:playsInClub ?Club.
}"""
        elif questionId == 6:
            q = """
SELECT ?team ?teamLabel 
WHERE {
    ?team rdfs:label ?teamLabel.{
        SELECT ?team
        WHERE {
        ?player se:hasNationality ?team.
        ?player se:Goals ?goal.
            FILTER(?goal != "-").
        }
        GROUP BY ?team
        ORDER BY ASC((SUM(xsd:integer(?goal))))
    }
}"""
        elif questionId == 7:
            q = """
select ?nationality where { 
    ?player se:hasNationality ?nationality .{
        select * where { 
            ?player se:Assists ?numb 
        }
        ORDER BY DESC(?numb) LIMIT 10
    }
}"""
        elif questionId == 8:
            q = """
SELECT * WHERE { VALUES ?result { <http://example.org/TO-DO> } }"""
        elif questionId == 9:
            q = """
select ?players ?playersLabel where { 
    ?matches rdf:type se:Match ;
        se:RoundNumber "Semi Finals" ;
        se:hasAwayTeam|se:hasHomeTeam ?teams .
    
    ?players rdf:type se:Player ;
            se:playsInTeam ?teams;
            rdfs:label ?playersLabel; .
}"""
        elif questionId == 10:
            q = """
SELECT ?player ?playerLabel
WHERE {
    ?player rdfs:label ?playerLabel.
    ?player se:playsInTeam ?team.{
        ?match se:AwayTeamScore ?away_team_score.
        ?match se:HomeTeamScore ?home_team_score.
        ?match se:hasAwayTeam ?away_team.
        ?match se:hasHomeTeam ?home_team.
        ?match se:ScheduledAt ?time.
        ?match se:RoundNumber "1".
        BIND(
            IF(?away_team_score > ?home_team_score, ?away_team, 
                IF(?away_team_score < ?home_team_score, ?home_team, "No one"))
            AS ?team
        ).
        FILTER(?time > "16-06-2018" && ?time < "22-06-2018").
    }
}"""
        elif questionId == 11:
            q = """
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT *
WHERE {
    SERVICE <""" + app.config.get("LOCAL_TRIPLESTORE") + """> {
        ?player se:playsInTeam ?team .
        ?player rdfs:label ?playerLabel .
        ?team rdfs:label ?teamLabel .
    }
    
    SERVICE <http://dbpedia.org/sparql> {
        ?country rdf:type dbo:Country ;
            rdfs:label ?teamLabel ;
            dbo:populationTotal ?population .
        
    }
} LIMIT 10"""
        
        if customQuery:
            query = customQuery
        else:
            query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>""" + q

        sparql = SPARQLWrapper(app.config.get("LOCAL_TRIPLESTORE"))
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparqlRes = sparql.query().convert()
        
        sparqlVars = []
        for var in sparqlRes['head']['vars']:
            if "Label" not in var:
                sparqlVars.append(var)

        return render_template('run-queries.html', 
                questionId=questionId, sparqlQuery=query,
                sparqlRes=sparqlRes, sparqlVars=sparqlVars)

    return app