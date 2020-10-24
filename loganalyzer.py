#!/usr/bin/env python3

import argparse
import datetime
import json
import re
import requests
import sys
import textwrap
import html

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

CURRENT_VERSION = '26.0.2'

LEVEL_INFO = 1
LEVEL_WARNING = 2
LEVEL_CRITICAL = 3
LEVEL_NONE = 4


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


# local file
def getLinesLocal(filename):
    try:
        with open(filename, "r") as f:
            return f.readlines()
    except:
        return

# other functions
# --------------------------------------


def search(term, lines):
    return [s for s in lines if term in s]

def searchWithIndex(term, lines):
    return [[s, i] for i, s in enumerate(lines) if term in s]

# checks
# --------------------------------------

cleanLog = "<br>To make a clean log file, please follow these steps: <br><br>1) Restart OBS. <br>2) Start your stream/recording for about 30 seconds. Make sure you replicate any issues as best you can, which means having any games/apps open and captured, etc. <br>3) Stop your stream/recording. <br>4) Select Help > Log Files > Upload Current Log File. Send that link via this troubleshooting tool or whichever support chat you are using."


def checkClassic(lines):
    if (len(search(': Open Broadcaster Software v0.', lines)) > 0):
        return True, [LEVEL_CRITICAL, "OBS Classic",
                      """You are still using OBS Classic. This version is no longer supported. While we cannot and will not do anything to prevent you from using it, we cannot help with any issues that may come up. <br>It is recommended that you update to OBS Studio. <br><br>Further information on why you should update (and how): <a href="https://obsproject.com/forum/threads/how-to-easily-switch-to-obs-studio.55820/">OBS Classic to OBS Studio</a>."""]
    else:
        return False, [LEVEL_NONE, "OBS Studio", "Nothing to say"]


def checkDual(lines):
    if (len(search('Warning: OBS is already running!', lines)) > 0):
        return [LEVEL_CRITICAL, "Two Instances",
                "Two instances of OBS are running. If you are not intentionally running two instances, they will likely interfere with each other and consume excessive resources. Stop one of them. Check Task Manager for stray OBS processes if you can't find the other one."]


def checkAutoconfig(lines):
    if (len(search('Auto-config wizard', lines)) > 0):
        return [LEVEL_CRITICAL, "Auto-Config Wizard",
                "The log contains an Auto-Config Wizard run. Results of this analysis are therefore inaccurate. Please post a link to a clean log file. " + cleanLog]


def checkCPU(lines):
    cpu = search('CPU Name', lines)
    if (len(cpu) > 0):
        if (('APU' in cpu[0]) or ('Pentium' in cpu[0]) or ('Celeron' in cpu[0])):
            return [LEVEL_CRITICAL, "Insufficient Hardware",
                    "Your system is below minimum specs for OBS to run and may be too underpowered to livestream. There are no recommended settings we can suggest, but try the Auto-Config Wizard in the Tools menu. You may need to upgrade or replace your computer for a better experience."]
        elif ('i3' in cpu[0]):
            return [LEVEL_INFO, "Insufficient Hardware",
                    "Your system is below minimum specs for OBS to run and is too underpowered to livestream using software encoding. Livestreams and recordings will only run smoothly if you are using the hardware QuickSync encoder (via Settings -> Output)."]


def getOBSVersionLine(lines):
    versionLines = search('OBS', lines)
    correctLine = 0
    if 'already running' in versionLines[correctLine]:
        correctLine += 1
    if 'multiple instances' in versionLines[correctLine]:
        correctLine += 1
    return versionLines[correctLine]


def getOBSVersionString(lines):
    versionLine = getOBSVersionLine(lines)
    if versionLine.split()[0] == 'OBS':
        versionString = versionLine.split()[1]
    elif versionLine.split()[2] == 'OBS':
        versionString = versionLine.split()[3]
    else:
        versionString = versionLine.split()[2]
    return versionString


obsver_re = re.compile(r"""
    (?i)
    (?P<ver_major>[0-9]+)
    \.
    (?P<ver_minor>[0-9]+)
    \.
    (?P<ver_micro>[0-9]+)
    (
        -
        (?P<special> (?P<special_type> rc|beta) \d*)
    )?
    $
    """, re.VERBOSE)


def checkObsVersion(lines):
    versionString = getOBSVersionString(lines)

    if parse_version(versionString) == parse_version('21.1.0'):
        return [LEVEL_WARNING, "Broken Auto-Update",
                """You are not running the latest version of OBS Studio. Automatic updates in version 21.1.0 are broken due to a bug. <br>Please update by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it."""]

    m = obsver_re.search(versionString.replace('-modified', ''))

    if m is None and re.match(r"(?:\d)+\.(?:\d)+\.(?:\d)+\+(?:[\d\w\-\.~\+])+", versionString):
        return [LEVEL_INFO, "Unofficial OBS Build (%s)" % (html.escape(versionString)), """Your OBS version identifies itself as '%s', which is not an official build. <br>If you are on Linux, ensure you're using the PPA. If you cannot switch to the PPA, contact the maintainer of the package for any support issues.""" % (html.escape(versionString))]
    if m is None and re.match(r"(?:\d)+\.(?:\d)+\.(?:\d\w)+(?:-caffeine)", versionString):
        return [LEVEL_INFO, "Third party OBS Version (%s)" % (html.escape(versionString)), """Your OBS version identifies itself as '%s', which is made by a third party. Contact them for any support issues.""" % (html.escape(versionString))]
    if m is None and re.match(r"(?:\d)+\.(?:\d)+\.(?:\d)+-(?:[\d-])*([a-z0-9]+)(?:-modified){0,1}", versionString):
        return [LEVEL_INFO, "Custom OBS Build (%s)" % (html.escape(versionString)), """Your OBS version identifies itself as '%s', which is not a released OBS version.""" % (html.escape(versionString))]
    if m is None:
        return [LEVEL_INFO, "Unparseable OBS Version (%s)" % (html.escape(versionString)), """Your OBS version identifies itself as '%s', which cannot be parsed as a valid OBS version number.""" % (html.escape(versionString))]

    # Do we want these to check the version number and tell the user that a
    # release version is actually available, if one is actually available?
    # We can consider adding something like that later.
    if m.group("special") is not None:
        if m.group("special_type") == "beta":
            return [LEVEL_INFO, "Beta OBS Version (%s)" % (html.escape(versionString)), """You are running a beta version of OBS. There is nothing wrong with this, but you may experience problems that you may not experience with fully released OBS versions. You are encouraged to upgrade to a released version of OBS as soon as one is available."""]

        if m.group("special_type") == "rc":
            return [LEVEL_INFO, "Release Candidate OBS Version (%s)" % (html.escape(versionString)), """You are running a release candidate version of OBS. There is nothing wrong with this, but you may experience problems that you may not experience with fully released OBS versions. You are encouraged to upgrade to a released version of OBS as soon as one is available."""]

    if parse_version(versionString.replace('-modified', '')) < parse_version(CURRENT_VERSION):
        return [LEVEL_WARNING, "Old Version",
                """You are not running the latest version of OBS Studio. Please update by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it."""]


def checkGPU(lines):
    versionString = getOBSVersionString(lines)
    if parse_version(versionString) < parse_version('23.2.1'):
        adapters = search('Adapter 1', lines)
        try:
            adapters.append(search('Adapter 2', lines)[0])
        except IndexError:
            pass
    else:
        adapters = search('Adapter 0', lines)
        try:
            adapters.append(search('Adapter 1', lines)[0])
        except IndexError:
            pass
    d3dAdapter = search('Loading up D3D11', lines)
    if (len(d3dAdapter) > 0):
        if (len(adapters) == 2 and ('Intel' in d3dAdapter[0])):
            return [LEVEL_CRITICAL, "Wrong GPU",
                    """Your Laptop has two GPUs. OBS is running on the weak integrated Intel GPU. For better performance as well as game capture being available you should run OBS on the dedicated GPU. Check the <a href="https://obsproject.com/wiki/Laptop-Troubleshooting">Laptop Troubleshooting Guide</a>."""]
        if (len(adapters) == 2 and ('Vega' in d3dAdapter[0])):
            return [LEVEL_CRITICAL, "Wrong GPU",
                    """Your Laptop has two GPUs. OBS is running on the weak integrated AMD Vega GPU. For better performance as well as game capture being available you should run OBS on the dedicated GPU. Check the <a href="https://obsproject.com/wiki/Laptop-Troubleshooting">Laptop Troubleshooting Guide</a>."""]
        elif (len(adapters) == 1 and ('Intel' in adapters[0])):
            return [LEVEL_WARNING, "Integrated GPU",
                    "OBS is running on an Intel iGPU. This hardware is generally not powerful enough to be used for both gaming and running obs. Situations where only sources from e.g. cameras and capture cards are used might work."]


refresh_re = re.compile(r"""
    (?i)
    output \s+ (?P<output_num>[0-9]+):
    .*
    refresh = (?P<refresh> [0-9.]+),
    """, re.VERBOSE)


def getMonitorRefreshes(lines):
    refreshes = {}

    refreshLines = search('refresh=', lines)

    for rl in refreshLines:
        m = refresh_re.search(rl)

        if m is not None:
            output = int(m.group("output_num"))
            refresh = float(m.group("refresh"))

            refreshes[output] = refresh

    return refreshes


def checkRefreshes(lines):
    refreshes = getMonitorRefreshes(lines)
    verinfo = getWindowsVersion(lines)

    # Our log doesn't have any refresh rates, so bail
    if len(refreshes) == 0:
        return

    # Couldn't figure out windows version
    if not verinfo:
        return

    # We don't care about refresh rates on Vista
    if verinfo["version"] == "6.1":
        return

    # If we know nothing about the windows version (Insider build?),
    # assume mixed refresh is fine
    if verinfo["version"] == "10.0" and "release" not in verinfo:
        return

    # FINALLY fixed in WIn10/2004
    if verinfo["version"] and verinfo["release"] >= 2004:
        return

    # We're on a version that has the mixed-refresh-rate problem, so lets
    # build a dict of the refresh rates we have, and see if it's bigger
    # than a single element. We're going to round each entry as we add
    # it, so that (e.g.) 59.94Hz and 60Hz are considered the same, since
    # that doesn't really cause a problem.
    r = {}
    for _, hz in refreshes.items():
        r[round(hz)] = True

    if len(r) > 1:
        return [LEVEL_WARNING, "Mismatched Refresh Rates",
                "The version of Windows you are running has a limitation which causes performance issues in hardware accelerated applications (such as games) if multiple monitors with different refresh rates are present. Your system's monitors have " + str(len(r)) + """ different refresh rates, so you are affected by this limitation. <br><br>To fix this issue, we recommend updating to the Windows 10 May 2020 Update. Follow <a href="https://blogs.windows.com/windowsexperience/2020/05/27/how-to-get-the-windows-10-may-2020-update/">these instructions</a> if you're not sure how to update."""]
    return

samples_re = re.compile(r"""
    (?i)
    samples \sper \ssec:
    \s*
    (?P<samples>\d+)
""" , re.VERBOSE)

sample_re = re.compile(r"""
    (?i)
    WASAPI:
    .*
    '(?P<device>.*)'
    .*
    \[(?P<sample>\d{2,12})\sHz\]
    .*
""", re.VERBOSE)

def getWasapiSampleRates(lines):
    samples = {}
    sampleLines = search(' Hz] initialized', lines)

    for sl in sampleLines:
            m = sample_re.search(sl)

            if m is not None:
                device = str(m.group('device'))
                sample = int(m.group('sample'))

                samples[device] = sample

    return samples

def checkWasapiSamples(lines):
    obsSampleLines = search('samples per sec: ', lines)
    obsSample = ""
    for osl in obsSampleLines:
        m = samples_re.search(osl)
        if m is not None:
            obsSample = int(m.group('samples'))
    samples = getWasapiSampleRates(lines)

    if len(samples) == 0:
        return

    s = {}
    if obsSample != "":
        s[round(obsSample)] = True
    for _, hz in samples.items():
        s[round(hz)] = True

    if len(s) > 1:
        smpls = ""
        if obsSample != "":
            smpls += "<br>OBS Sample Rate: <strong>" + str(obsSample) + "</strong> Hz"
        for d, hz in samples.items():
            smpls += "<br>" + d + ": <strong>" + str(hz) + "</strong> Hz"
        return [LEVEL_WARNING, "Mismatched Sample Rates",
            "At least one of your audio devices has a sample rate that doesn't match the rest. This can result in audio drift over time or sound distortion. Check your audio devices in Windows settings (both Playback and Recording) and ensure the Default Format (under Advanced) is consistent. 48000 Hz is recommended." + smpls]

def checkMicrosoftSoftwareGPU(lines):
    if (len(search('Microsoft Basic Render Driver', lines)) > 0):
        return [LEVEL_CRITICAL, "No GPU driver available",
                "Your GPU is using the Microsoft Basic Render Driver, which is a pure software render. This will cause very high CPU load when used with OBS. Make sure to install proper drivers for your GPU. To use OBS in a virtual machine, you need to enable GPU passthrough."]


def checkOpenGLonWindows(lines):
    opengl = search('Warning: The OpenGL renderer is currently in use.', lines)
    if (len(opengl) > 0):
        return [LEVEL_CRITICAL, "OpenGL Renderer",
                "The OpenGL renderer should not be used on Windows, as it is not well optimized and can have visual artifacting. Switch back to the Direct3D renderer in Settings > Advanced."]


def checkGameDVR(lines):
    if search('Game DVR Background Recording: On', lines):
        return [LEVEL_WARNING, "Windows 10 Game DVR",
                """To ensure that OBS Studio has the hardware resources it needs for realtime streaming and recording, we recommend disabling the "Game DVR Background Recording" feature via <a href="https://obsproject.com/wiki/How-to-disable-Windows-10-Gaming-Features#game-dvrcaptures">these instructions</a>."""]


def checkGameMode(lines):
    verinfo = getWindowsVersion(lines)

    if not verinfo or verinfo["version"] != "10.0":
        return

    if verinfo["version"] == "10.0" and "release" not in verinfo:
        return

    if search("Game Mode: On", lines) and verinfo["release"] < 1809:
        return [LEVEL_WARNING, "Windows 10 Game Mode",
                """In some versions of Windows 10 (prior to version 1809), the "Game Mode" feature interferes with OBS Studio's normal functionality by starving it of CPU and GPU resources. We recommend disabling it via <a href="https://obsproject.com/wiki/How-to-disable-Windows-10-Gaming-Features#game-mode">these instructions</a>."""]

    # else
    if search("Game Mode: Off", lines):
        return [LEVEL_INFO, "Windows 10 Game Mode",
                """In Windows 10 versions 1809 and newer, we recommend that "Game Mode" be enabled for maximum gaming performance. Game Mode can be enabled via the Windows 10 "Settings" app, under Gaming > <a href="ms-settings:gaming-gamemode">Game Mode</a>."""]

def checkWin10Hags(lines):
    if search('Hardware GPU Scheduler: On', lines):
        return [LEVEL_CRITICAL, "Hardware-accelerated GPU Scheduler",
                """The new Windows 10 Hardware-accelerated GPU scheduling ("HAGS") added with version 2004 is currently known to cause performance and capture issues with OBS, games and overlay tools. It's a new and experimental feature and we recommend disabling it via <a href="ms-settings:display-advancedgraphics">this screen</a> or <a href="https://obsproject.com/wiki/How-to-disable-Windows-10-Hardware-GPU-Scheduler">these instructions</a>."""]

def checkNVENC(lines):
    msgs = search("Failed to open NVENC codec", lines)
    if (len(msgs) > 0):
        return [LEVEL_WARNING, "NVENC Start Failure",
                """The NVENC Encoder failed to start due of a variety of possible reasons. Make sure that Windows Game Bar and Windows Game DVR are disabled and that your GPU drivers are up to date. <br><br>You can perform a clean driver installation for your GPU by following the instructions at <a href="http://obsproject.com/forum/resources/performing-a-clean-gpu-driver-installation.65/"> Clean GPU driver installation</a>. <br>If this doesn't solve the issue, then it's possible your graphics card doesn't support NVENC. You can change to a different Encoder in Settings > Output."""]


def check940(lines):
    gpu = search('NVIDIA GeForce 940', lines)
    attempt = search('NVENC encoder', lines)
    if (len(gpu) > 0) and (len(attempt) > 0):
        return [LEVEL_CRITICAL, "NVENC Not Supported",
                """The NVENC Encoder is not supported on the NVIDIA 940 and 940MX. Recording fails to start because of this. Please select "Software (x264)" or "Hardware (QSV)" as encoder instead in Settings > Output."""]


def checkInit(lines):
    if (len(search('Failed to initialize video', lines)) > 0):
        return [LEVEL_CRITICAL, "Initialize Failed",
                "Failed to initialize video. Your GPU may not be supported, or your graphics drivers may need to be updated."]


def checkKiller(lines):
    if(len(search('Interface: Killer', lines)) > 0):
        return [LEVEL_INFO, "Killer NIC",
                """Killer's Firewall is known for it's poor performance and issues when trying to stream. Please download the driver pack from <a href="https://www.killernetworking.com/killersupport/driver-downloads/category/other-downloads">the vendor's page</a> , completely uninstall all Killer NIC items and install their Driver only package."""]


def checkWifi(lines):
    if (len(search('802.11', lines)) > 0):
        return [LEVEL_WARNING, "Wi-Fi Streaming",
                "In many cases, wireless connections can cause issues because of their unstable nature. Streaming really requires a stable connection. Often wireless connections are fine, but if you have problems, the first troubleshooting step would be to switch to wired. We highly recommend streaming on wired connections."]


def checkBind(lines):
    if (len(search('Binding to ', lines)) > 0):
        return [LEVEL_WARNING, "Binding to IP",
                """Binding to a manually chosen IP address is rarely needed. Go to Settings -> Advanced -> Network and set "Bind to IP" back to "Default"."""]


# Log line examples:
# win 7: 19:39:17.395: Windows Version: 6.1 Build 7601 (revision: 24535; 64-bit)
# win 10: 15:30:58.866: Windows Version: 10.0 Build 19041 (release: 2004; revision: 450; 64-bit)
def getWindowsVersionLine(lines):
    versionLines = search('Windows Version:', lines)
    if len(versionLines) > 0:
        return versionLines[0]


winver_re = re.compile(r"""
    (?i)
    Windows\sVersion: \s+ (?P<version>[0-9.]+)
    \s+
    Build \s+ (?P<build>\d+)
    \s+
    \(
        (release: \s+ (?P<release>\d|\w+); \s+)?
        revision: \s+ (?P<revision>\d+);
        \s+
        (?P<bits>\d+)-bit
    \)
    """, re.VERBOSE)

# I guess I'll call the Win10 sub-versions "releases", even though Microsoft
# calls them "versions" because Win10 is also "Version 10.0".
#
# We probably don't need all the info here, but it comes in handy
win10versions = {
    10240: {
        "release": 1507,
        "name": "Windows 10 1507",
        "date": datetime.date(2015, 7, 29),
        "EoS": datetime.date(2017, 5, 9),
    },
    10586: {
        "release": 1511,
        "name": "Windows 10 1511",
        "date": datetime.date(2015, 11, 10),
        "EoS": datetime.date(2017, 10, 10),
    },
    14393: {
        "release": 1607,
        "name": "Windows 10 1607",
        "date": datetime.date(2016, 8, 2),
        "EoS": datetime.date(2018, 4, 10),
    },
    15063: {
        "release": 1703,
        "name": "Windows 10 1703",
        "date": datetime.date(2017, 4, 5),
        "EoS": datetime.date(2018, 10, 9),
    },
    16299: {
        "release": 1709,
        "name": "Windows 10 1709",
        "date": datetime.date(2017, 10, 17),
        "EoS": datetime.date(2019, 4, 9),
    },
    17134: {
        "release": 1803,
        "name": "Windows 10 1803",
        "date": datetime.date(2018, 4, 30),
        "EoS": datetime.date(2019, 11, 12),
    },
    17763: {
        "release": 1809,
        "name": "Windows 10 1809",
        "date": datetime.date(2018, 11, 13),
        "EoS": datetime.date(2020, 11, 10),
    },
    18362: {
        "release": 1903,
        "name": "Windows 10 1903",
        "date": datetime.date(2019, 5, 21),
        "EoS": datetime.date(2020, 12, 8),
    },
    18363: {
        "release": 1909,
        "name": "Windows 10 1909",
        "date": datetime.date(2019, 11, 12),
        "EoS": datetime.date(2021, 5, 11),
    },
    19041: {
        "release": 2004,
        "name": "Windows 10 2004",
        "date": datetime.date(2020, 5, 27)
    },
}

winversions = {
    "6.1": {
        "name": "Windows 7",
        "date": datetime.date(2012, 10, 26),
        "EoS": datetime.date(2020, 1, 14),
    },
    "6.2": {
        "name": "Windows 8",
        "date": datetime.date(2013, 10, 17),
        "EoS": datetime.date(2016, 1, 12),
    },
    "6.3": {
        "name": "Windows 8.1",
        "date": datetime.date(2013, 10, 17),
        "EoS": datetime.date(2023, 1, 10),
    },
}


def getWindowsVersion(lines):
    versionLine = getWindowsVersionLine(lines)

    if not versionLine:
        return

    m = winver_re.search(versionLine)
    if not m:
        return

    ver = {
        "version": m.group("version"),
        "build": int(m.group("build")),
        "revision": int(m.group("revision")),
        "bits": int(m.group("bits")),
        "release": 0
    }

    # Older naming/numbering/etc
    if ver["version"] in winversions:
        v = winversions[ver["version"]]
        ver.update(v)
        return ver

    if ver["version"] == "10.0":
        if ver["build"] in win10versions:
            v = win10versions[ver["build"]]
            ver.update(v)
        return ver

    return


def checkWindowsVer(lines):
    verinfo = getWindowsVersion(lines)
    if not verinfo:
        return

    # This is such a hack, but it's unclear how to do this better
    if verinfo["version"] == "10.0" and verinfo["release"] is 0:
        msg = "You are running an unknown Windows 10 release (build %d), which means you are probably using an Insider build. Some checks that are applicable only to specific Windows versions will not be performed. Also, because Insider builds are test versions, you may have problems that would not happen with release versions of Windows." % (
            verinfo["build"])
        return[LEVEL_WARNING, "Windows 10 Version Unknown", msg]

    if "EoS" in verinfo and datetime.date.today() > verinfo["EoS"]:
        wv = "%s (EOL)" % (html.escape(verinfo["name"]))
        msg = "You are running %s, which has not been supported by Microsoft since <strong>%s</strong>. We recommend updating to the latest Windows release to ensure continued security, functionality, and compatibility." % (
            html.escape(verinfo["name"]), verinfo["EoS"].strftime("%B %Y"))
        return [LEVEL_WARNING, wv, msg]

    # special case for OBS 24.0.3 and earlier, which report Windows 10/1909
    # as being Windows 10/1903
    versionString = getOBSVersionString(lines)
    if parse_version(versionString) <= parse_version("24.0.3"):
        if verinfo["version"] == "10.0" and verinfo["release"] == 1903:
            return [LEVEL_INFO, "Windows 10 1903/1909",
                    "Due to a bug in OBS versions 24.0.3 and earlier, the exact release of Windows 10 you are using cannot be determined. You are using either release 1903, or release 1909. Fortunately, there were no major changes in behavior between Windows 10 release 1903 and Windows 10 release 1909, and instructions given here for release 1903 can also be used for release 1909, and vice versa."]

    # our windows version isn't out of support, so just say what version the user has and when
    # it actually does go out of support
    wv = "%s (OK)" % (html.escape(verinfo["name"]))

    if "EoS" in verinfo:
        msg = "You are running %s, which will be supported by Microsoft until <strong>%s</strong>." % (
            html.escape(verinfo["name"]), verinfo["EoS"].strftime("%B %Y"))
    else:
        msg = "You are running %s, for which Microsoft has not yet announced an end of life date." % (
            html.escape(verinfo["name"]))

    return [LEVEL_INFO, wv, msg]


def checkAdmin(lines):
    adminlines = search('Running as administrator', lines)
    if ((len(adminlines) > 0) and (adminlines[0].split()[-1] == 'false')):
        renderlag = getRenderLag(lines)

        if renderlag >= 3:
            return [LEVEL_WARNING, "Not Admin",
                    "OBS is not running as Administrator. Because of this, OBS will not be able to Game Capture certain games, and it will not be able to request a higher GPU priority for itself -- which is the likely cause of the render lag you are currently experincing. Run OBS as Administrator to help alleviate this problem."]

        # else
        return [LEVEL_INFO, "Not Admin",
                "OBS is not running as Administrator. This can lead to OBS not being able to Game Capture certain games. If you are not running into issues, you can ignore this."]


def check32bitOn64bit(lines):
    winVersion = search('Windows Version', lines)
    obsVersion = getOBSVersionLine(lines)
    if (len(winVersion) > 0
            and '64-bit' in winVersion[0]
            and '64-bit' not in obsVersion
            and '64bit' not in obsVersion):
        # thx to secretply for the bugfix
        return [LEVEL_WARNING, "32-bit OBS on 64-bit Windows",
                "You are running the 32 bit version of OBS on a 64 bit system. This will reduce performance and greatly increase the risk of crashes due to memory limitations. You should only use the 32 bit version if you have a capture device that lacks 64 bit drivers. Please run OBS using the 64-bit shortcut."]


def checkElements(lines):
    if (len(search('obs-streamelements', lines)) > 0):
        return [LEVEL_WARNING, "StreamElements OBS.Live",
                """The obs.live plugin is installed. This overwrites OBS' default browser source and causes a severe performance impact. To get rid of it, first, export your scene collections and profiles, second manually uninstall OBS completely, third reinstall OBS Studio only with the latest installer from <a href="https://obsproject.com/download">https://obsproject.com/download</a>"""]


def checkAMDdrivers(lines):
    if (len(search('The AMF Runtime is very old and unsupported', lines)) > 0):
        return [LEVEL_WARNING, "AMD Drivers",
                """The AMF Runtime is very old and unsupported. The AMF Encoder will no work properly or not show up at all. Consider updating your drivers by downloading the newest installer from <a href="https://support.amd.com/en-us/download">AMD's website</a>. """]


def checkNVIDIAdrivers(lines):
    if (len(search('[jim-nvenc] Current driver version does not support this NVENC version, please upgrade your driver', lines)) > 0):
        return [LEVEL_WARNING, "Old NVIDIA Drivers",
                """The installed NVIDIA driver does not support NVENC features needed for optimized encoders. Consider updating your drivers by downloading the newest installer from<a href="https://www.nvidia.de/Download/index.aspx">NVIDIA's website</a>. """]


def checkMP4(lines):
    writtenFiles = search('Writing file ', lines)
    mp4 = search('.mp4', writtenFiles)
    mov = search('.mov', writtenFiles)
    if (len(mp4) > 0 or len(mov) > 0):
        return [LEVEL_CRITICAL, "MP4/MOV Recording",
                "Record to FLV or MKV. If you record to MP4 or MOV and the recording is interrupted, the file will be corrupted and unrecoverable. <br><br>If you require MP4 files for some other purpose like editing, remux them afterwards by selecting File > Remux Recordings in the main OBS Studio window."]


def checkAttempt(lines):
    recordingStarts = search('== Recording Start ==', lines)
    streamingStarts = search('== Streaming Start ==', lines)
    if (len(recordingStarts) + len(streamingStarts) == 0):
        return [LEVEL_INFO, "No Output Session",
                "Your log contains no recording or streaming session. Results of this log analysis are limited. Please post a link to a clean log file. " + cleanLog]


def checkPreset(lines):
    encoderLines = search('x264 encoder:', lines)
    presets = search('preset: ', lines)
    sensiblePreset = True
    for l in presets:
        if (not (('veryfast' in l) or ('superfast' in l) or ('ultrafast' in l))):
            sensiblePreset = False

    if ((len(encoderLines) > 0) and (not sensiblePreset)):
        return [LEVEL_INFO, "Non-Default x264 Preset",
                "A slower x264 preset than 'veryfast' is in use. It is recommended to leave this value on veryfast, as there are significant diminishing returns to setting it lower. It can also result in very poor gaming performance on the system if you're not using a 2 PC setup."]


def checkCustom(lines):
    encoderLines = search("'adv_ffmpeg_output':", lines)
    if (len(encoderLines) > 0):
        return [LEVEL_WARNING, "Custom FFMPEG Output",
                """Custom FFMPEG output is in use. Only absolute professionals should use this. If you got your settings from a YouTube video advertising "Absolute best OBS settings" then we recommend using one of the presets in Simple output mode instead."""]


audiobuf_re = re.compile(r"""
    (?i)
    adding \s (?P<added> \d+) \s milliseconds \s of \s audio \s buffering
    , \s
    total \s audio \s buffering \s is \s now \s (?P<total> \d+) \s milliseconds
    (
        \s
        \( source: (?P<source> .*) \)
    )?
    $
    """, re.VERBOSE)


def checkAudioBuffering(lines):
    maxBuffering = searchWithIndex('Max audio buffering reached!', lines)
    if (len(maxBuffering) > 0):
        # This doesn't correspond to a specific amount of time -- it's
        # emitted if the delay is greater than MAX_BUFFERING_TICKS, and that
        # amount of time varies by sample rate. Unfortunately, the max
        # buffering reached message doesn't directly say which audio source
        # was the offender. Is it worth just ditching this check and using
        # the "greater than 500ms" check, which could potentially also easily
        # know the specific device?
        append = ""
        for line, index in maxBuffering:
            if (len(lines) > index):
                m = audiobuf_re.search(lines[index + 1].replace('\r', ''))
                if m.group("source"):
                    append += "<br><br>Source affected (potential cause):<strong>" + m.group("source") + "</strong>"
                    break
        return [LEVEL_CRITICAL, "Max Audio Buffering",
                "Audio buffering hit the maximum value. This is an indicator of very high system load, will affect stream latency, and may even cause individual audio sources to stop working. Keep an eye on CPU usage especially, and close background programs if needed. <br><br>Occasionally, this can be caused by incorrect device timestamps. Restart OBS to reset buffering." + append]

    buffering = search('total audio buffering is now', lines)
    vals = [0, ]
    if (len(buffering) > 0):
        for i in buffering:
            m = audiobuf_re.search(i)
            if m:
                vals.append(int(m.group("total")))

        if (max(vals) > 500):
            return [LEVEL_WARNING, "High Audio Buffering",
                    "Audio buffering reached values above 500ms. This is an indicator of very high system load and will affect stream latency. Keep an eye on CPU usage especially, and close background programs if needed. Restart OBS to reset buffering."]

    return None


def checkMulti(lines):
    mem = search('user is forcing shared memory', lines)
    if (len(mem) > 0):
        return [LEVEL_WARNING, "Memory Capture",
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
            severity = LEVEL_CRITICAL
        elif (15 > val and val >= 5):
            severity = LEVEL_WARNING
        else:
            severity = LEVEL_INFO
    return [severity, "{}% Dropped Frames".format(val),
            """Your log contains streaming sessions with dropped frames. This can only be caused by a failure in your internet connection or your networking hardware. It is not caused by OBS. Follow the troubleshooting steps at: <a href="https://obsproject.com/wiki/Dropped-Frames-and-General-Connection-Issues">Dropped Frames and General Connection Issues</a>."""]


def getRenderLag(lines):
    drops = search('rendering lag', lines)
    val = 0
    severity = 9000
    for drop in drops:
        v = float(drop[drop.find("(") + 1: drop.find(")")
                       ].strip('%').replace(",", "."))
        if (v > val):
            val = v

    return val


def checkRenderLag(lines):
    val = getRenderLag(lines)

    if (val != 0):
        if (val >= 10):
            severity = LEVEL_CRITICAL
        elif (10 > val and val >= 3):
            severity = LEVEL_WARNING
        else:
            severity = LEVEL_INFO

        return [severity, "{}% Rendering Lag".format(val),
                """Your GPU is maxed out and OBS can't render scenes fast enough. Running a game without vertical sync or a frame rate limiter will frequently cause performance issues with OBS because your GPU will be maxed out. OBS requires a little GPU to render your scene. <br><br>Enable Vsync or set a reasonable frame rate limit that your GPU can handle without hitting 100% usage. <br><br>If that's not enough you may also need to turn down some of the video quality options in the game. If you are experiencing issues in general while using OBS, your GPU may be overloaded for the settings you are trying to use.<br><br>Please check our guide for ideas why this may be happening, and steps you can take to correct it: <a href="https://obsproject.com/wiki/GPU-overload-issues">GPU Overload Issues</a>."""]


def checkEncodeError(lines):
    if (len(search('Error encoding with encoder', lines)) > 0):
        return [LEVEL_INFO, "Encoder start error",
                """An encoder failed to start. This could result in a bitrate stuck at 0 or OBS stuck on "Stopping Recording". Depending on your encoder, try updating your drivers. If you're using QSV, make sure your iGPU is enabled. If that still doesn't help, try switching to a different encoder in Settings -> Output."""]


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
            severity = LEVEL_CRITICAL
        elif (15 > val and val >= 5):
            severity = LEVEL_WARNING
        else:
            severity = LEVEL_INFO
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
            return [LEVEL_INFO, "Low Stream Bitrate",
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
            return [LEVEL_INFO, "Low Stream Bitrate",
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
            res.append([LEVEL_WARNING, "Non-Standard Aspect Ratio",
                        "Almost all modern streaming services and video platforms expect video in 16:9 aspect ratio. OBS is currently configured to record in an aspect ration that differs from that. You (or your viewers) will see black bars during playback. Go to Settings -> Video and change your Canvas Resolution to one that is 16:9."])
        if (fmt != 'NV12'):
            res.append([LEVEL_CRITICAL, "Wrong Color Format",
                        "Color Formats other than NV12 are primarily intended for recording, and are not recommended when streaming. Streaming may incur increased CPU usage due to color format conversion. You can change your Color Format in Settings -> Advanced."])
        if (not ((fps == 60) or (fps == 30))):
            res.append([LEVEL_WARNING, "Non-Standard Framerate",
                        "Framerates other than 30fps or 60fps may lead to playback issues like stuttering or screen tearing. Stick to either of these for better compatibility with video players. You can change your OBS frame rate in Settings -> Video."])
        if (fps >= 144):
            res.append([LEVEL_WARNING, "Excessively High Framerate",
                        "Recording at a tremendously high framerate will not give you higher quality recordings. Usually quite the opposite. Most computers cannot handle encoding at high framerates. You can change your OBS frame rate in Settings -> Video."])
        if 'Full' in yuv:
            res.append([LEVEL_WARNING, "Wrong YUV Color Range",
                        """Having the YUV Color range set to "Full" will cause playback issues in certain browsers and on various video platforms. Shadows, highlights and color will look off. In OBS, go to "Settings -> Advanced" and set "YUV Color Range" back to "Partial"."""])
    return res

nicspeed_re = re.compile(r"(?i)Interface: (?P<nicname>.+) \(ethernet, (?P<speed>\d+) mbps\)")

def checkNICSpeed(lines):
    nicLines = search('Interface: ', lines)
    if (len(nicLines) > 0):
        for i in nicLines:
            m = nicspeed_re.search(i)
            if m:
                nic = m.group("nicname")
                speed = int(m.group("speed"))
                if speed < 1000:
                    if 'GbE' in nic or 'Gigabit' in nic:
                        return [LEVEL_WARNING, "Slow Network Connection", "Your gigabit-capable network card is only connecting at 100mbps. This may indicate a bad network cable or outdated router / switch which could be impacting network performance."]
    return None


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
        res.append([LEVEL_WARNING, "Capture Interference",
                    "Display and Game Capture Sources interfere with each other. Never put them in the same scene."])
    if (len(game) > 1):
        if (res is None):
            res = []
        violation = True
        res.append([LEVEL_WARNING, "Multiple Game Capture",
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


# main functions
##############################################


def textOutput(string):
    dedented_text = textwrap.dedent(string).strip()
    return textwrap.fill(dedented_text, initial_indent=' ' * 4, subsequent_indent=' ' * 4, width=80, )


def getSummary(messages):
    summary = ""
    critical = []
    warning = []
    info = []
    for i in messages:
        if (i[0] == LEVEL_CRITICAL):
            critical.append(i[1])
        elif (i[0] == LEVEL_WARNING):
            warning.append(i[1])
        elif (i[0] == LEVEL_INFO):
            info.append(i[1])
    summary += "{}Critical: {}\n".format(RED, ", ".join(critical))
    summary += "{}Warning:  {}\n".format(YELLOW, ", ".join(warning))
    summary += "{}Info:     {}\n".format(CYAN, ", ".join(info))
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

    results += "{} \n".format(RESET)
    return results


def doAnalysis(url=None, filename=None):
    messages = []
    success = False
    logLines = []

    if url is not None:
        matchGist = re.match(
            r"(?i)\b((?:https?:(?:/{1,3}gist\.github\.com)/)(anonymous/)?([a-z0-9]{32}))", url)
        matchHaste = re.match(
            r"(?i)\b((?:https?:(?:/{1,3}(www\.)?hastebin\.com)/)([a-z0-9]{10}))", url)
        matchObs = re.match(
            r"(?i)\b((?:https?:(?:/{1,3}(www\.)?obsproject\.com)/logs/)(.{16}))", url)
        matchPastebin = re.match(
            r"(?i)\b((?:https?:(?:/{1,3}(www\.)?pastebin\.com/))(?:raw/)?(.{8}))", url)
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

    elif filename is not None:
        logLines = getLinesLocal(filename)
        messages.append(getDescription(logLines))
        success = True

    if (success):
        classic, m = checkClassic(logLines)
        messages.append(m)
        if (not classic):
            messages.append(checkObsVersion(logLines))
            messages.append(checkDual(logLines))
            messages.append(checkAutoconfig(logLines))
            messages.append(checkCPU(logLines))
            messages.append(checkAMDdrivers(logLines))
            messages.append(checkNVIDIAdrivers(logLines))
            messages.append(checkGPU(logLines))
            messages.append(checkRefreshes(logLines))
            messages.append(checkInit(logLines))
            # messages.append(checkElements(logLines))
            messages.append(checkNVENC(logLines))
            messages.append(check940(logLines))
            messages.append(checkKiller(logLines))
            messages.append(checkWifi(logLines))
            messages.append(checkBind(logLines))
            messages.append(checkWindowsVer(logLines))
            messages.append(checkAdmin(logLines))
            messages.append(check32bitOn64bit(logLines))
            messages.append(checkAttempt(logLines))
            messages.append(checkMP4(logLines))
            messages.append(checkPreset(logLines))
            messages.append(checkCustom(logLines))
            messages.append(checkAudioBuffering(logLines))
            messages.append(checkDrop(logLines))
            messages.append(checkRenderLag(logLines))
            messages.append(checkEncodeError(logLines))
            messages.append(checkEncoding(logLines))
            messages.append(checkMulti(logLines))
            messages.append(checkStreamSettingsX264(logLines))
            messages.append(checkStreamSettingsNVENC(logLines))
            messages.append(checkMicrosoftSoftwareGPU(logLines))
            messages.append(checkWasapiSamples(logLines))
            messages.append(checkOpenGLonWindows(logLines))
            messages.append(checkGameDVR(logLines))
            messages.append(checkGameMode(logLines))
            messages.append(checkWin10Hags(logLines))
            messages.append(checkNICSpeed(logLines))
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
        messages.append([LEVEL_CRITICAL, "NO LOG",
                         "URL or file doesn't contain a log."])
    # print(messages)
    ret = [i for i in messages if i is not None]
    # print(ret)
    return (ret)


def main():
    parser = argparse.ArgumentParser()
    loggroup = parser.add_mutually_exclusive_group(required=True)

    loggroup.add_argument("--url", '-u', dest='url',
                          default=None, help="url of gist or haste with log")
    loggroup.add_argument("--file", "-f", dest='file',
                          default=None, help="local filenamne with log")
    flags = parser.parse_args()

    msgs = doAnalysis(url=flags.url, filename=flags.file)
    print(getSummary(msgs))
    print(getResults(msgs))


if __name__ == "__main__":
    main()
