import os
from flask import Flask, render_template, request, redirect
from SPARQLWrapper import SPARQLWrapper, JSON

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
        questionId = int(request.args['id'])
        if (not questionId or questionId < 1 or questionId > 10):
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
            }
            """
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
            }
            """
        elif questionId == 3:
            q = """
            select  ?won (COUNT(?won) as ?numberOfTime) where {
                ?match se:RoundNumber ?round .
                ?match se:hasAwayTeam ?awayTeam .
                ?match se:hasHomeTeam ?homeTeam .
                ?match se:HomeTeamScore ?homeScore .
                ?match se:AwayTeamScore ?awayScore . 
                BIND(
                    IF(?homeScore > ?awayScore, ?homeTeam,
                        IF(?homeScore < ?awayScore, ?awayTeam,"Draw")) AS ?won) .
            
                filter(?won != "Draw" && ( ?round = "1" || ?round = "2"  || ?round ="3")) .
            }
            group by ?won
            order by desc(?numberOfTime) limit 3
            """
        elif questionId == 4:
            q = """
            select ?players where { 
                ?matches rdf:type se:Match ;
                    se:RoundNumber "Semi Finals" ;
                    se:hasAwayTeam|se:hasHomeTeam ?teams .
                
                ?players rdf:type se:Player ;
                        se:playsInTeam ?teams; 
                        se:hasRole <http://www.semanticweb.org/kde/ontologies/sport-events/Goalkeeper> .
            }
            """
        elif questionId == 5:
            q = """
            SELECT (COUNT(DISTINCT(?Club)) AS ?count) WHERE {
                ?player se:hasNationality ?team.
                ?team rdfs:label "Spain".
                ?player se:playsInClub ?Club.
            }
            """
        elif questionId == 6:
            q = """
            SELECT ?team WHERE {
                    ?player se:hasNationality ?team.
                    ?player se:Goals ?goal.
                        FILTER(?goal != "-").
                }
            GROUP BY ?team
            ORDER BY ASC((SUM(xsd:integer(?goal)))) LIMIT 1
            """
        elif questionId == 7:
            q = """
            select ?nationality where { 
                ?player se:hasNationality ?nationality . {
                select * where { 
                    ?player se:Assists ?numb 
                }
                ORDER BY DESC(?numb) LIMIT 10

                }
            }
            """
        elif questionId == 8:
            q = ""
            print("[TODO]")
        elif questionId == 9:
            q = """
            select ?players where { 
                ?matches rdf:type se:Match ;
                    se:RoundNumber "Semi Finals" ;
                    se:hasAwayTeam|se:hasHomeTeam ?teams .
                
                ?players rdf:type se:Player ;
                        se:playsInTeam ?teams .
            }
            """
        elif quetionId == 10:
            q = """
            SELECT ?player WHERE {
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
                    FILTER(?time > "16/06/2018" && ?time < "22/06/2018").
                } 
            } 
            """
        
        sparql = SPARQLWrapper("http://192.168.1.47:7200/repositories/test")
        sparql.setQuery("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX se: <http://www.semanticweb.org/kde/ontologies/sport-events#>
            """ + q)
        sparql.setReturnFormat(JSON)
        sparqlRes = sparql.query().convert()
        
        sparqlVars = []
        for var in sparqlRes['head']['vars']:
            if "Label" not in var:
                sparqlVars.append(var)

        return render_template('dashboard/competency-questions.html', questionId=questionId, sparqlRes=sparqlRes, sparqlVars=sparqlVars)

    return app