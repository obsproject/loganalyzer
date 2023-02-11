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


def getSubSections(lines):
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


def getLoadedModules(lines):
    loadedModulePos = []
    for i, s in enumerate(lines):
        if 'Loaded Modules:' in s:
            loadedModulePos.append(i)
    return loadedModulePos


def getPluginEnd(lines):
    loadedModules = getLoadedModules(lines)
    subSections = getSubSections(lines)
    for i, s in enumerate(lines):
        if (subSections[i] > loadedModules[0]):
            return subSections[i]
