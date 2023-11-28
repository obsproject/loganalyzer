from checks.vars import *
import html

from .utils.utils import *
from .utils.macosversions import *


def getMacVersionLine(lines):
    isMac = search('OS Name: Mac OS X', lines) + search('OS Name: macOS', lines)
    macVersion = search('OS Version:', lines)
    if (len(isMac) > 0 and len(macVersion) > 0):
        return macVersion[0]


def getMacVersion(lines):
    versionLine = getMacVersionLine(lines)

    if not versionLine:
        return

    m = macver_re.search(versionLine)
    if not m:
        return

    ver = {
        "major": m.group("major"),
        "minor": m.group("minor"),
        "full": m.group("major") + "." + m.group("minor")
    }

    if ver["full"] in macversions:
        v = macversions[ver["full"]]
        ver.update(v)
        return ver

    if ver["major"] in macversions:
        v = macversions[ver["major"]]
        ver.update(v)
        return ver

    return


def checkMacVer(lines):
    verinfo = getMacVersion(lines)
    if not verinfo:
        return

    mv = "macOS %s.%s" % (html.escape(verinfo["major"]), html.escape(verinfo["minor"]))
    if (int(verinfo["major"]) <= 10 and "max" in verinfo):
        msg = "You are running %s %s, which is multiple versions out of date and no longer supported by Apple or recent OBS versions. We recommend updating to the latest macOS release to ensure continued security, functionality and compatibility." % (mv, html.escape(verinfo["name"]))
        mv += " (EOL)"
        return [LEVEL_WARNING, mv, msg]

    if "latest" in verinfo:
        msg = "You are running %s %s, which is currently supported by Apple and the most recent version of OBS." % (mv, html.escape(verinfo["name"]))
        mv += " (OK)"
        return [LEVEL_INFO, mv, msg]

    msg = "You are running %s %s, which is not officially supported by Apple but is compatible with the most recent version of OBS. Updating to a more recent version of macOS is recommended to ensure that you are able to install future versions of OBS." % (mv, html.escape(verinfo["name"]))
    mv += " (OK)"
    return [LEVEL_INFO, mv, msg]


def checkRosettaTranslationStatus(lines):
    if (len(search('Rosetta translation used: true', lines)) > 0):
        return [LEVEL_WARNING, "Intel OBS on Apple Silicon Mac",
                "You are running the Intel version of OBS on an Apple Silicon Mac. You may get improved performance using the Apple Silicon version of OBS."]


def checkMacPermissions(lines):
    macPerms = search('[macOS] Permission for', lines)
    deniedPermissions = []

    for line in macPerms:
        if 'denied' in line:
            found = re.search(r'Permission for (.+) denied', line)
            if found:
                permissionName = found.group(1).title()
                permissionDescription = {
                    "Audio Device Access": "<b>Microphone</b>: OBS requires this permission if you want to capture your microphone.",
                    "Video Device Access": "<b>Camera</b>: This permission is needed in order to capture content from a webcam or capture card.",
                    "Accessibility": "<b>Accessibility</b>: For keyboard shortcuts (hotkeys) to work while other apps are focused this permission is needed.",
                    "Screen Capture": "<b>Screen Recording</b>: OBS requires this permission to be able to capture your screen."
                }.get(permissionName)

                if permissionDescription:
                    deniedPermissions.append(permissionDescription)

    if deniedPermissions:
        deniedPermissionsString = "<br>\n<ul>\n<li>" + "</li>\n<li>".join(deniedPermissions) + "</li>\n</ul>"
        return [LEVEL_WARNING, "Permissions Not Granted (" + str(len(deniedPermissions)) + ")",
                """The following permissions have not been granted:""" + deniedPermissionsString + "If you would like to grant permissions for the above, follow the instructions in the " + '<a href="https://obsproject.com/kb/macos-permissions-guide">macOS Permissions Guide</a>.']
