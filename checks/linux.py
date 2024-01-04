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


def checkDistro(lines):
    isDistroNix = search('Distribution:', lines)

    if len(isDistroNix) <= 0:
        return

    distro = isDistroNix[0].split()
    distro = distro[2:]
    distro = ' '.join(distro)

    return [LEVEL_INFO, distro, ""]


def checkFlatpak(lines):
    isFlatpak = search('Flatpak Runtime:', lines)

    if len(isFlatpak) > 0:
        return [LEVEL_INFO, "Flatpak",
                "You are using the Flatpak. Plugins are available as Flatpak extensions, which you can find in your Distribution's Software Center or via <code>flatpak search com.obsproject.Studio</code>. Installation of external plugins is not supported."]


def checkSnapPackage(lines):
    isDistroNix = search('Distribution:', lines)

    if len(isDistroNix) <= 0:
        return

    distro = isDistroNix[0].split()
    # Snap Package logs "Ubuntu Core" as distro, so it gets split halfway
    if distro[2] == '"Ubuntu' and distro[3] == 'Core"':
        return [LEVEL_WARNING, "Snap Package",
                "You are using the Snap Package. This is a community-supported modified build of OBS Studio; please file issues on the <a href=\"https://github.com/snapcrafters/obs-studio/issues\">Snapcrafters GitHub</a>.<br><br>OBS may be unable to assist with issues arising out of the usage of this package. We recommend following our <a href=\"https://obsproject.com/download#linux\">Install Instructions</a> instead."]


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
                    "Ubuntu 20.04 does not provide the needed dependencies for OBS to capture under Wayland.<br> Capture will only function under X11/Xorg."]

    windowSystemLine = getWindowSystemLine(lines)
    # If there is no Window System, OBS is running under Wayland
    if windowSystemLine:
        # If there is, OBS is running under XWayland
        return [LEVEL_CRITICAL, "Running under XWayland",
                "OBS is running under XWayland, which prevents OBS from being able to capture.<br>To fix that, you will need to run OBS with the following command in a terminal:<p><code>obs -platform wayland</code></p>"]

    hasNoPipewireCapture = search('[pipewire] No capture', lines)
    if len(hasNoPipewireCapture) > 0:
        return [LEVEL_CRITICAL, "No PipeWire capture on Wayland",
                """In order to capture displays or windows under Wayland, OBS requires the appropriate PipeWire capture portal for your Desktop Environment.<br><br>
                An overview of available capture portals can be found on the Arch Linux Wiki:<br>
                <a href='https://wiki.archlinux.org/title/XDG_Desktop_Portal'>XDG Desktop Portal</a><br>
                Note that the availability of Window and/or Display capture depends on your Desktop Environment's implementation of these portals."""]

    return [LEVEL_INFO, "Wayland",
            """Window and Display Captures are available via <a href='https://wiki.archlinux.org/title/XDG_Desktop_Portal'>XDG Desktop Portal</a><br>.
            Please note that the availability of captures and specific features depends on your Desktop Environment's implementation of these portals.<br><br>
            Global Keyboard Shortcuts are not currently available under Wayland."""]


def checkX11Captures(lines):
    isDistroNix = search('Distribution:', lines)
    isFlatpak = search('Flatpak Runtime:', lines)

    if (len(isDistroNix) <= 0) and (len(isFlatpak) <= 0):
        return

    sessionTypeLine = getSessionTypeLine(lines)
    if not sessionTypeLine:
        return

    sessionType = sessionTypeLine.split()[3]
    if sessionType != 'x11':
        return

    # obsolete PW sources
    hasPipewireCaptureDesktop = search('pipewire-desktop-capture-source', lines)
    hasPipewireCaptureWindow = search('pipewire-window-capture-source', lines)
    # unified PW source
    hasPipewireCaptureScreen = search('pipewire-screen-capture-source', lines)

    if (len(hasPipewireCaptureDesktop) > 0) or (len(hasPipewireCaptureWindow) > 0) or (len(hasPipewireCaptureScreen) > 0):
        return [LEVEL_WARNING, "PipeWire capture on X11",
                """Most Desktop Environments do not implement the PipeWire capture portals on X11. This can result in being unable to pick a window or display, or the selected source will stay empty.<br><br>
                We generally recommend using \"Window Capture (Xcomposite)\" on X11, as \"Display Capture (XSHM)\" can introduce bottlenecks depending on your setup."""]

    return [LEVEL_INFO, "X11",
            "If you wish to capture a window or an entire display, captures are available via Xcomposite and XSHM respectively. We generally recommend sticking to \"Window Capture (Xcomposite)\" since \"Display Capture (XSHM)\" can introduce bottlenecks depending on your setup."]
