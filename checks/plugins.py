from .vars import *
from .utils.utils import *
from .core import *
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
    if (getLoadedModules(lines) and checkOperatingSystem(lines)):
        commonPlugins = ['frontend-tools', 'vlc-video', 'obs-outputs', 'obs-vst', 'obs-ffmpeg', 'obs-browser', 'obs-transitions', 'decklink', 'decklink-captions', 'text-freetype2', 'decklink-output-ui', 'decklink-ouput-ui', 'aja', 'aja-output-ui', 'obs-x264', 'obs-websocket', 'obs-filters', 'image-source', 'rtmp-services', 'coreaudio-encoder', 'obs-webrtc']
        windowsPlugins = ['win-wasapi', 'win-mf', 'win-dshow', 'win-capture', 'obs-text', 'obs-qsv11', 'win-decklink', 'enc-amf']
        macPlugins = ['mac-virtualcam', 'mac-videotoolbox', 'mac-syphon', 'mac-capture', 'mac-avcapture']
        linuxPlugins = ['obs-libfdk', 'linux-v4l2', 'linux-pulseaudio', 'linux-pipewire', 'linux-jack', 'linux-capture', 'linux-alsa', 'obs-qsv11']
        pluginList = lines[(getLoadedModules(lines)[0] + 1):getPluginEnd(lines)]
        thirdPartyPlugins = []

        for s in pluginList:
            if '     ' in s:
                timestamp, plugin = s.split(': ', 1)
                plugin = plugin.rsplit('.', 1)[0]
                plugin = plugin.strip()
                thirdPartyPlugins.append(plugin)

        thirdPartyPlugins = set(thirdPartyPlugins).difference(commonPlugins)
        if (checkOperatingSystem(lines) == "windows"):
            thirdPartyPlugins = set(thirdPartyPlugins).difference(windowsPlugins)
        elif (checkOperatingSystem(lines) == "mac"):
            thirdPartyPlugins = set(thirdPartyPlugins).difference(macPlugins)
        elif (checkOperatingSystem(lines) == "linux"):
            thirdPartyPlugins = set(thirdPartyPlugins).difference(linuxPlugins)
        else:
            thirdPartyPlugins = []

        pluginString = str(thirdPartyPlugins)
        pluginString = pluginString.replace("', '", "<br><li>")
        pluginString = pluginString[2:]
        pluginString = pluginString[:-2]

        if (len(thirdPartyPlugins)):
            return [LEVEL_INFO, "Third-Party Plugins (" + str(len(thirdPartyPlugins)) + ")",
                    """You have the following third-party plugins installed:<br><ul><li>""" + pluginString + "</ul>"]
