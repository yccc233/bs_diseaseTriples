import re
import os
import json

from util import utils

from py2neo import *
from stanfordcorenlp import StanfordCoreNLP


class DiseaseExtractor:
    def __init__(self, paperPath='', isNLP=True, isNeo4j=False):
        self.diseaseFilePath = './data/gene_result.txt'
        if not os.path.exists(self.diseaseFilePath):
            print('!-- error : path:%s not exist --!' % self.diseaseFilePath)
            exit(1)

        self.paperPath = ''
        if paperPath == '' or paperPath is None:
            self.paperPath = './data/paper_test.txt'
        else:
            self.paperPath = paperPath
        if not os.path.exists(self.paperPath):
            print('!-- error : path:%s not exist --!' % self.paperPath)
            exit(1)
        self.geneList = []
        self.getGeneName()
        self.nlp = None
        self.graph = None
        self.matcher = None
        # 打开NLP服务
        if isNLP:
            self.nlp = StanfordCoreNLP(r'/Users/yucheng/Applications/python/package/stanford_nlp', timeout=100)
        # 连接neo4j数据库
        if isNeo4j:
            self.graph = Graph("http://localhost:7474", auth=("neo4j", "1111"))  # 这里是数据库的用户名和密码，按照自己的真实情况填写
            self.matcher = NodeMatcher(self.graph)
        print('*-- DiseaseExtractor init success! (including geneList)--*\n')

    def extract(self, isNeo4j=False):
        with open(self.paperPath, 'r', encoding='utf-8') as f:  # 读取要抽取的文本
            content = f.read()  # 读取该文件的全部文本
            content = content.replace('\n', ' ')  # 文本预处理
            content = content.replace('\t', '')
            # content = content.replace('-', '_')
            content = content.replace('et al.', ' ')

            sentenceList = re.split('[.?!;]',content)  # 以.?!;作为分隔符，将文本转化成一个list


            print('-- The relationship of triples is as follows --\n')
            for longSentence in sentenceList:
                # 过滤掉括号内的内容，降低噪声影响
                longSentence = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", longSentence)

                for shortsentence in longSentence.split(','):  # 以.作为分隔符，继续将小文本转为list
                    sentences = utils.strsplit(shortsentence)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        geneName = self.isListInSentence(self.geneList, sentence)  # 获取句子中包含的 基因型数据

                        if geneName:  # 如果包含基因型数据
                            rels = self.findRelation(geneName, sentence)  # 找出三元组关系
                            if rels is None :  # 如果三元组非空，则将结果保存在neo4j中
                                continue
                            for rell in rels:
                                if isNeo4j:
                                    self.saveInNeo(rell[0], rell[1], rell[2])
                                print('(' + rell[0] + ') - (' + rell[1] + ') -> (' + rell[2] + ')')
        print('\n-- End of presentation --')
        self.nlp.close()

    # 从./data/gene_result.txt中获取基因型数据
    def getGeneName(self):
        with open(self.diseaseFilePath, 'r', encoding='utf-8') as f:  # 读取./data/gene_result.txt
            lines = f.readlines()
            resList = []
            for line in lines:  # 遍历每一行数据
                line = line.strip().replace(' ', '')  # 去空格
                if not line:
                    continue
                if line[0].isdigit():  # 如果字符的开头是数字，则基因型数据一般就在改行字符中
                    name = line[line.rfind('.') + 1:]
                    resList.append(name)
            resList = list(set(resList))  # 去重
            self.geneList = resList[:]

    # 查看sentence中是否包含mList中的元素
    def isListInSentence(self, gList, sentence):
        sentence = sentence.upper()
        sList = sentence.split(' ')
        for value in gList:
            if value in sList or value + 'S' in sList:
                return value
            # else: # 匹配基因型以及后面可能带有的的序号
            #     if re.search(gene,sentence) is not None:
            #         for s in sentence:
            #             if re.match('%s[\d]*'%gene,s) is not None:
            #                 return s
        return None

    # 获取三元组 返回关系列表 2d [][]
    def findRelation(self, geneName, sentence):
        output = self.nlp.annotate(sentence, properties={
            'annotators': 'openie',
            'outputFormat': 'json'
        })

        data = json.loads(output)
        result = data['sentences'][0]['openie']
        relations = []
        for res in result:
            if res['subject'] == geneName or res['object'] == geneName:
                rel = []
                rel.append(res['subject'])
                rel.append(res['relation'])
                rel.append(res['object'])
                relations.append(rel)
        return relations


    # 将结果保存在neo4j中
    def saveInNeo(self, objectName, relation, subjectName):
        a = self.matcher.match("gene", name=objectName).first()  # 查看库中是否已经存在该节点，防止重复
        if not a:  # 如果不存在则生成该节点
            a = Node("gene", name=objectName)
        b = self.matcher.match("disease", name=subjectName).first()  # 查看库中是否已经存在该节点，防止重复
        if not b:  # 如果不存在则生成该节点
            b = Node("disease", name=subjectName)
        r = Relationship(a, relation, b)  # 创建关系
        s = a | b | r
        self.graph.create(s)  # 在neo4j库中创建该三元组

if __name__ == '__main__':
    t = DiseaseExtractor()
    t.extract()
