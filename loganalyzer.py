#!/usr/bin/env python3

import re
import requests
import json
import argparse
import textwrap
from pkg_resources import parse_version

RED = "\033[1;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[1;34m"
MAGENTA = "\033[1;35m"
CYAN = "\033[1;36m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"

CURRENT_VERSION = '23.0.0'


# error levels:
# 1 = info
# 2 = warning
# 3 = critical


# gist.github.com
# --------------------------------------

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

def getObslog(obslogId):
    API_URL = "https://obsproject.com/logs"
    return requests.get('{0}/{1}'.format(API_URL, obslogId)).text


def getLinesObslog(obslogText):
    return obslogText.split('\n')


# pastebin.com
# --------------------------------------

def getRawPaste(obslogId):
    API_URL = "https://pastebin.com/raw"
    return requests.get('{0}/{1}'.format(API_URL, obslogId)).text


def getLinesPaste(obslogText):
    return obslogText.split('\n')


# discord
# --------------------------------------


def getRawDiscord(obslogId):
    API_URL = "https://cdn.discordapp.com/attachments"
    return requests.get('{0}/{1}'.format(API_URL, obslogId)).text


def getLinesDiscord(obslogText):
    return obslogText.split('\n')


# other functions
# --------------------------------------


def search(term, lines):
    return [s for s in lines if term in s]


# checks
# --------------------------------------

cleanLog = "<br>To make a clean log file, please follow these steps: <br><br>1) Restart OBS. <br>2) Start your stream/recording for about 30 seconds. Make sure you replicate any issues as best you can, which means having any games/apps open and captured, etc. <br>3) Stop your stream/recording. <br>4) Select Help > Log Files > Upload Current Log File. Send that link via this troubleshooting tool or whichever support chat you are using."

def checkClassic(lines):
    if (len(search('Open Broadcaster Software', lines)) > 0):
        return True, [3, "OBS Classic",
                      """You are still using OBS Classic. This version is no longer supported. While we cannot and will not do anything to prevent you from using it, we cannot help with any issues that may come up. <br>It is recommended that you update to OBS Studio. <br><br>Further information on why you should update (and how): <a href="https://obsproject.com/forum/threads/how-to-easily-switch-to-obs-studio.55820/">OBS Classic to OBS Studio</a>."""]
    else:
        return False, [4, "OBS Studio", "Nothing to say"]


def checkDual(lines):
    if (len(search('Warning: OBS is already running!', lines)) > 0):
        return [3, "Two Instances",
                "Two instances of OBS are running. If you are not intentionally running two instances, they will likely interfere with each other and consume excessive resources. Stop one of them. Check Task Manager for stray OBS processes if you can't find the other one."]


def checkAutoconfig(lines):
    if (len(search('Auto-config wizard', lines)) > 0):
        return [3, "Auto-Config Wizard",
                "The log contains an Auto-Config Wizard run. Results of this analysis are therefore inaccurate. Please post a link to a clean log file. " + cleanLog]


def checkCPU(lines):
    cpu = search('CPU Name', lines)
    if (len(cpu) > 0):
        if (('APU' in cpu[0]) or ('Pentium' in cpu[0]) or ('Celeron' in cpu[0])):
            return [3, "Insufficient Hardware",
                    "Your system is below minimum specs for OBS to run and may be too underpowered to livestream. There are no recommended settings we can suggest, but try the Auto-Config Wizard in the Tools menu. You may need to upgrade or replace your computer for a better experience."]
        elif ('i3' in cpu[0]):
            return [1, "Insufficient Hardware",
                    "Your system is below minimum specs for OBS to run and is too underpowered to livestream using software encoding. Livestreams and recordings will only run smoothly if you are using the hardware QuickSync encoder (via Settings -> Output)."]


def checkMemory(lines):
    ram = search('Physical Memory:', lines)


def checkOldVersion(lines):
    versionLines = search('OBS', lines)
    if versionLines[0].split()[0] == 'OBS':
        versionString = versionLines[0].split()[1]
    elif versionLines[0].split()[2] == 'OBS':
        versionString = versionLines[0].split()[3]
    else:
        versionString = versionLines[0].split()[2]
    if parse_version(versionString) == parse_version('21.1.0'):
        return [2, "Broken Auto-Update",
                """You are not running the latest version of OBS Studio. Automatic updates in version 21.1.0 are broken due to a bug. <br>Please update by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it."""]
    elif versionString.startswith('22.0.2-26'):
        return [1, "Beta OBS Version",
                """You are running a beta build of OBS Studio."""]
    elif versionString.startswith('23.0.0-rc'):
        return [1, "Release Candidate", 
        """You are running a release candidate version of OBS Studio."""]
    elif parse_version(versionString) < parse_version(CURRENT_VERSION):
        return [2, "Old Version",
                """You are not running the latest version of OBS Studio. Please update by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it."""]


def checkGPU(lines):
    adapters = search('Adapter 1', lines)
    try:
        adapters.append(search('Adapter 2', lines)[0])
    except IndexError:
        pass
    d3dAdapter = search('Loading up D3D11', lines)
    if (len(d3dAdapter) > 0):
        if (len(adapters) == 2 and ('Intel' in d3dAdapter[0])):
            return [3, "Wrong GPU",
                    """Your Laptop has two GPUs. OBS is running on the weak integrated Intel GPU. For better performance as well as game capture being available you should run OBS on the dedicated GPU. Check the <a href="https://obsproject.com/wiki/Laptop-Troubleshooting">Laptop Troubleshooting Guide</a>."""]
        elif (len(adapters) == 1 and ('Intel' in adapters[0])):
            return [2, "Integrated GPU",
                    "OBS is running on an Intel iGPU. This hardware is generally not powerful enough to be used for both gaming and running obs. Situations where only sources from e.g. cameras and capture cards are used might work."]


def checkMicrosoftSoftwareGPU(lines):
    if (len(search('Microsoft Basic Render Driver', lines)) > 0):
        return [3, "No GPU driver available",
                "Your GPU is using the Microsoft Basic Render Driver, which is a pure software render. This will cause very high CPU load when used with OBS. Make sure to install proper drivers for your GPU. To use OBS in a virtual machine, you need to enable GPU passthrough."]

def checkOpenGLonWindows(lines):
    opengl = search('Warning: The OpenGL renderer is currently in use.', lines)
    if (len(opengl) > 0):
        return [3, "OpenGL Renderer",
                    "The OpenGL renderer should not be used on Windows, as it is not well optimized and can have visual artifacting. Switch back to the Direct3D renderer in Settings > Advanced."]

def checkGamingFeatures(lines):
    features = 0
    features += len(search('Game Bar: On', lines))
    features += len(search('Game DVR: On', lines))
    features += len(search('Game DVR Background Recording: On', lines))
    if features > 0:
        return [2, "Windows 10 Gaming Features",
                    """Certain Windows 10 Gaming features are turned on and interfere with OBS by putting additional load on your CPU and GPU. We recommend disabling them when using OBS via <a href="https://obsproject.com/wiki/How-to-disable-Windows-10-Gaming-Features">these instructions</a>.<br><br>These features are designed to provide the most performance to your game by lowering GPU priority of other applications, which would be fine if OBS didn't need a tiny bit of GPU to function."""]
    

def checkNVENC(lines):
    msgs = search("Failed to open NVENC codec", lines)
    if (len(msgs) > 0):
        return [2, "NVENC Start Failure",
                """The NVENC Encoder failed to start due of a variety of possible reasons. Make sure that Windows Game Bar and Windows Game DVR are disabled and that your GPU drivers are up to date. <br><br>You can perform a clean driver installation for your GPU by following the instructions at <a href="http://obsproject.com/forum/resources/performing-a-clean-gpu-driver-installation.65/"> Clean GPU driver installation</a>. <br>If this doesn't solve the issue, then it's possible your graphics card doesn't support NVENC. You can change to a different Encoder in Settings > Output."""]


def check940(lines):
    gpu = search('NVIDIA GeForce 940', lines)
    attempt = search('NVENC encoder', lines)
    if (len(gpu) > 0) and (len(attempt) > 0):
        return [3, "NVENC Not Supported",
                """The NVENC Encoder is not supported on the NVIDIA 940 and 940MX. Recording fails to start because of this. Please select "Software (x264)" or "Hardware (QSV)" as encoder instead in Settings > Output."""]


def checkInit(lines):
    if (len(search('Failed to initialize video', lines)) > 0):
        return [3, "Initialize Failed",
                "Failed to initialize video. Your GPU may not be supported, or your graphics drivers may need to be updated."]


def checkKiller(lines):
    if(len(search('Interface: Killer', lines)) > 0):
        return [1, "Killer NIC", 
                """Killer's Firewall is known for it's poor performance and issues when trying to stream. Please download the driver pack from <a href="https://www.killernetworking.com/killersupport/driver-downloads/category/other-downloads">the vendor's page</a> , completely uninstall all Killer NIC items and install their Driver only package."""]


def checkWifi(lines):
    if (len(search('802.11', lines)) > 0):
        return [2, "Wi-Fi Streaming",
                "In many cases, wireless connections can cause issues because of their unstable nature. Streaming really requires a stable connection. Often wireless connections are fine, but if you have problems, the first troubleshooting step would be to switch to wired. We highly recommend streaming on wired connections."]


def checkBind(lines):
    if (len(search('Binding to ', lines)) > 0):
        return [2, "Binding to IP",
                """Binding to a manually chosen IP address is rarely needed. Go to Settings → Advanced → Network and set "Bind to IP" back to "Default"."""]


def checkAdmin(lines):
    adminlines = search('Running as administrator', lines)
    if ((len(adminlines) > 0) and (adminlines[0].split()[-1] == 'false')):
        return [1, "Not Admin",
                "OBS is not running as Administrator. This can lead to OBS not being able to Game Capture certain games. If you are not running into issues, you can ignore this."]


def check32bitOn64bit(lines):
    winVersion = search('Windows Version', lines)
    obsVersion = search('OBS', lines)
    if (len(winVersion) > 0
            and len(obsVersion) > 0
            and '64-bit' in winVersion[0]
            and '64-bit' not in obsVersion[0]
            and '64bit' not in obsVersion[0]):
        # thx to secretply for the bugfix
        return [2, "32-bit OBS on 64-bit Windows",
                "You are running the 32 bit version of OBS on a 64 bit system. This will reduce performance and greatly increase the risk of crashes due to memory limitations. You should only use the 32 bit version if you have a capture device that lacks 64 bit drivers. Please run OBS using the 64-bit shortcut."]


def checkElements(lines):
    if (len(search('obs-streamelements', lines)) > 0):
        return [2, "StreamElements OBS.Live",
                """The obs.live plugin is installed. This overwrites OBS' default browser source and causes a severe performance impact. To get rid of it, first, export your scene collections and profiles, second manually uninstall OBS completely, third reinstall OBS Studio only with the latest installer from <a href="https://obsproject.com/download">https://obsproject.com/download</a>"""]


def checkAMDdrivers(lines):
    if (len(search('The AMF Runtime is very old and unsupported', lines)) > 0):
        return [2, "AMD Drivers",
                """The AMF Runtime is very old and unsupported. The AMF Encoder will no work properly or not show up at all. Consider updating your drivers by downloading the newest installer from <a href="https://support.amd.com/en-us/download">AMD's website</a>. """]


def checkMP4(lines):
    writtenFiles = search('Writing file ', lines)
    mp4 = search('.mp4', writtenFiles)
    mov = search('.mov', writtenFiles)
    if (len(mp4) > 0 or len(mov) > 0):
        return [3, "MP4/MOV Recording",
                "If you record to MP4 or MOV and the recording is interrupted, the file will be corrupted and unrecoverable. <br><br>If you require MP4 files for some other purpose like editing, remux them afterwards by selecting File > Remux Recordings in the main OBS Studio window."]


def checkAttempt(lines):
    recordingStarts = search('== Recording Start ==', lines)
    streamingStarts = search('== Streaming Start ==', lines)
    if (len(recordingStarts) + len(streamingStarts) == 0):
        return [1, "No Output Session",
                "Your log contains no recording or streaming session. Results of this log analysis are limited. Please post a link to a clean log file. " + cleanLog]


def checkPreset(lines):
    encoderLines = search('x264 encoder:', lines)
    presets = search('preset: ', lines)
    sensiblePreset = True
    for l in presets:
        if (not (('veryfast' in l) or ('superfast' in l) or ('ultrafast' in l))):
            sensiblePreset = False

    if ((len(encoderLines) > 0) and (not sensiblePreset)):
        return [1, "Non-Default x264 Preset",
                "A slower x264 preset than 'veryfast' is in use. It is recommended to leave this value on veryfast, as there are significant diminishing returns to setting it lower. It can also result in very poor gaming performance on the system if you're not using a 2 PC setup."]


def checkCustom(lines):
    encoderLines = search("'adv_ffmpeg_output':", lines)
    if (len(encoderLines) > 0):
        return [2, "Custom FFMPEG Output",
                """Custom FFMPEG output is in use. Only absolute professionals should use this. If you got your settings from a YouTube video advertising "Absolute best OBS settings" then we recommend using one of the presets in Simple output mode instead."""]


def checkAudio(lines):
    buffering = search('total audio buffering is now', lines)
    vals = []
    if (len(buffering) > 0):
        for i in buffering:
            if (i.split()[12] == "now"):
                vals.append(int(i.split()[13]))
            else:
                vals.append(int(i.split()[12]))
        if (max(vals) > 500):
            return [2, "High Audio Buffering",
                    "Audio buffering reached values above 500ms. This is an indicator of very high system load and will affect stream latency. Keep an eye on CPU usage especially, and close background programs if needed. Restart OBS to reset buffering."]
    else:
        return None


def checkMulti(lines):
    mem = search('user is forcing shared memory', lines)
    if (len(mem) > 0):
        return [2, "Memory Capture",
                """SLI/Crossfire Capture Mode (aka 'Shared memory capture') is very slow, and only to be used on SLI & Crossfire systems. <br><br>If you're using a laptop or a display with multiple graphics cards and your game is only running on one of them, consider switching OBS to run on the same GPU instead of enabling this setting. Guide available <a href="https://obsproject.com/wiki/Laptop-Troubleshooting">here</a>."""]


def checkDrop(lines):
    drops = search('insufficient bandwidth', lines)
    val = 0
    severity = 9000
    for drop in drops:
        v = float(drop[drop.find("(") + 1: drop.find(")")
                  ].strip('%').replace(",", "."))
        if (v > val):
            val = v
    if (val != 0):
        if (val >= 15):
            severity = 3
        elif (15 > val and val >= 5):
            severity = 2
        else:
            severity = 1
    return [severity, "{}% Dropped Frames".format(val),
            """Your log contains streaming sessions with dropped frames. This can only be caused by a failure in your internet connection or your networking hardware. It is not caused by OBS. Follow the troubleshooting steps at: <a href="https://obsproject.com/wiki/Dropped-Frames-and-General-Connection-Issues">Dropped Frames and General Connection Issues</a>."""]


def checkRendering(lines):
    drops = search('rendering lag', lines)
    val = 0
    severity = 9000
    for drop in drops:
        v = float(drop[drop.find("(") + 1: drop.find(")")
                  ].strip('%').replace(",", "."))
        if (v > val):
            val = v
    if (val != 0):
        if (val >= 15):
            severity = 3
        elif (15 > val and val >= 5):
            severity = 2
        else:
            severity = 1
        return [severity, "{}% Rendering Lag".format(val),
                """Your GPU is maxed out and OBS can't render scenes fast enough. Running a game without vertical sync or a frame rate limiter will frequently cause performance issues with OBS because your GPU will be maxed out. OBS requires a little GPU to render your scene. <br><br>Enable Vsync or set a reasonable frame rate limit that your GPU can handle without hitting 100% usage. <br>If that's not enough you may also need to turn down some of the video quality options in the game. If you are experiencing issues in general while using OBS, your GPU may be overloaded for the settings you are trying to use. <br>Please check our guide for ideas why this may be happening, and steps you can take to correct it: <a href="https://obsproject.com/wiki/GPU-overload-issues">GPU Overload Issues</a>."""]


def checkEncoding(lines):
    drops = search('skipped frames', lines)
    val = 0
    severity = 9000
    for drop in drops:
        v = float(drop[drop.find("(") + 1: drop.find(")")
                  ].strip('%').replace(",", "."))
        if (v > val):
            val = v
    if (val != 0):
        if (val >= 15):
            severity = 3
        elif (15 > val and val >= 5):
            severity = 2
        else:
            severity = 1
        return [severity, "{}% Encoder Overload".format(val),
                """The encoder is skipping frames because of CPU overload. Read about <a href="https://obsproject.com/wiki/General-Performance-and-Encoding-Issues">General Performance and Encoding Issues</a>."""]


def checkStreamSettingsX264(lines):
    streamingSessions = []
    for i, s in enumerate(lines):
        if "[x264 encoder: 'simple_h264_stream'] settings:" in s:
            streamingSessions.append(i)

    if (len(streamingSessions) > 0):
        bitrate = float(lines[streamingSessions[-1] + 2].split()[-1])
        fps_num = float(lines[streamingSessions[-1] + 5].split()[-1])
        fps_den = float(lines[streamingSessions[-1] + 6].split()[-1])
        width = float(lines[streamingSessions[-1] + 7].split()[-1])
        height = float(lines[streamingSessions[-1] + 8].split()[-1])

        bitrateEstimate = (width * height * fps_num / fps_den) / 20000
        if (bitrate < bitrateEstimate):
            return [1, "Low Stream Bitrate",
                    "Your stream encoder is set to a video bitrate that is too low. This will lower picture quality especially in high motion scenes like fast paced games. Use the Auto-Config Wizard to adjust your settings to the optimum for your situation. It can be accessed from the Tools menu in OBS, and then just follow the on-screen directions."]


def checkStreamSettingsNVENC(lines):
    streamingSessions = []
    for i, s in enumerate(lines):
        if "[NVENC encoder: 'streaming_h264'] settings:" in s:
            streamingSessions.append(i)
    if (len(streamingSessions) > 0):
        bitrate = 0
        fps_num = 0
        width = 0
        height = 0
        for i in range(12):
            chunks = lines[streamingSessions[-1] + i].split()
            if (chunks[-2] == 'bitrate:'): 
                bitrate = float(chunks[-1])
            elif (chunks[-2] == 'keyint:'): 
                fps_num = float(chunks[-1])
            elif (chunks[-2] == 'width:'): 
                width = float(chunks[-1])
            elif (chunks[-2] == 'height:'): 
                height = float(chunks[-1])
        bitrateEstimate = (width * height * fps_num) / 20000
        if (bitrate < bitrateEstimate):
            return [1, "Low Stream Bitrate",
                    "Your stream encoder is set to a video bitrate that is too low. This will lower picture quality especially in high motion scenes like fast paced games. Use the Auto-Config Wizard to adjust your settings to the optimum for your situation. It can be accessed from the Tools menu in OBS, and then just follow the on-screen directions."]


def checkVideoSettings(lines):
    videoSettings = []
    res = []
    for i, s in enumerate(lines):
        if "video settings reset:" in s:
            videoSettings.append(i)
    if (len(videoSettings) > 0):
        basex, basey = lines[videoSettings[-1] + 1].split()[-1].split('x')
        outx, outy = lines[videoSettings[-1] + 2].split()[-1].split('x')
        fps_num, fps_den = lines[videoSettings[-1] + 4].split()[-1].split('/')
        fmt = lines[videoSettings[-1] + 5].split()[-1]
        yuv = lines[videoSettings[-1] + 6].split()[-1]
        baseAspect = float(basex) / float(basey)
        outAspect = float(outx) / float(outy)
        fps = float(fps_num) / float(fps_den)
        if ((not ((1.77 < baseAspect) and (baseAspect < 1.7787))) or
                (not ((1.77 < outAspect) and (outAspect < 1.7787)))):
            res.append([2, "Non-Standard Aspect Ratio",
                        "Almost all modern streaming services and video platforms expect video in 16:9 aspect ratio. OBS is currently configured to record in an aspect ration that differs from that. You (or your viewers) will see black bars during playback."])
        if (fmt != 'NV12'):
            res.append([3, "Wrong Color Format",
                        "Color Formats other than NV12 are primarily intended for recording, and are not recommended when streaming. Streaming may incur increased CPU usage due to color format conversion."])
        if (not ((fps == 60) or (fps == 30))):
            res.append([2, "Non-Standard Framerate",
                        "Framerates other than 30fps or 60fps may lead to playback issues like stuttering or screen tearing. Stick to either of these for better compatibility with video players."])
        if 'Full' in yuv:
            res.append([2, "Wrong YUV Color Range",
                        """Having the YUV Color range set to "Full" will cause playback issues in certain browsers and on various video platforms. Shadows, highlights and color will look off. In OBS, go to "Settings -> Advanced" and set "YUV Color Range" back to "Partial"."""])
    return res


def getScenes(lines):
    scenePos = []
    for i, s in enumerate(lines):
        if '- scene' in s:
            scenePos.append(i)
    return scenePos


def getSections(lines):
    sectPos = []
    for i, s in enumerate(lines):
        if '------------------------------------------------' in s:
            sectPos.append(i)
    return sectPos


def getNextPos(old, lst):
    for new in lst:
        if (new > old):
            return new


def checkSources(lower, higher, lines):
    res = None
    violation = False
    monitor = search('monitor_capture', lines[lower:higher])
    game = search('game_capture', lines[lower:higher])
    if (len(monitor) > 0 and len(game) > 0):
        res = []
        res.append([2, "Capture Interference",
                    "Monitor and Game Capture Sources interfere with each other. Never put them in the same scene"])
    if (len(game) > 1):
        if (res is None):
            res = []
        violation = True
        res.append([2, "Multiple Game Capture",
                    "Multiple Game Capture sources are usually not needed, and can sometimes interfere with each other. You can use the same Game Capture for all your games! If you change games often, try out the hotkey mode, which lets you press a key to select your active game. If you play games in fullscreen, use 'Capture any fullscreen application' mode."])
    return res, violation


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
                higher = getNextPos(s, sceneLines) - 1
            else:
                higher = getNextPos(s, sections) - 1
            m, h = checkSources(s, higher, lines)
            if (not hit):
                ret.append(m)
                hit = h
    elif (len(added) > 0):
        ret = []
    else:
        ret.append([[1, "No Scenes/Sources",
                     """There are neither scenes nor sources added to OBS. You won't be able to record anything but a black screen without adding sources to your scenes. <br><br>If you're new to OBS Studio, check out our <a href="https://obsproject.com/wiki/OBS-Studio-Quickstart">4 Step Quickstart Guide</a>. <br><br>For a more detailed guide, check out our <a href="https://obsproject.com/wiki/OBS-Studio-Overview">Overview Guide</a>. <br>If you want a video guide, check out these community created video tutorials:<br> - <a href="https://obsproject.com/forum/resources/full-video-guide-for-obs-studio-and-twitch.377/">Nerd or Die's quickstart video guide</a> <br> - <a href="https://www.youtube.com/playlist?list=PLzo7l8HTJNK-IKzM_zDicTd2u20Ab2pAl">EposVox's Master Class</a>"""]])
    return ret


# main functions
##############################################


def textOutput(string):
    dedented_text = textwrap.dedent(string).strip()
    return textwrap.fill(dedented_text, initial_indent=' ' * 4, subsequent_indent=' ' * 4, width=80, )


def getSummary(messages):
    summary = ""
    critical = ""
    warning = ""
    info = ""
    for i in messages:
        if (i[0] == 3):
            critical = critical + i[1] + ", "
        elif (i[0] == 2):
            warning = warning + i[1] + ", "
        elif (i[0] == 1):
            info = info + i[1] + ", "
    summary += "{}Critical: {}\n".format(RED, critical)
    summary += "{}Warning:  {}\n".format(YELLOW, warning)
    summary += "{}Info:     {}\n".format(CYAN, info)
    return summary


def getResults(messages):
    results = ""
    results += "{}--------------------------------------\n".format(RESET)
    results += " \n"
    results += "Details\n"
    results += "\nCritical:"
    for i in messages:
        if (i[0] == 3):
            results += "\n{}{}\n".format(RED, i[1])
            results += textOutput(i[2])

    results += "{} \n".format(RESET)
    results += "\nWarning:"
    for i in messages:
        if (i[0] == 2):
            results += "\n{}{}\n".format(YELLOW, i[1])
            results += textOutput(i[2])

    results += "{} \n".format(RESET)
    results += "\nInfo:"
    for i in messages:
        if (i[0] == 1):
            results += "\n{}{}\n".format(CYAN, i[1])
            results += textOutput(i[2])
    return results


def doAnalysis(url):
    messages = []
    success = False
    logLines = []
    matchGist = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}gist\.github\.com)/)(anonymous/)?([a-z0-9]{32}))", url)
    matchHaste = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?hastebin\.com)/)([a-z0-9]{10}))", url)
    matchObs = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?obsproject\.com)/logs/)(.{16}))", url)
    matchPastebin = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}(www\.)?pastebin\.com/))(.{8}))", url)
    matchDiscord = re.match(
        r"(?i)\b((?:https?:(?:/{1,3}cdn\.discordapp\.com)/)(attachments/)([0-9]{18}/[0-9]{18}/[0-9\-\_]{19}.txt))", url)
    if (matchGist):
        gistObject = getGist(matchGist.groups()[-1])
        logLines = getLinesGist(gistObject)
        messages.append(getDescriptionGist(gistObject))
        success = True
    elif (matchHaste):
        hasteObject = getHaste(matchHaste.groups()[-1])
        logLines = getLinesHaste(hasteObject)
        messages.append(getDescription(logLines))
        success = True
    elif (matchObs):
        obslogObject = getObslog(matchObs.groups()[-1])
        logLines = getLinesObslog(obslogObject)
        messages.append(getDescription(logLines))
        success = True
    elif (matchPastebin):
        pasteObject = getRawPaste(matchPastebin.groups()[-1])
        logLines = getLinesPaste(pasteObject)
        messages.append(getDescription(logLines))
        success = True
    elif (matchDiscord):
        pasteObject = getRawDiscord(matchDiscord.groups()[-1])
        logLines = getLinesDiscord(pasteObject)
        messages.append(getDescription(logLines))
        success = True
    if (success):
        classic, m = checkClassic(logLines)
        messages.append(m)
        if (not classic):
            messages.append(checkOldVersion(logLines))
            messages.append(checkDual(logLines))
            messages.append(checkAutoconfig(logLines))
            messages.append(checkCPU(logLines))
            messages.append(checkAMDdrivers(logLines))
            messages.append(checkGPU(logLines))
            messages.append(checkInit(logLines))
            #messages.append(checkElements(logLines))
            messages.append(checkNVENC(logLines))
            messages.append(check940(logLines))
            messages.append(checkKiller(logLines))
            messages.append(checkWifi(logLines))
            messages.append(checkBind(logLines))
            messages.append(checkAdmin(logLines))
            messages.append(check32bitOn64bit(logLines))
            messages.append(checkAttempt(logLines))
            messages.append(checkMP4(logLines))
            messages.append(checkPreset(logLines))
            messages.append(checkCustom(logLines))
            messages.append(checkAudio(logLines))
            messages.append(checkDrop(logLines))
            messages.append(checkRendering(logLines))
            messages.append(checkEncoding(logLines))
            messages.append(checkMulti(logLines))
            messages.append(checkStreamSettingsX264(logLines))
            messages.append(checkStreamSettingsNVENC(logLines))
            messages.append(checkMicrosoftSoftwareGPU(logLines))
            messages.append(checkOpenGLonWindows(logLines))
            messages.append(checkGamingFeatures(logLines))
            m = checkVideoSettings(logLines)
            for sublist in m:
                if sublist is not None:
                    messages.append(sublist)
            m = parseScenes(logLines)
            for sublist in m:
                if sublist is not None:
                    for item in sublist:
                        messages.append(item)
    else:
        messages.append([3, "NO LOG", "URL doesn't contain a log."])
    # print(messages)
    ret = [i for i in messages if i is not None]
    # print(ret)
    return (ret)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", '-u', dest='url',
                        default="", help="url of gist or haste", required=True)
    flags = parser.parse_args()

    msgs = doAnalysis(flags.url)
    print(getSummary(msgs))
    print(getResults(msgs))


if __name__ == "__main__":
    main()
