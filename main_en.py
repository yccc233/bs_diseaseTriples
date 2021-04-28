import extract1 as extract
import re
from py2neo import *

geneList = []
phenList = []
covidList = []
proteinList = []
proteinGeneList = []
path = './data/paper_2.txt'

geneColor = '32'
phenColor = '35'
covidColor = '33'
proteinColor = '34'


def init():
    with open('./data/gene.txt', 'r') as file:
        genes_en = file.readlines()
        for g in genes_en:
            g = g.strip()
            if g and g not in geneList:
                geneList.append(g)
    with open('./data/phen_en.txt', 'r') as file:
        phens_en = file.readlines()
        for p in phens_en:
            p = p.strip()
            if p and p not in phenList:
                phenList.append(p.lower())
    with open('./data/covid_en.txt', 'r') as file:
        covid_en = file.readlines()
        for c in covid_en:
            c = c.strip().upper()
            if c and c not in covidList:
                covidList.append(c.upper())
    with open('./data/protein_en.txt','r') as file:
        protein_en = file.readlines()
        for p in protein_en:
            p = p.strip()
            if p and p not in proteinList:
                proteinList.append(p)
    with open('./data/gene_protein_tran.txt', 'r') as file:
        proteinGene_en = file.readlines()
        for pg in proteinGene_en:
            pg = pg.strip()
            if pg and pg not in proteinGeneList:
                proteinGeneList.append(pg)


def isInProteinList(protein):
    for pro in proteinList:
        if pro.lower() == protein.lower():
            return True
    return False


def getGeneEntities(tags):
    genes = []
    for tag in tags:
        if tag[1] == 'NNP' and tag[0] in geneList and tag[0] not in genes:
            genes.append(tag[0])
        else:
            if tag[1] == 'NN':
                tmp = tag[0].upper()
                if tmp in geneList and tmp not in genes:
                    genes.append(tag[0])
    return genes


def getProteinEntities(tags):
    proteins = []
    flag = len(tags)-1
    while flag >= 0:
        tag = tags[flag]
        if tag[1] == 'NN':
            protein = tag[0]
            if flag < len(tags)-1 and ( tags[flag+1][1] == 'CD' or tags[flag+1][1] == 'PRP'):
                protein = protein + ' ' + tags[flag+1][0]
            flag = flag-1
            while flag >= 0 and (tags[flag][1] == 'NN' or tags[flag][1] == 'PRP' or tags[flag][1] == 'VBG' or tags[flag][1] == 'NNP'):
                protein = tags[flag][0] + ' ' + protein
                flag = flag-1
            Is = isInProteinList(protein)
            if Is and protein not in proteins:
                proteins.append(protein)
        else:
            flag = flag-1
    return proteins


def getPhenEntitiies(tags):
    phens = []
    for flag in range(len(tags)):
        tag = tags[flag]
        if tag[1] == 'NN':
            phen = tag[0]
            for i in range(flag - 1, 0, -1):
                if tags[i][1] == 'JJ' or tags[i][1] == 'IN' or tags[i][1] == 'NN':
                    phen = tags[i][0] + ' ' + phen
                else:
                    break
            if phen.lower() in phenList and phen not in phens:
                phens.append(phen)
    return phens


def getRelation(words):
    negs = [
        'not',
        'never',
        'cannot'
    ]
    for word in words:
        if word in negs:
            return False
    return True


def isCovids(graph):
    covids = []
    sentenceUp = graph.upper().replace('-', '_')
    for covid in covidList:
        flag = sentenceUp.find(covid)
        if flag >= 0:
            covids.append(graph[flag:flag + len(covid)])
    return covids


def isSentence(sentence):
    if not sentence:
        return False
    if sentence == '\n' or sentence == '\t':
        return False
    if sentence == ' ' or sentence == '':
        return False
    return True


def handleSentenceByGraph(graph):
    sentences = re.split('[.?!;]', graph)
    if sentences[-1] == '':
        sentences.remove(sentences[-1])
    for i in range(0, len(sentences)):
        sentences[i] = sentences[i].strip() + '. '
    return sentences


def handleParagraph(text):
    text = text.replace('\t', '')
    paragraphs = text.split('\n')
    return paragraphs


def replaceByColor(sentence, tarWord, color):
    new_word = '\033[0' + color + 'm' + tarWord + '\033[0m'
    len_w = len(tarWord)
    len_t = len(sentence)
    for i in range(len_t - len_w, -1, -1):
        if sentence[i: i + len_w] == tarWord:
            sentence = sentence[:i] + new_word + sentence[i + len_w:]
    return sentence


def proteinToGene(protein):
    for pg in proteinGeneList:
        if pg.find(protein) > 0 :
            return pg.split(':')[0]
    return None


def doColor(obj):
    s = '\n*-- green is genotype, blue is protein, purple is phenotype, yellow is COVID-19 --*\n\n'
    s = replaceByColor(s, 'green', geneColor)
    s = replaceByColor(s, 'purple', phenColor)
    s = replaceByColor(s, 'yellow', covidColor)
    s = replaceByColor(s, 'blue', proteinColor)
    print(s)
    triple_s = []
    with open(path, 'r') as file:
        totalText = file.read()
    color_text = ''
    for graph in handleParagraph(totalText):
        graph = graph.replace('et al.', ' ')
        sentences = handleSentenceByGraph(graph)
        for sentence in sentences:
            if not isSentence(sentence):
                continue
            sentence = sentence.replace('-', '_')
            tags = obj.nlp.pos_tag(sentence.replace('%', ''))
            genes = getGeneEntities(tags)
            phens = getPhenEntitiies(tags)
            covids = isCovids(sentence)
            proteins = getProteinEntities(tags)
            rel = getRelation(tags)
            for gene in genes:
                sentence = replaceByColor(sentence, gene, geneColor)
            for phen in phens:
                sentence = replaceByColor(sentence, phen, phenColor)
            for covid in covids:
                sentence = replaceByColor(sentence, covid, covidColor)
            for protein in proteins:
                sentence = replaceByColor(sentence, protein, proteinColor)
            if proteins is not []:
                for protein in proteins:
                    gene = proteinToGene(protein)
                    if gene not in genes:
                        genes.append(gene)
            if rel:
                for gene in genes:
                    if len(phens) > 0:
                        for phen in phens:
                            triple = [gene.upper(), phen]
                            if triple not in triple_s:
                                triple_s.append(triple)
            if len(covids) > 0:
                for gene in genes:
                    triple = ['COVID-19', gene.upper()]
                    if triple not in triple_s:
                        triple_s.append(triple)
                for phen in phens:
                    triple = ['COVID-19', phen]
                    if triple not in triple_s:
                        triple_s.append(triple)
            color_text = color_text + sentence
        color_text = color_text + '\n'
    print(color_text)
    return triple_s


def insertNeo4j(triple_s):
    graph = None
    try:
        graph = Graph("http://localhost:7474", auth=("neo4j", "1111"))
    except Exception as e:
        print('*-- warning: %s --*' % e)
        exit(1)
    matcher = NodeMatcher(graph)
    covid = matcher.match('covid', name='COVID-19').first()
    if not covid:
        covid = Node('covid', name='COVID-19')
        graph.create(covid)
    for triple in triple_s:
        if triple[0] == 'COVID-19':
            if triple[1] in geneList:
                sub = matcher.match('gene', name=triple[1]).first()
                if not sub:
                    sub = Node('gene', name=triple[1])
                r = Relationship(covid, 'related', sub)
                s = covid | sub | r
                graph.create(s)
            else:
                if triple[1] in phenList:
                    sub = matcher.match('phen', name=triple[1]).first()
                    if not sub:
                        sub = Node('phen', name=triple[1])
                    r = Relationship(covid, 'related', sub)
                    s = covid | sub | r
                    graph.create(s)
                else:
                    print('*-- node %s-%s cannot find home! --*' % (triple[0], triple[1]))
        else:
            gene = matcher.match('gene', name=triple[0]).first()
            if not gene:
                gene = Node('gene', name=triple[0])
            phen = matcher.match('phen', name=triple[1]).first()
            if not phen:
                phen = Node('phen', name=triple[1])
            r = Relationship(gene, 'related', phen)
            s = gene | phen | r
            graph.create(s)
    print('\n*-- insert nto neo4j success --*\n')


def test(obj):
    # sentence = 'SARS-CoV-2, severe acute respiratory syndrome coronavirus-2; COVID-19, coronavirus disease 2019; ACE, angiotensin-converting enzyme;'
    #
    # # sentence = 'angiotensin I converting enzyme 1, dipeptidyl carboxypeptidase I, TNF_alpha convertase enzyme'
    # sentence = sentence.replace('-','_')
    # print(obj.nlp.pos_tag(sentence))
    # print(getProteinEntities(obj.nlp.pos_tag(sentence)))
    sentence = 'In contrast, less common signs at the time of hospital admission include diarrhea, hemoptysis, and shortness of breath'
    print(obj.nlp.pos_tag(sentence))
    print(getPhenEntitiies(obj.nlp.pos_tag(sentence)))

if __name__ == '__main__':
    obj = extract.DiseaseExtractor(paperPath=path)
    init()
    # test(obj)
    with open(path, 'r') as f:
        total_text = f.read()
    triples = doColor(obj)
    print('\n', triples)
    # insertNeo4j(triples)
    obj.nlp.close()
    print('*-- bye~bye --*')
