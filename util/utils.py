def strsplit(s):
    clause = [
        'that',
        'while',
        'because',
        'and'
    ]
    if s is None or s == '' or s == ' ':
        return []
    splitsentence = []
    for t in s.split(clause[0]):
        t = t.strip()
        flag = True
        tlist = t.split(' ')
        for i in range(0, len(tlist)):
            if tlist[i] == 'and' and i < len(tlist) - 3:
                flag = False
                splitsentence.append(t[:t.index('and')].strip())
                splitsentence.append(t[t.index('and') + 3:].strip())
        if flag:
            splitsentence.append(t)

    tar = []
    for sentence in splitsentence:
        for s in sentence.split(clause[1]):
            tar.append(s.strip())

    # tar = []
    # for s1 in s.split(clause[0]):
    #     for s2 in s1.split(clause[1]):
    #         for s3 in s2.split(clause[2]):
    #             for s4 in s3.split(clause[3]):
    #                 tar.append(s4.strip())
    return tar

def find(list,str):
    for i in range(0,len(list)):
        if list[i] == str:
            return i
    return -1

def stripSides(s):
    if s is None or s == '' or s == ' ':
        return s
    # # 一般大写都是开头
    # if s[0].isupper():
    #     return s
    # 不是大写的话是从句中分离出来的，截取不必要的词汇，如such as，部分如therefore用前一定有‘，’的可以不用考虑
    words = [
        'such as',
        'because','Because'
        'like',
        'and'
    ]
    for w in words:
        if s.find(w) == 0 and len(w) < len(s):
            return s[len(w):].strip()
    return s