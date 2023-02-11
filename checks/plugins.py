from .vars import *
from .utils.utils import *
import re

import_re = re.compile(r"""
    (?i)
    \/
    (?P<plugin>[^\/]+)
    '\sdue\sto\spossible\simport\sconflicts
    """, re.VERBOSE)


def checkImports(lines):
    conflicts = search('due to possible import conflicts', lines)
    if (len(conflicts) > 0):
        append = ""
        for p in conflicts:
            c = import_re.search(p)
            if c and c.group("plugin"):
                append += "<li>" + c.group("plugin").replace('.dll', '') + "</li>"

        if append:
            append = "<br><br>Plugins affected:<ul>" + append + "</ul>"
            return [LEVEL_CRITICAL, "Outdated Plugins (" + str(len(conflicts)) + ")",
                    """Some plugins need to be manually updated, as they do not work with this version of OBS. Check our <a href="https://obsproject.com/kb/obs-studio-28-plugin-compatibility">Plugin Compatibility Guide</a> for known updates & download links.""" + append]


def checkPluginList(lines):
    if (getPluginLine(lines)): 
        firstPartyPlugins = ['win-wasapi.dll', 'win-mf.dll', 'win-dshow.dll', 'win-capture.dll', 'vlc-video.dll', 'text-freetype2.dll', 'rtmp-services.dll', 'obs-x264.dll', 'obs-websocket.dll', 'obs-vst.dll', 'obs-transitions.dll', 'obs-text.dll', 'obs-qsv11.dll', 'obs-outputs.dll', 'obs-filters.dll', 'obs-ffmpeg.dll', 'obs-browser.dll', 'image-source.dll', 'frontend-tools.dll', 'decklink-output-ui.dll', 'decklink-captions.dll', 'coreaudio-encoder.dll', 'win-decklink.dll', 'decklink-ouput-ui.dll', 'enc-amf.dll']
        thirdPartyPlugins = []
        pluginStart = getPluginLine(lines)[0] + 1
        pluginEnd = getSmallerSections(lines)[6]

        x = pluginStart
        y = 0

        while (x < pluginEnd):
            noNumbers = lines[x].split(' ')
            if(len(noNumbers[-1]) > 1):
                thirdPartyPlugins.append(noNumbers[-1])
            x = x + 1
        
        while (y < len(thirdPartyPlugins)):
            currentPlugin = thirdPartyPlugins[y]
            updatedPlugin = currentPlugin[:-1]
            thirdPartyPlugins[y] = updatedPlugin
            y = y + 1

        thirdPartyPlugins = set(thirdPartyPlugins).difference(firstPartyPlugins)
        pluginString = str(thirdPartyPlugins)
        pluginString = pluginString.replace("', '", "<br>")
        pluginString = pluginString[2:]
        pluginString = pluginString[:-2]

        if(len(pluginString) > 5):
            return [LEVEL_INFO, "Third-Party Plugins",
                """You have the following third party plugins installed:<br><br><strong>""" + pluginString + "</strong>"]
