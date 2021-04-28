import extract1 as extract
from util import utils
import re

def replace_color(text, word, color):
    new_word = '\033[0' + color + 'm' + word + '\033[0m'
    len_w = len(word)
    len_t = len(text)
    for i in range(len_t - len_w, -1, -1):
        if text[i: i + len_w] == word:
            text = text[:i] + new_word + text[i + len_w:]
    return text


def is_in_each_other(list):
    le = len(list)
    for i in range(0, le):
        for j in range(0, le):
            if list[j].find(list[i]) >= 0 and i != j:
                return True
    return False


def replace_color_list(text, word, color):
    if is_in_each_other(word):
        return replace_color(text, word[0], color)
    for w in word:
        new_word = '\033[0' + color + 'm' + w + '\033[0m'
        len_w = len(w)
        len_t = len(text)
        for i in range(len_t - len_w, -1, -1):
            if text[i: i + len_w] == w:
                text = text[:i] + new_word + text[i + len_w:]
    return text


def selfsplite(line):
    tar = line.split('.')
    return tar

def get_color_text(path, obj):
    text = []
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            for sentence in re.split('[.?!;]', line):
                if not sentence or sentence == '\n':
                    continue
                tar_sentence = sentence+'.'
                sentence = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", sentence)
                for short in re.split('[,:]', sentence):
                    for slice in utils.strsplit(short):
                        slice = utils.stripSides(slice)
                        gene = obj.isListInSentence(obj.geneList,slice)
                        if not gene:
                            continue
                        sentence = sentence.replace('\t', ' ')  # 文本预处理
                        sentence = sentence.replace('et al.', ' ')
                        gene, rel, phen = obj.findRelation(gene, sentence)
                        if gene:
                            tar_sentence = replace_color(tar_sentence, gene, '32')
                        if rel:
                            tar_sentence = replace_color(tar_sentence, rel, '33')
                        if phen:
                            tar_sentence = replace_color_list(tar_sentence, phen, '35')
                text.append(tar_sentence)

    return text


if __name__ == '__main__':
    print('*-- welcome --*')
    path = './data/paper_test.txt'
    obj = extract.DiseaseExtractor(paperPath=path, isNeo4j=False)
    # obj.extract()
    print('*-- text follows --*')

    s = '\n*-- green is genotype, yellow is relationship, purple is phenotype --*\n\n'
    s = replace_color(s, 'green', '32')
    s = replace_color(s, 'yellow', '33')
    s = replace_color(s, 'purple', '35')

    print(s)

    text = get_color_text(path, obj)
    for t in text:
        print(t.strip())

    obj.nlp.close()
    print('\n~bye bye~\n')
