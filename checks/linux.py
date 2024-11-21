from .vars import *
from .utils.utils import *


def getSessionTypeLine(lines):
    sessionType = search('Session Type:', lines)
    if len(sessionType) > 0:
        return sessionType[0]


def getWindowSystemLine(lines):
    windowSystem = search('Window System:', lines)
    if len(windowSystem) > 0:
        return windowSystem[0]


def checkWayland(lines):
    isDistroNix = search('Distribution:', lines)
    isFlatpak = search('Flatpak Runtime:', lines)

    if (len(isDistroNix) <= 0) and (len(isFlatpak) <= 0):
        return

    sessionTypeLine = getSessionTypeLine(lines)
    if not sessionTypeLine:
        return

    sessionType = sessionTypeLine.split()[3]
    if sessionType != 'wayland':
        return

    if len(isDistroNix) > 0:
        distro = isDistroNix[0].split()
        if distro[2] == '"Ubuntu"' and distro[3] == '"20.04"':
            return [LEVEL_CRITICAL, "Ubuntu 20.04 under Wayland",
                    "Ubuntu 20.04 does not provide the needed dependencies for OBS to capture under Wayland.<br> So OBS is able to capture only under X11/Xorg."]

    windowSystemLine = getWindowSystemLine(lines)
    # If there is no Window System, OBS is running under Wayland
    if not windowSystemLine:
        return

    # If there is, OBS is running under XWayland
    return [LEVEL_CRITICAL, "Running under XWayland",
            "OBS is running under XWayland, which prevents OBS from being able to capture.<br>To fix that, you will need to run OBS with the following command in a terminal:<p><code>obs -platform wayland</code></p>"]
