import html
import re
from pkg_resources import parse_version

from .vars import *
from .utils.utils import *


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


def getOBSVersionLine(lines):
    versionLines = search('OBS', lines)
    correctLine = 0
    if 'already running' in versionLines[correctLine]:
        correctLine += 1
    if 'multiple instances' in versionLines[correctLine]:
        correctLine += 1
    if 'windows from screen capture' in versionLines[correctLine]:
        correctLine += 1
    return versionLines[correctLine]


def getOBSVersionString(lines):
    versionLine = getOBSVersionLine(lines)
    versionString = versionLine[versionLine.find("OBS"):]
    return versionString.split()[1]


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
        return [LEVEL_WARNING, "Old Version (%s)" % versionString,
                """You are running an old version of OBS Studio (%s). Please update to version %s by going to Help -> Check for updates in OBS or by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it.""" % (versionString, CURRENT_VERSION)]
