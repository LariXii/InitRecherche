from lxml import etree
from datetime import datetime
from networkx import nx
import csv
import codecs
import ujson
import re


# all of the element types in dblp
all_elements = {"article", "inproceedings", "proceedings", "book", "incollection", "phdthesis", "mastersthesis", "www"}
# all of the feature types in dblp
all_features = {"address", "author", "booktitle", "cdrom", "chapter", "cite", "crossref", "editor", "ee", "isbn",
                "journal", "month", "note", "number", "pages", "publisher", "school", "series", "title", "url",
                "volume", "year"}


def log_msg(message):
    """Produce a log with current time"""
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)


def context_iter(dblp_path, dtd_validation=True):
    """Create a dblp data iterator of (event, element) pairs for processing"""
    return etree.iterparse(source=dblp_path, dtd_validation=dtd_validation, load_dtd=True)  # required dtd


def clear_element(element):
    """Free up memory for temporary element tree after processing the element"""
    element.clear()
    while element.getprevious() is not None:
        del element.getparent()[0]


def extract_feature(elem, features, include_key=False):
    """Extract the value of each feature"""
    if include_key:
        attribs = {'key': [elem.attrib['key']]}
    else:
        attribs = {}
    for feature in features:
        attribs[feature] = []
    for sub in elem:
        if sub.tag not in features:
            continue
        if sub.tag == 'title':
            text = re.sub("<.*?>", "", etree.tostring(sub).decode('utf-8')) if sub.text is None else sub.text
        elif sub.tag == 'pages':
            text = count_pages(sub.text)
        else:
            text = sub.text
        if text is not None and len(text) > 0:
            attribs[sub.tag] = attribs.get(sub.tag) + [text]
    return attribs


def count_pages(pages):
    """Borrowed from: https://github.com/billjh/dblp-iter-parser/blob/master/iter_parser.py
    Parse pages string and count number of pages. There might be multiple pages separated by commas.
    VALID FORMATS:
        51         -> Single number
        23-43      -> Range by two numbers
    NON-DIGITS ARE ALLOWED BUT IGNORED:
        AG83-AG120
        90210H     -> Containing alphabets
        8e:1-8e:4
        11:12-21   -> Containing colons
        P1.35      -> Containing dots
        S2/109     -> Containing slashes
        2-3&4      -> Containing ampersands and more...
    INVALID FORMATS:
        I-XXI      -> Roman numerals are not recognized
        0-         -> Incomplete range
        91A-91A-3  -> More than one dash
        f          -> No digits
    ALGORITHM:
        1) Split the string by comma evaluated each part with (2).
        2) Split the part to subparts by dash. If more than two subparts, evaluate to zero. If have two subparts,
           evaluate by (3). If have one subpart, evaluate by (4).
        3) For both subparts, convert to number by (4). If not successful in either subpart, return zero. Subtract first
           to second, if negative, return zero; else return (second - first + 1) as page count.
        4) Search for number consist of digits. Only take the last one (P17.23 -> 23). Return page count as 1 for (2)
           if find; 0 for (2) if not find. Return the number for (3) if find; -1 for (3) if not find.
    """
    cnt = 0
    for part in re.compile(r",").split(pages):
        subparts = re.compile(r"-").split(part)
        if len(subparts) > 2:
            continue
        else:
            try:
                re_digits = re.compile(r"[\d]+")
                subparts = [int(re_digits.findall(sub)[-1]) for sub in subparts]
            except IndexError:
                continue
            cnt += 1 if len(subparts) == 1 else subparts[1] - subparts[0] + 1
    return "" if cnt == 0 else str(cnt)


def parse_entity_gc(dblp_path, type_name, features=None, include_key=False):
    """Parse specific elements according to the given type name and features"""
    log_msg("PROCESS: Start parsing for {}...".format(str(type_name)))
    assert features is not None, "features must be assigned before parsing the dblp dataset"
    edges = []
    nodes = []
    try:
        for _, elem in context_iter(dblp_path):
            if elem.tag in type_name:
                #print(elem.tag, elem.attrib['key'])
                nodes.append((elem.attrib['key'], {'parti': elem.tag}))
                for sub in elem:
                    if sub.tag not in features:
                        continue
                    nodes.append((sub.text, {'parti': sub.tag}))
                    edges.append((sub.text, elem.attrib['key']))
                    #print(sub.tag, sub.text)
            elif elem.tag not in all_elements:
                continue
    except StopIteration:
        print("Fin du fichier")
    return nodes, edges


def parse_article(dblp_path, include_key=False):
    type_name = ['article']
    features = ['author']
    return parse_entity_gc(dblp_path, type_name, features, include_key=include_key)


def parse_journal(dblp_path):
    """Fonction retournant un tableau de journal contenu dans un fichier xml passé en paramètre"""
    type_name = ['journal']
    log_msg("PROCESS: Start parsing for {}...".format(str(type_name)))
    journals = set()
    impacts = {}
    for _, elem in context_iter(dblp_path, False):
        if elem.tag in type_name:
            journals.add(elem.text)
            impacts[elem.text] = elem.attrib['impact_factor']
        elif elem.tag not in all_elements:
            continue
        clear_element(elem)
    return journals, impacts


def parse_art_aut_by_journals(dblp_path, journals, features=None):
    """Fonction qui permet de récupèrer les articles et auteurs qui ont publié dans une liste de journaux prédéfini"""
    """Parse specific elements according to the given type name and features"""
    type_name = ['article']
    features = ['author']
    log_msg("PROCESS: Start parsing for {}...".format(str(type_name)))
    assert features is not None, "features must be assigned before parsing the dblp dataset"
    edges = []
    nodes = []
    dict_journals = {}
    for j in journals:
        dict_journals[j] = 0
    try:
        for _, elem in context_iter(dblp_path, False):
            if elem.tag in type_name:
                j = elem.findall('journal')
                if len(j[0].text) > 0:
                    if j[0].text in journals:
                        dict_journals[j[0].text] += 1
                        if dict_journals[j[0].text] < 11:
                            for sub in elem:
                                if sub.tag not in features:
                                    continue
                                #Ajout des noeuds des auteurs
                                nodes.append((sub.text, {'parti': sub.tag}))
                                #Ajout des liens auteurs/articles
                                edges.append((sub.text, elem.attrib['key']))
                                # print(sub.tag, sub.text)
                            #Ajout des noeuds articles
                            nodes.append((elem.attrib['key'], {'parti': elem.tag}))
                            #Ajout des noeuds journals
                            nodes.append((j[0].text, {'parti': j[0].tag}))                            
                            #Ajout des liens articles/journals
                            edges.append((j[0].text, elem.attrib['key']))
            elif elem.tag not in all_elements:
                continue
    except StopIteration:
        print("Fin du fichier")
    print(dict_journals)
    return nodes, edges


def parse_article_to_graph(dblp_path):
    type_name = ['article']
    features = ['author']
    """Parse specific elements according to the given type name and features"""
    log_msg("PROCESS: Start parsing for {}...".format(str(type_name)))
    assert features is not None, "features must be assigned before parsing the dblp dataset"
    edges = []
    nodes = []
    try:
        for _, elem in context_iter(dblp_path):
            if elem.tag in type_name:
                j = elem.findall('journal')
                if len(j[0].text) > 0:
                    # Ajout des noeuds articles
                    nodes.append((elem.attrib['key'], {'parti': elem.tag}))
                    # Ajout des noeuds journals
                    nodes.append((j[0].text, {'parti': j[0].tag}))
                    # Ajout des liens articles/journals
                    edges.append((j[0].text, elem.attrib['key']))
                    for sub in elem:
                        if sub.tag not in features:
                            continue
                        # Ajout des noeuds des auteurs
                        nodes.append((sub.text, {'parti': sub.tag}))
                        # Ajout des liens auteurs/articles
                        edges.append((sub.text, elem.attrib['key']))
            elif elem.tag not in all_elements:
                continue
    except StopIteration:
        print("Fin du fichier")
    return nodes, edges
