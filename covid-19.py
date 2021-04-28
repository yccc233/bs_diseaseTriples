from py2neo import *

if __name__ == '__main__':
    graph = None
    try:
        graph = Graph("http://localhost:7474", auth=("neo4j", "1111"))
    except:
        print('*-- warning: please open your neo4j server --*')
        exit(1)
    matcher = NodeMatcher(graph)

    covid = matcher.match('main', name='COVID-19').first()
    if not covid:
        covid = Node('main', name='COVID-19')
        graph.create(covid)
        print('*-- create a main node \'COVID-19\' success --*')
    genes = matcher.match('gene')
    if not genes:
        print('*-- no result in genes --*')
    relation = 'have'
    for gene in genes:
        r = Relationship(covid,relation,gene)
        s = covid | gene | r
        graph.create(s)
    print('*-- work done --*')