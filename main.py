from dblp_parser_graph import *
import matplotlib.pyplot as plt
from networkx import nx

dblp_path = 'resources/output.xml'

journals, impacts = parse_journal('resources/journals.xml')

print(journals)

G = nx.DiGraph()
#n, e = parse_article_to_graph(dblp_path)
n, e = parse_art_aut_by_journals('resources/articles.xml', journals)

G.add_nodes_from(n)
G.add_edges_from(e)

#for u, v in G.edges():
#    print("Source : %s / Destination : %s" % (u, v))

print(len(G.nodes()))

#for u, v, action in G.edges(data='action'):
#    if action is not None:
#        print("(%s) [%s] (%s)" % (u, action, v))

color_map = []

for n in G.nodes():
    if G.nodes[n]['parti'] == 'author':
        color_map.append('red')
    elif G.nodes[n]['parti'] == 'article':
        color_map.append('blue')
    else:
        color_map.append('green')


for c, v in impacts.items():
    try:
        G.nodes[c]['impact_factor'] = v
    except KeyError:
        continue

print(list(G.nodes().data()))

options = {
    'node_color': color_map,
    'node_size': 50,
    'line_color': 'grey',
    'linewidths': 0,
    'width': 0.1,
}

pos = nx.spring_layout(G)
nx.draw(G, pos, font_size=16, with_labels=False, **options)
#for p in pos:  # raise text positions
#    pos[p][1] += 0.07
#nx.draw_networkx_labels(G, pos)
plt.show()
