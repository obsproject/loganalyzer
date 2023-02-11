# other functions
# --------------------------------------


def search(term, lines):
    return [s for s in lines if term in s]


def searchWithIndex(term, lines):
    return [[s, i] for i, s in enumerate(lines) if term in s]


def getSections(lines):
    sectPos = []
    for i, s in enumerate(lines):
        if '------------------------------------------------' in s:
            sectPos.append(i)
    return sectPos


def getSmallerSections(lines):
    sectPos = []
    for i, s in enumerate(lines):
        if '---------------------------------' in s:
            sectPos.append(i)
    return sectPos


def getNextPos(old, lst):
    for new in lst:
        if (new > old):
            return new


def getScenes(lines):
    scenePos = []
    for i, s in enumerate(lines):
        if '- scene' in s:
            scenePos.append(i)
    return scenePos
    

def getPluginLine(lines):
    pluginLinePos = []
    for i, s in enumerate(lines):
        if 'Loaded Modules:' in s:
            pluginLinePos.append(i)
    return pluginLinePos