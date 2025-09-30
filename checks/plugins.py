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
        return [LEVEL_CRITICAL, f"Plugins Not Loaded ({len(notLoadedPlugins)})",
                f"""Some plugins were not loaded. This can be the result of a version incompatibility between OBS and the plugin, or of a missing dependency.{pluginString}"""]


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
