from .vars import *
from .utils.utils import *


def checkMulti(lines):
    mem = search('user is forcing shared memory', lines)
    if (len(mem) > 0):
        return [LEVEL_WARNING, "Memory Capture",
                """SLI/Crossfire Capture Mode (aka 'Shared memory capture') is very slow, and only to be used on SLI & Crossfire systems. <br><br>If you're using a laptop or a display with multiple graphics cards and your game is only running on one of them, consider switching OBS to run on the same GPU instead of enabling this setting. Guide available <a href="https://obsproject.com/wiki/Laptop-Troubleshooting">here</a>."""]


def checkSources(lower, higher, lines):
    res = None
    violation = False
    monitor = search('monitor_capture', lines[lower:higher])
    game = search('game_capture', lines[lower:higher])
    if (len(monitor) > 0 and len(game) > 0):
        res = []
        res.append([LEVEL_WARNING, "Capture Interference",
                    "Display and Game Capture Sources interfere with each other. Never put them in the same scene."])
    if (len(game) > 1):
        if (res is None):
            res = []
        violation = True
        res.append([LEVEL_WARNING, "Multiple Game Capture",
                    "Multiple Game Capture sources are usually not needed, and can sometimes interfere with each other. You can use the same Game Capture for all your games! If you change games often, try out the hotkey mode, which lets you press a key to select your active game. If you play games in fullscreen, use 'Capture any fullscreen application' mode."])
    return res, violation


def checkBrowserAccel(lines):
    disabled = search('Browser Hardware Acceleration: false', lines)
    blacklisted = search('[obs-browser]: Blacklisted device detected, disabling browser source hardware acceleration', lines)
    if (len(disabled) > 0 and len(blacklisted) == 0):
        return [LEVEL_WARNING, "Browser Not Accelerated",
                "Browser hardware acceleration is currently disabled. Enabling acceleration is highly recommended due to the improvements to performance and significantly lower CPU usage for browser sources. This can be enabled in Settings -> Advanced."]
    elif (len(blacklisted) > 0):
        return [LEVEL_INFO, "Browser Not Accelerated",
                "Unfortunately, browser source hardware acceleration is not compatible with your system/graphics card. Because of this, browser sources will use extra CPU and may stutter. Try to use as few browser sources as possible."]


def parseScenes(lines):
    ret = []
    hit = False
    sceneLines = getScenes(lines)
    sourceLines = search(' - source:', lines)
    added = search('User added source', lines)
    if ((len(sceneLines) > 0) and (len(sourceLines) > 0)):
        sections = getSections(lines)
        higher = 0
        for s in sceneLines:
            if (s != sceneLines[-1]):
                higher = getNextPos(s, sceneLines)
            else:
                higher = getNextPos(s, sections)
            m, h = checkSources(s, higher, lines)
            if (not hit and m not in ret):
                ret.append(m)
                hit = h
    elif (len(added) > 0):
        ret = []
    else:
        ret.append([[LEVEL_INFO, "No Scenes/Sources",
                     """There are neither scenes nor sources added to OBS. You won't be able to record anything but a black screen without adding sources to your scenes. <br><br>If you're new to OBS Studio, check out our <a href="https://obsproject.com/wiki/OBS-Studio-Quickstart">4 Step Quickstart Guide</a>. <br><br>For a more detailed guide, check out our <a href="https://obsproject.com/wiki/OBS-Studio-Overview">Overview Guide</a>. <br>If you want a video guide, check out these community created video tutorials:<br> - <a href="https://obsproject.com/forum/resources/full-video-guide-for-obs-studio-and-twitch.377/">Nerd or Die's quickstart video guide</a> <br> - <a href="https://www.youtube.com/playlist?list=PLzo7l8HTJNK-IKzM_zDicTd2u20Ab2pAl">EposVox's Master Class</a>"""]])
    return ret
