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
    moduleStart = getLoadedModules(lines)[0]
    operatingSystem = checkOperatingSystem(lines)
    if moduleStart and operatingSystem:
        commonPlugins = ['frontend-tools', 'vlc-video', 'obs-outputs', 'obs-vst', 'obs-ffmpeg', 'obs-browser', 'obs-transitions', 'decklink', 'decklink-captions', 'text-freetype2', 'decklink-output-ui', 'decklink-ouput-ui', 'aja', 'aja-output-ui', 'obs-x264', 'obs-websocket', 'obs-filters', 'image-source', 'rtmp-services', 'obs-webrtc', 'obs-nvenc', 'nv-filters', 'test-input']
        osPlugins = {"windows": ['win-wasapi', 'win-mf', 'win-dshow', 'win-capture', 'obs-text', 'obs-qsv11', 'win-decklink', 'enc-amf', 'coreaudio-encoder'],
                     "mac": ['mac-virtualcam', 'mac-videotoolbox', 'mac-syphon', 'mac-capture', 'mac-avcapture', 'coreaudio-encoder', 'mac-avcapture-legacy'],
                     "linux": ['obs-libfdk', 'linux-v4l2', 'linux-pulseaudio', 'linux-pipewire', 'linux-jack', 'linux-capture', 'linux-alsa', 'obs-qsv11']
                     }
        pluginList = lines[(moduleStart + 1):getPluginEnd(lines)]
        thirdPartyPlugins = []

        for s in pluginList:
            if '     ' in s:
                timestamp, plugin = s.split(': ', 1)
                plugin = plugin.rsplit('.', 1)[0]
                plugin = plugin.strip()
                thirdPartyPlugins.append(plugin)

        disabledPlugins = search(", is disabled", lines[:moduleStart])
        for line in disabledPlugins:
            thirdPartyPlugins.append(line.split("'")[1] + " (disabled)")

        thirdPartyPlugins = set(thirdPartyPlugins).difference(commonPlugins)
        if operatingSystem in osPlugins:
            thirdPartyPlugins = set(thirdPartyPlugins).difference(osPlugins[operatingSystem])
        else:
            thirdPartyPlugins = []

        pluginString = "<br><li>".join(str(plugin) for plugin in thirdPartyPlugins)

        if thirdPartyPlugins:
            return [LEVEL_INFO, f"Third-Party Plugins ({len(thirdPartyPlugins)})",
                    f"""You have the following third-party plugins installed:<br><ul><li>{pluginString}</ul>"""]
