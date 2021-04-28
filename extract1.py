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

        self.paperPath = None
        if paperPath is None:
            self.paperPath = './data/paper_test.txt'
        else:
            self.paperPath = paperPath
        if not os.path.exists(self.paperPath):
            print('!-- error : path:%s not exist --!' % self.paperPath)
            exit(1)
        self.geneList = []
        self.getGeneName()
        self.isNeo4j = isNeo4j
        self.nlp = None
        self.graph = None
        self.matcher = None
        # 打开NLP服务
        if isNLP:
            self.nlp = StanfordCoreNLP(r'/Users/yucheng/Applications/python/package/stanford_nlp', timeout=60)
        # 连接neo4j数据库
        if isNeo4j:
            self.graph = None
            try:
                self.graph = Graph("http://localhost:7474", auth=("neo4j", "1111"))  # 这里是数据库的用户名和密码，按照自己的真实情况填写
            except:
                print('*-- warning: please open your neo4j server --*')
                exit(1)
            self.matcher = NodeMatcher(self.graph)
            print('*-- neo4j is opening!--*')
        print('*-- DiseaseExtractor init success!--*\n')

    def extract(self, showTriple=False):
        genelist = relationlist = phenlist = []
        with open(self.paperPath, 'r', encoding='utf-8') as f:  # 读取要抽取的文本
            content = f.read()  # 读取该文件的全部文本
            content = content.replace('\n', ' ')  # 文本预处理
            content = content.replace('-', '_')
            content = content.replace('et al.', ' ')

            sentenceList = re.split('[.?!;:]', content)  # 以.?!;作为分隔符，将文本转化成一个list
            if showTriple:
                print('*-- The relationship of triples is as follows --*\n')
            for longSentence in sentenceList:
                # 过滤掉括号内的内容，降低噪声影响, [], {} ()
                longSentence = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", longSentence)

                for shortSentence in longSentence.split(','):  # 以.作为分隔符，继续将小文本转为list
                    sentenceSlices = utils.strsplit(shortSentence)
                    for slice in sentenceSlices:
                        slice = slice.strip()
                        # if slice[0] == '#':
                        #     continue
                        slice = utils.stripSides(slice)
                        # print(slice)  # 输出分析语句
                        geneName = self.isListInSentence(self.geneList, slice)  # 获取句子中包含的 基因型数据

                        if geneName:  # 如果包含基因型数据
                            objectName, relation, resList = self.findRelation(geneName, slice)  # 找出三元组关系
                            if resList is None or resList == [''] or resList == [' ']:  # 如果三元组非空，则将结果保存在neo4j中
                                continue
                            for sub in resList:
                                if self.isNeo4j:
                                    self.saveInNeo(objectName.strip(), relation.strip(), sub.strip())
                                if showTriple:
                                    print('(' + objectName.strip() + ') - [ ' + relation.strip() + ' ] -> (' + sub.strip() + ')')
                                genelist.append(objectName.strip())
                                relationlist.append(relation.strip())
                                phenlist.append(sub.strip())
        if self.isNeo4j:
            print('\n*-- save into neo4j success--*')
        if showTriple:
            print('\n*-- End of presentation --*')
        return genelist,relationlist,phenlist

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

    # 获取三元组(gene,rel,list)
    def findRelation(self, geneName, sentence):
        if sentence.find(geneName) < 0:
            return geneName, '', []
        relation, resList = self.getReason(sentence)
        for l in resList:
            if relation == l or geneName == l:
                resList.remove(l)
        return geneName, relation, resList

    # 使用分词及语义分析技术抽取事件三元组中的关系和实体
    def getReason(self, sentence):
        try:
            dependencyInfos = self.nlp.dependency_parse(sentence)  # 语义分析
            # for info in dependencyInfos: # 测试用
            #     print(info)
            words = self.nlp.word_tokenize(sentence)  # 分词
            rootIndex = dependencyInfos[0][2] - 1  # 文本主内容的下标
            resList = []
            relation = words[rootIndex]
            # 添加动词修饰符，如not never等
            for info in dependencyInfos:
                if info[0] == 'advmod' or info[0] == 'amod' and info[1] == dependencyInfos[0][2]:
                    relation = words[info[2] - 1] + ' ' + relation

            case = cc = obj = obl = -1
            for i in range(rootIndex, len(dependencyInfos)):  # 遍历语义分析的结果
                if dependencyInfos[i][0] == 'case':
                    case = i
                if dependencyInfos[i][0] == 'cc':
                    cc = i
                if dependencyInfos[i][0] == 'obj':
                    obj = i
                # if dependencyInfos[i][0] == 'obl':
                #     obl = i
            if obj >= 0:  # (如果没有case的时候)判断obj对象
                resList.append(self.getObjs(dependencyInfos, obj, words))
            # if obl >= 0:
            #     resList.append(self.getObjs(dependencyInfos, obl, words))
            if case >= 0:  # 如果语义依赖关系为因果，则对该内容进一步处理
                resList.append(self.getCases(dependencyInfos, dependencyInfos[case][1] - 1, 'case', words))
            if cc >= 0 and case >= 0 and dependencyInfos[cc][2] - 1 == dependencyInfos[case][1]:  # 如果并列关系的前一位和case相同则可以认定为关系并列
                resList.append(self.getCases(dependencyInfos, dependencyInfos[cc][1] - 1, 'cc', words))


        except:
            return '', []
        return relation, resList

    # 根据关系名词，获取该关系对应的实体
    def getCases(self, dependencyInfos, Index, IndexName, words):
        res = []
        partSpeech = ''
        for info in dependencyInfos:  # 遍历语义分析结果
            if info[0] == IndexName:  # 跳过关系名词
                continue
            if info[1] - 1 == Index or info[2] - 1 == Index:  # 根据语义依赖关系过滤可能的实体
                if words[Index] and words[Index] not in res:
                    if words[info[2] - 1] not in self.geneList:
                        partSpeech += info[0]
                        res.append(words[info[2] - 1])  # 获取实体
        if 'n' in partSpeech or 'mod' in partSpeech:  # 根据词性过滤实体
            return ' '.join(res)
        return words[Index]

    def getObjs(self, dependencyInfos, Index, words):
        res = []

        for i in range (0,len(dependencyInfos)):
            if dependencyInfos[i][0] == 'amod' or dependencyInfos[i][0] == 'mod':
                res.append(words[dependencyInfos[i][2]-1])
        res.append(words[dependencyInfos[Index][2]-1])
        return ' '.join(res)

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
