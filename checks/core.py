import html
import re

from .vars import *
from .utils.utils import *
from .utils import obsversion


def checkClassic(lines):
    if (len(search(': Open Broadcaster Software v0.', lines)) > 0):
        return True, [LEVEL_CRITICAL, "OBS Classic",
                      """You are still using OBS Classic. This version is no longer supported. While we cannot and will not do anything to prevent you from using it, we cannot help with any issues that may come up. <br>It is recommended that you update to OBS Studio. <br><br>Further information on why you should update (and how): <a href="https://obsproject.com/forum/threads/how-to-easily-switch-to-obs-studio.55820/">OBS Classic to OBS Studio</a>."""]
    else:
        return False, [LEVEL_NONE, "OBS Studio", "Nothing to say"]


def checkCrash(lines):
    if (len(search('Unhandled exception:', lines)) > 0):
        return True, [LEVEL_CRITICAL, "Crash Log",
                      """You have uploaded a crash log. The Log Analyzer does not yet process crash logs."""]
    else:
        return False, [LEVEL_NONE, "OBS Studio Log", "Nothing to say"]


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
    versionPattern = re.compile(r': OBS \d+\.\d+\.\d+')
    versionLines = search('OBS', lines)
    for line in versionLines:
        if versionPattern.search(line):
            return line


def getOBSVersionString(lines):
    versionLine = getOBSVersionLine(lines)
    if versionLine:
        versionString = versionLine[versionLine.find("OBS"):]
        return versionString.split()[1]


def checkObsVersion(lines):
    version = obsversion.ObsVersion(getOBSVersionString(lines))

    if not version.parsed:
        return [LEVEL_INFO, f"Unparseable OBS Version ({html.escape(version.string)})",
                f"""Your OBS version identifies itself as '{html.escape(version.string)}', which cannot be parsed as a valid OBS version number."""]

    if version.modified:
        return [LEVEL_INFO, f"Custom OBS Build ({html.escape(version.string)})",
                f"""Your OBS version identifies itself as '{html.escape(version.string)}', which is not a released OBS version."""]

    if version.trail and 'caffeine' in version.trail:
        return [LEVEL_INFO, f"Third party OBS Version ({html.escape(version.string)})",
                f"""Your OBS version identifies itself as '{html.escape(version.string)}', which is made by a third party. Contact them for any support issues."""]

    if version.trail:
        if checkOperatingSystem(lines) == "linux":
            return [LEVEL_INFO, f"Unofficial OBS Build ({html.escape(version.string)})",
                    f"""Your OBS version identifies itself as '{html.escape(version.string)}', which is not an official build. <br> Only the PPA and the flatpak aare official releases. If you cannot or wish not switch to those, please contact the maintainer of your package for any support issues."""]
        else:
            return [LEVEL_INFO, f"Unofficial OBS Build ({html.escape(version.string)})",
                    f"""Your OBS version identifies itself as '{html.escape(version.string)}', which is not an official build. <br> Please contact the maintainer of your release for any support issues."""]

    if version.beta:
        if version.version.beta_type == version._beta_types["beta"]:
            if version < CURRENT_VERSION:
                return [LEVEL_WARNING, f"Outdated Beta OBS Version ({html.escape(version.string)})",
                        f"""The beta version of OBS you are running is outdated. It is recommended you update to version {CURRENT_VERSION} by going to Help -> Check for updates in OBS or by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it."""]
            else:
                return [LEVEL_INFO, f"Beta OBS Version ({html.escape(version.string)})",
                        f"""You are running a beta version of OBS. There is nothing wrong with this, but you may experience problems that you may not experience with fully released OBS versions. You are encouraged to upgrade to a released version of OBS as soon as one is available."""]

        if version.version.beta_type == version._beta_types["rc"]:
            if version < CURRENT_VERSION:
                return [LEVEL_WARNING, f"Outdated Release Candidate OBS Version ({html.escape(version.string)})",
                        f"""The release candidate version of OBS you are running is outdated. It is recommended you update to version {CURRENT_VERSION} by going to Help -> Check for updates in OBS or by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it."""]
            else:
                return [LEVEL_INFO, f"Release Candidate OBS Version ({html.escape(version.string)})",
                        f"""You are running a release candidate version of OBS. There is nothing wrong with this, but you may experience problems that you may not experience with fully released OBS versions. You are encouraged to upgrade to a released version of OBS as soon as one is available."""]

    if version < CURRENT_VERSION:
        return [LEVEL_WARNING, f"Old Version ({html.escape(version.string)})",
                f"""You are running an old version of OBS Studio ({html.escape(version.string)}). Please update to version {CURRENT_VERSION} by going to Help -> Check for updates in OBS or by downloading the latest installer from the <a href="https://obsproject.com/download">downloads page</a> and running it."""]


def checkOperatingSystem(lines):
    firstSection = lines[:getSubSections(lines)[0]]
    for s in firstSection:
        if 'mac' in s:
            return "mac"
        elif 'windows' in s:
            return "windows"
        elif 'linux' in s:
            return "linux"


def checkPortableMode(lines):
    if search('Portable mode: true', lines):
        return [LEVEL_INFO, "Portable Mode",
                """You are running OBS in Portable Mode. This means that OBS will store its settings with the executable. This is useful if you want to run OBS from a flash drive or other removable media."""]


def checkSafeMode(lines):
    if search('Safe Mode enabled.', lines):
        modulesNotLoaded = search('not on safe list', lines)
        moduleNames = []

        for line in modulesNotLoaded:
            found = re.search(r"'([^']+)'", line)
            if found:
                moduleNames.append(found.group(1))

        if moduleNames:
            modulesNotLoadedString = "<br>\n<ul>\n<li>" + "</li>\n<li>".join(moduleNames) + "</li>\n</ul>"
            return [LEVEL_WARNING, "Safe Mode Enabled (" + str(len(moduleNames)) + ")",
                    """You are running OBS in Safe Mode. Safe Mode disables third-party plugins and prevents scripts from running. The following modules were not loaded:""" + modulesNotLoadedString]
        else:
            return [LEVEL_WARNING, "Safe Mode Enabled",
                    """You are running OBS in Safe Mode. Safe Mode disables third-party plugins and prevents scripts from running."""]
