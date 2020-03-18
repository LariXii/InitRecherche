from dblp_parser_graph import *
import matplotlib.pyplot as plt
from networkx import nx
import networkx

dblp_path = 'resources/output.xml'

journals, impacts = parse_journal('resources/journals.xml')

#print(journals)

G = nx.DiGraph()
#n, e = parse_article_to_graph(dblp_path)
n, e = parse_art_aut_by_journals('resources/articles.xml', journals)

G.add_nodes_from(n)
G.add_edges_from(e)

#for u, v in G.edges():
#    print("Source : %s / Destination : %s" % (u, v))

#print(len(G.nodes()))

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

# --> Afficher l'ensemble des noeuds et les données leur correspondants.
#print(list(G.nodes().data()))

# --> Attribuer à chaque noeud article, son poids.

x = nx.classes.function.degree(G)
pattern = re.compile("journals/*", re.IGNORECASE)
poids_articles = []
for noeud in x :
    if pattern.match(noeud[0]) :
        poids_articles.append(noeud)
    else :
        continue
#print(poids_articles)
liste_auteurs = []


for n in G.nodes() :
    if G.nodes()[n]['parti'] == 'author' :
        liste_auteurs.append(n)
    else :
        continue

# --> Articles écrits par auteur.
auteur_article = dict()
for noeud in G :
    if G.nodes()[noeud]['parti'] == 'author' :
        #print("\nVoisin de {} est {}".format(noeud, list(G.neighbors(noeud))))
        auteur_article[noeud] = list(G.neighbors(noeud))
    else :
        continue

# --> Articles écrits pour quel journal
journal_article = dict()
for noeud in G :
    if G.nodes()[noeud]['parti'] == 'journal' :
        #print("\nVoisin de {} est {}".format(noeud, list(G.neighbors(noeud))))
        journal_article[noeud] = list(G.neighbors(noeud))
    else :
        continue

# --> Récupérer les impact factor de chaque Journal.

journal_impact = dict()
for noeud in G :
    if G.nodes()[noeud]['parti'] == 'journal' :
        journal_impact[noeud] = G.nodes()[noeud]['impact_factor']
    else :
        continue

# --> Attribuer à chaque article, un poids égale à l'impact factor de son journal.
liste_journaux = journal_impact.keys()
t = []
impact_article = dict()
for journal in liste_journaux :
    if journal in journal_article.keys() :
        impact_article[journal_impact[journal]] = journal_article[journal]
    else :
        continue



# --> Attribuer à chaque auteur un coeff. || ('Auteur' : Coefficient)
auteur_coef = dict()
nombre_articles = 0
somme_impact_articles = 0

#for impact in impact_article.values() :
#    for article in impact :
#        print("Article : {} est présent dans {}".format(article, impact))


for auteur in auteur_article.keys() : #L'auteur
    nombre_articles = len(auteur_article[auteur]) #Nombre d'articles ayant été écrits par l'auteur.
    for articles in auteur_article[auteur] : #Article par article

        for articles_impact_article in impact_article.values() : #Check si l'article est présent dans la liste où on a fait la correspondance impact - article
            if articles in articles_impact_article : #Si l'article a un impact, on le rajoute à la somme pour calculer le coeff.
                for cle in impact_article.keys() : #On parcourt la liste selon l'impact des articles.
                    if impact_article[cle] == articles_impact_article :
                        somme_impact_articles = somme_impact_articles + float(cle)
                        coeff = somme_impact_articles/nombre_articles #Le coeff de l'auteur est la somme des poids de ses articles/le nombre de ses articles.
                        auteur_coef[auteur] = coeff
                        somme_impact_articles = 0
                    else :
                        continue
            else :
                continue

list_nodes = dict()
for author in auteur_coef.keys() :
    for node in G.nodes() :
        if node == author :
            list_nodes[node] = auteur_coef[author]*5
            continue

difference = set(G.nodes().keys()) - set(list_nodes.keys())
for d in difference :
    list_nodes[d] = 1

options = {
    'node_color': color_map,
    #'node_size': 50,
    'line_color': 'grey',
    'linewidths': 0,
    'width': 0.1,
}


liste_des_noeuds = list(list_nodes.keys())
liste_des_poids = list(list_nodes.values())

pos = nx.spring_layout(G)
#nx.draw(G, pos, font_size=16, with_labels=False, **options)
nx.draw(G, pos, font_size=16, nodelist=liste_des_noeuds, node_size=[v * 100 for v in liste_des_poids], with_labels=True, **options)
#for p in pos:  # raise text positions
#    pos[p][1] += 0.07
#nx.draw_networkx_labels(G, pos)
plt.show()
