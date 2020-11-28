from SPARQLWrapper import SPARQLWrapper, JSON, N3
from rdflib import Graph

# sparql = SPARQLWrapper("http://dbpedia.org/sparql")
# sparql.setQuery("""
#     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#     SELECT ?label
#     WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }
# """)
# sparql.setReturnFormat(JSON)
# results = sparql.query().convert()

# for result in results["results"]["bindings"]:
#     print(result["label"]["value"])

# print('---------------------------')

# for result in results["results"]["bindings"]:
#     print('%s: %s' % (result["label"]["xml:lang"], result["label"]["value"]))

sparql = SPARQLWrapper("http://dbpedia.org/sparql")

sparql.setQuery("""
    DESCRIBE <http://dbpedia.org/resource/Asturias>
""")

sparql.setReturnFormat(N3)
results = sparql.query().convert()
g = Graph()
g.parse(data=results, format="n3")
print(g.serialize(format='n3'))