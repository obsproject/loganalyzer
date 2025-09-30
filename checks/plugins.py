from .vars import *
from .utils.utils import *
from .core import *
import os.path


def checkImports(lines):
    notLoaded = search("' not loaded", lines[:getLoadedModules(lines)[0]])
    notLoaded += search("' compiled with newer libobs", lines[:getLoadedModules(lines)[0]])
    notLoadedPlugins = []

    for line in notLoaded:
        plugin = os.path.split(os.path.splitext(line.split("'")[1])[0])[1]
        if plugin:
            notLoadedPlugins.append(plugin)

    pluginString = "<br><li>".join(str(plugin) for plugin in notLoadedPlugins)
    if notLoadedPlugins:
        pluginString = f"<br><br>Plugins affected:<br><ul><li>{pluginString}</ul>"
        return [LEVEL_WARNING, f"Plugins Not Loaded ({len(notLoadedPlugins)})",
                f"""Some plugins were not loaded. This can be the result of a version incompatibility between OBS and the plugin, or of a missing dependency.{pluginString}"""]


def checkPluginList(lines):
    moduleStart = getLoadedModules(lines)[0]
    operatingSystem = checkOperatingSystem(lines)
    if moduleStart and operatingSystem:

        # When adding to those lists, please follow alphabetical order.
        commonPlugins = ['aja', 'aja-output-ui', 'decklink', 'decklink-captions', 'decklink-ouput-ui', 'decklink-output-ui', 'frontend-tools', 'image-source', 'nv-filters', 'obs-browser', 'obs-ffmpeg', 'obs-filters', 'obs-nvenc', 'obs-outputs', 'obs-transitions', 'obs-vst', 'obs-webrtc', 'obs-websocket', 'obs-x264', 'rtmp-services', 'test-input', 'text-freetype2', 'vlc-video']
        osPlugins = {"windows": ['coreaudio-encoder', 'enc-amf', 'obs-qsv11', 'obs-text', 'win-capture', 'win-decklink', 'win-dshow', 'win-mf', 'win-wasapi'],
                     "mac": ['coreaudio-encoder', 'mac-avcapture', 'mac-avcapture-legacy', 'mac-capture', 'mac-syphon', 'mac-videotoolbox', 'mac-virtualcam'],
                     "linux": ['linux-alsa', 'linux-capture', 'linux-jack', 'linux-pipewire', 'linux-pulseaudio', 'linux-v4l2', 'obs-libfdk', 'obs-qsv11']
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
