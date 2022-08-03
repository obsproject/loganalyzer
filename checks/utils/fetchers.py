import requests
import re


# gist.github.com
# --------------------------------------


def matchGist(url):
    return re.match(
        r"(?i)\b((?:https?:(?:/{1,3}gist\.github\.com)/)(anonymous/)?([a-z0-9]{32}))", url)


def getGist(inputUrl):
    API_URL = "https://api.github.com"
    gistId = inputUrl
    return requests.get('{0}/gists/{1}'.format(API_URL, gistId)).json()


def getLinesGist(gistObject):
    files = [(v, k) for (k, v) in gistObject['files'].items()]
    return files[0][0]['content'].split('\n')


def getDescriptionGist(gistObject):
    desc = gistObject['description']
    if (desc == ""):
        desc = gistObject['id']
    return [0, "DESCRIPTION", desc]


# hastebin.com
# --------------------------------------


def matchHaste(url):
    return re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?hastebin\.com)/)([a-z0-9]{10}))", url)


def getHaste(hasteId):
    API_URL = "https://hastebin.com"
    return requests.get('{0}/documents/{1}'.format(API_URL, hasteId)).json()


def getLinesHaste(hasteObject):
    text = hasteObject['data']
    return text.split('\n')


def getDescription(lines):
    return [0, "DESCRIPTION", lines[0]]


# obsproject.com
# --------------------------------------


def matchObs(url):
    return re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?obsproject\.com)/logs/)(.{16}))", url)


def getObslog(obslogId):
    API_URL = "https://obsproject.com/logs"
    return requests.get('{0}/{1}'.format(API_URL, obslogId)).text


def getLinesObslog(obslogText):
    return obslogText.split('\n')


# pastebin.com
# --------------------------------------


def matchPastebin(url):
    return re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?pastebin\.com/))(?:raw/)?(.{8}))", url)


def getRawPaste(obslogId):
    API_URL = "https://pastebin.com/raw"
    return requests.get('{0}/{1}'.format(API_URL, obslogId)).text


def getLinesPaste(obslogText):
    return obslogText.split('\n')


# discord
# --------------------------------------


def matchDiscord(url):
    return re.match(
        r"(?i)\b((?:https?:(?:/{1,3}cdn\.discordapp\.com)/)(attachments/)([0-9]{18,}/[0-9]{18,}/(?:[0-9\-\_]{19}|message).txt))", url)


def getRawDiscord(obslogId):
    API_URL = "https://cdn.discordapp.com/attachments"
    resp = requests.get('{0}/{1}'.format(API_URL, obslogId))
    if resp.status_code == 200:
        return resp.text
    return ""


def getLinesDiscord(obslogText):
    return obslogText.split('\n')


# local file
def getLinesLocal(filename):
    try:
        with open(filename, "r") as f:
            return f.readlines()
    except:
        return
