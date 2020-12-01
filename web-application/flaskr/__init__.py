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
    
    @app.route('/widoco')
    def widoco():
        return render_template('widoco.html')
    
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

        # Default SPARQL Query / competency question
        if (not customQuery and (not questionId or questionId < 1 or questionId > 12)):
            questionId = 1

        if customQuery:
            query = customQuery
        else:
            query = getQueryByCompetencyQuestionId(questionId)
        
        sparql = SPARQLWrapper(app.config.get("LOCAL_TRIPLESTORE"))
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparqlRes = sparql.query().convert()
        
        sparqlVars = []
        for var in sparqlRes['head']['vars']:
            if "Label" not in var:
                sparqlVars.append(var)

        return render_template('run-queries.html', questionId=questionId, sparqlQuery=query, sparqlRes=sparqlRes)

    return app

# Returns SPARQL defined for related competency question
def getQueryByCompetencyQuestionId(questionId):
    app = Flask(__name__, instance_relative_config=True, static_url_path='/assets')
    app.config.from_pyfile('settings.py')
    
    if questionId == 1:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX dbo: <http://dbpedia.org/ontology/> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

select ?Player ?Role  ?playerLabel ?roleLabel where {
    	?Player se:hasRole ?Role ;
    			se:goals 	?MostGoals .
    filter(?MostGoals = ?MaxGoals) .
    ?Player rdfs:label ?playerLabel . 
    ?Role rdfs:label ?roleLabel .
    {
select * where { 
    ?BestPlayer se:hasRole ?Role .
    ?BestPlayer se:goals  ?MostGoals .
    filter(xsd:int(?MostGoals) = ?MaxGoals)
    {
    select (max(xsd:int(?Goals)) as ?MaxGoals) where
        {
            ?Player se:goals ?Goals . 
        }
    }
}
    }
}
limit 1"""
    elif questionId == 2:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX dbo:<http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

select ?pointsTeamFaceRussia where {
    ?Team4 se:points ?pointsTeamFaceRussia . 
    {
        select distinct (?Team3 as ?Team4) where {
            ?Team3 ?p ?o .
            { 
                select ?Team3 where {
                    ?Team2 se:isOpponentOf ?Team3 .
                    ?Match2 se:hasTeam ?Team2 .
                    ?Match2 se:round "1"^^rdfs:Literal .
                    {
                        select * where {
                            ?Team1 se:isOpponentOf ?Team2 .
                            ?Match se:hasHomeTeam ?Team1 .
                            ?Team1 rdfs:label "Russia" .
                            ?Match se:round  "1"^^rdfs:Literal .
                        }
                    }
                }
            }
        }
    }
}"""
    elif questionId == 3:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

select  ?won (COUNT(?won) as ?numberOfTime) ?wonLabel  where {
    ?match se:round ?round .
    ?match se:hasAwayTeam ?awayTeam .
    ?match se:hasHomeTeam ?homeTeam .
    ?match se:homeTeamScore ?homeScore .
    ?match se:awayTeamScore ?awayScore . 
     BIND(
        IF(?homeScore > ?awayScore, ?homeTeam,
            IF(?homeScore < ?awayScore, ?awayTeam,"Draw")) AS ?won) .

       ?won rdfs:label ?wonLabel .

    filter(?won != "Draw" && ( ?round = "1"^^rdfs:Literal || ?round = "2"^^rdfs:Literal  || ?round ="3"^^rdfs:Literal) && lang(?wonLabel) = "en") .
}
group by ?won ?wonLabel
order by desc(?numberOfTime) limit 3"""
    elif questionId == 4:
        q = """
PREFIX se:<http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX owl:<http://www.w3.org/2002/07/owl#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xml:<http://www.w3.org/XML/1998/namespace>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>

select ?players ?playersLabel where { 
    ?matches rdf:type dbo:FootballMatch ;
          se:round "Semi Finals"^^rdfs:Literal ;
          se:hasTeam ?teams .
    
    ?players rdf:type dbo:SoccerPlayer ;
    		se:playsIn ?teams;
      		rdfs:label ?playersLabel;
    		se:hasRole <http://www.semanticweb.org/kde/ontologies/sport-events/Goalkeeper> .
}"""
    elif questionId == 5:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT (COUNT(DISTINCT(?club)) AS ?count)
WHERE {
    ?player se:hasNationality ?team.
    ?team rdfs:label "Spain".
    ?player se:playsIn ?club.
    ?club rdf:type dbo:SoccerClub.
}"""
    elif questionId == 6:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?team ?teamLabel WHERE {
    ?team rdfs:label ?teamLabel .
    filter(lang(?teamLabel) = "en") .
    {
        SELECT ?team WHERE {
            ?player se:hasNationality ?team .
            ?player se:goals ?goal .
        }
        
        GROUP BY ?team
        ORDER BY ASC((SUM(xsd:nonNegativeInteger(?goal))))
    }
}"""
    elif questionId == 7:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

select ?nationality ?nationalityLabel where { 
    ?player se:hasNationality ?nationality .
    ?nationality rdfs:label ?nationalityLabel .
    filter(lang(?nationalityLabel) = "en") .

    {
select * where { 
	?player se:assists ?numb 
}
ORDER BY DESC(?numb) LIMIT 10

 }
}"""
    elif questionId == 8:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?player ?playerLabel
WHERE {
    ?match se:scheduledAt ?date.
    FILTER (xsd:dateTime(?date) >= "2018-06-23T00:00:00"^^xsd:dateTime && xsd:dateTime(?date) < "2018-06-24T00:00:00"^^xsd:dateTime).
    ?match se:hasHomeTeam ?HomeTeam.
    ?player se:playsIn ?HomeTeam.
    ?player rdfs:label ?playerLabel.    
}"""
    elif questionId == 9:
        q = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>

select * where { 
    ?matches rdf:type dbo:FootballMatch ;
          se:round "Semi Finals"^^rdfs:Literal ;
          se:hasTeam ?teams .
    
    ?players rdf:type dbo:SoccerPlayer ;
    		se:playsIn ?teams ;
      		rdfs:label ?playersLabel .
}"""
    elif questionId == 10:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?player ?playerLabel
WHERE {
    ?player se:playsIn ?team .
    ?team rdf:type se:Team .
    ?player rdfs:label ?playerLabel
    {
        ?match se:awayTeamScore ?away_team_score.
        ?match se:homeTeamScore ?home_team_score.
        ?match se:hasAwayTeam ?away_team.
        ?match se:hasHomeTeam ?home_team.
        ?match se:scheduledAt ?time.
        ?match se:round "1"^^rdfs:Literal.
        BIND(
                IF(?away_team_score > ?home_team_score, ?away_team,
                IF(?away_team_score < ?home_team_score, ?away_team, "No one"))
            AS ?team
        ).
        FILTER(xsd:dateTime(?time) > "2018-06-16T00:00:00"^^xsd:dateTime && xsd:dateTime(?time) < "2018-06-22T00:00:00"^^xsd:dateTime).
    }
}"""
    elif questionId == 11:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>

select ?firstMatch ?city ?country where {
    ?firstMatch rdf:type dbo:FootballMatch ;
                se:scheduledAt ?scheduledAt ;
                se:tookPlaceIn ?stadium .
    
    ?stadium se:isIn ?city .
    ?city se:isIn ?country .
} order by ?scheduledAt limit 1"""
    elif questionId == 12:
        q = """
PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>

select ?lastMatch ?teams ?country ?population where {
    ?lastMatch se:hasTeam ?teams .
    ?teams rdfs:label ?teamsLabel .
    
    filter(lang(?teamsLabel) = "en") .
    
    SERVICE <http://dbpedia.org/sparql> {
		?country rdf:type dbo:Country ;
        	rdfs:label ?teamsLabel ;
        	dbo:populationTotal ?population .
        
    }
    
    {
        select ?lastMatch where {
            service <""" + app.config.get("LOCAL_TRIPLESTORE") + """> {
                ?lastMatch rdf:type dbo:FootballMatch ;
                            se:scheduledAt ?scheduledAt .
            }
        } order by desc(?scheduledAt) limit 1
    }
}"""
    else:
        q = ""
    
    return q