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


def isWayland(lines):
    if not (checkDistro(lines) or checkFlatpak(lines)):
        return False

    sessionTypeLine = getSessionTypeLine(lines)
    if not sessionTypeLine:
        return False

    if 'wayland' not in sessionTypeLine:
        return False

    return True


def isX11(lines):
    if not (checkDistro(lines) or checkFlatpak(lines)):
        return False

    sessionTypeLine = getSessionTypeLine(lines)
    if not sessionTypeLine:
        return False

    if 'x11' not in sessionTypeLine:
        return False

    return True


def checkDistro(lines):
    isDistroNix = search('Distribution:', lines)

    if len(isDistroNix) <= 0:
        return

    distro = isDistroNix[0].split()
    distro = distro[2:]
    distro = ' '.join(distro)
    distroHelp = ''

    # this is logged when the file can't be found at all
    if distro == 'Missing /etc/os-release !':
        distro = '(Missing)'
        distroHelp = 'No distribution detected. This can lead to undefined behavior. Please consult your distribution\'s support channels on how to fix this.<br>'
        return [LEVEL_WARNING, distro, distroHelp]

    return [LEVEL_INFO, distro, distroHelp]


def checkFlatpak(lines):
    isFlatpak = search('Flatpak Runtime:', lines)

    if isFlatpak and ('org.kde.Platform' not in isFlatpak[0]) and ('org.freedesktop.Platform' not in isFlatpak[0]):
        return [LEVEL_WARNING, "Unofficial Flatpak",
                "You are using an unofficial Flatpak package. Please file issues with the packager.<br><br>OBS may be unable to assist with issues arising out of the usage of this package. We recommend following our <a href=\"https://obsproject.com/download#linux\">Install Instructions</a> instead."]

    if isFlatpak:
        return [LEVEL_INFO, "Flatpak",
                "You are using the Flatpak. Plugins are available as Flatpak extensions, which you can find in your Distribution's Software Center or via <code>flatpak search com.obsproject.Studio</code>. Installation of external plugins is not supported."]


def checkSnapPackage(lines):
    isDistroNix = search('Distribution:', lines)

    if len(isDistroNix) <= 0:
        return

    if '"Ubuntu Core"' in isDistroNix[0]:
        return [LEVEL_WARNING, "Snap Package",
                "You are using the Snap Package. This is a community-supported modified build of OBS Studio; please file issues on the <a href=\"https://github.com/snapcrafters/obs-studio/issues\">Snapcrafters GitHub</a>.<br><br>OBS may be unable to assist with issues arising out of the usage of this package. We recommend following our <a href=\"https://obsproject.com/download#linux\">Install Instructions</a> instead."]


def checkWayland(lines):
    if not isWayland(lines):
        return

    isDistroNix = checkDistro(lines)
    if isDistroNix and ('"Ubuntu" "20.04"' in isDistroNix[1]):
        return [LEVEL_CRITICAL, "Ubuntu 20.04 under Wayland",
                "Ubuntu 20.04 does not provide the needed dependencies for OBS to capture under Wayland.<br> Capture will only function under X11/Xorg."]

    windowSystemLine = getWindowSystemLine(lines)
    # If there is no Window System, OBS is running under Wayland
    if windowSystemLine:
        # If there is, OBS is running under XWayland
        return [LEVEL_CRITICAL, "Running under XWayland",
                "OBS is running under XWayland, which prevents OBS from being able to capture.<br>To fix that, you will need to run OBS with the following command in a terminal:<p><code>obs -platform wayland</code></p>"]

    hasPipewirePortal = search('[pipewire]', lines)
    hasNoPipewireCapture = search('[pipewire] No capture', hasPipewirePortal)
    if not hasPipewirePortal or hasNoPipewireCapture:
        return [LEVEL_CRITICAL, "No PipeWire capture on Wayland",
                """In order to capture displays or windows under Wayland, OBS requires the appropriate PipeWire capture portal for your Desktop Environment.<br><br>
                An overview of available capture portals can be found on the Arch Linux Wiki:<br>
                <a href='https://wiki.archlinux.org/title/XDG_Desktop_Portal'>XDG Desktop Portal</a><br>
                Note that the availability of Window and/or Display capture depends on your Desktop Environment's implementation of these portals."""]


def checkX11Captures(lines):
    if not isX11(lines):
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


def checkDesktopEnvironment(lines):
    isDistroNix = search('Distribution:', lines)
    isFlatpak = search('Flatpak Runtime:', lines)

    if (len(isDistroNix) <= 0) and (len(isFlatpak) <= 0):
        return

    desktopEnvironmentLine = search('Desktop Environment:', lines)

    if not desktopEnvironmentLine:
        return

    desktopEnvironment = desktopEnvironmentLine[0].split()

    if (len(desktopEnvironment) > 3):
        desktopEnvironment = desktopEnvironment[3:]
        desktopEnvironment = ' '.join(desktopEnvironment)
    else:
        desktopEnvironment = ''

    if (len(desktopEnvironment) > 0):
        return [LEVEL_INFO, desktopEnvironment, '']


def checkMissingModules(lines):
    isDistroNix = search('Distribution:', lines)

    if (len(isDistroNix) <= 0):
        return

    modulesMissingList = []
    modulesCheckList = ('obs-browser.so', 'obs-websocket.so', 'vlc-video.so')

    for module in modulesCheckList:
        if not search(module, lines):
            modulesMissingList.append(module)

    if len(modulesMissingList):
        modulesMissingString = str(modulesMissingList)
        modulesMissingString = modulesMissingString.replace("['", "<ul><li>")
        modulesMissingString = modulesMissingString.replace("', '", "</li><li>")
        modulesMissingString = modulesMissingString.replace("']", "</li></ul>")

        return [LEVEL_INFO, "Missing Modules (" + str(len(modulesMissingList)) + ")",
                """You are missing the following default modules:<br>""" + modulesMissingString]


def checkLinuxVCam(lines):
    isDistroNix = search('Distribution:', lines)
    isFlatpak = search('Flatpak Runtime:', lines)

    if (len(isDistroNix) <= 0) and (len(isFlatpak) <= 0):
        return

    hasV4L2Module = search('v4l2loopback not installed', lines)

    if len(hasV4L2Module) > 0:
        return [LEVEL_INFO, "Virtual Camera not available",
                """Using the Virtual Camera requires the <code>v4l2loopback</code> kernel module to be installed.<br>
                If required, please refer to our <a href="https://github.com/obsproject/obs-studio/wiki/install-instructions#prerequisites-for-all-versions">Install Instructions</a> on how to install this on your distribution."""]


def checkLinuxSystemInfo(lines):
    if flatpak := checkFlatpak(lines):
        logLevel = flatpak[0]
        linuxDistroOrFlatpak = flatpak[1]
        linuxSystemInfoHelp = flatpak[2] + '<br>'
    elif distro := checkDistro(lines):
        logLevel = distro[0]
        linuxDistroOrFlatpak = 'Distribution: ' + distro[1]
        linuxSystemInfoHelp = distro[2]
    else:
        return

    if isX11(lines):
        displayServer = 'X11'
    elif isWayland(lines):
        displayServer = 'Wayland'
    else:
        # can happen with misconfigured or virtual systems
        logLevel = LEVEL_WARNING
        displayServer = 'None'
        linuxSystemInfoHelp += 'No Display Server detected. This can lead to undefined behavior. Please consult your Desktop Environment\'s or Window Manager\'s support channels on how to fix this.<br>'

    if checkDesktopEnvironment(lines):
        desktopEnvironment = 'DE: ' + checkDesktopEnvironment(lines)[1]
    else:
        # can happen for some misconfigured tiling window managers
        logLevel = LEVEL_WARNING
        desktopEnvironment = 'DE: None'
        linuxSystemInfoHelp += 'No Desktop Environment detected. This can lead to undefined behavior. Please consult your Desktop Environment\'s or Window Manager\'s support channels on how to fix this.'

    return [logLevel, linuxDistroOrFlatpak + ' | ' + displayServer + ' | ' + desktopEnvironment, linuxSystemInfoHelp]
