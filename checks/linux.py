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
                "You are using the Flatpak. Plugins are available as Flatpak extensions, which you can find in your Distributions Software Center or via <code>flatpak search com.obsproject.Studio</code>. Installation of external plugins is not supported."]


def checkSnapPackage(lines):
    isDistroNix = search('Distribution:', lines)

    if len(isDistroNix) <= 0:
        return

    distro = isDistroNix[0].split()
    # Snap Package logs "Ubuntu Core" as distro, so it gets split halfway
    if distro[2] == '"Ubuntu' and distro[3] == 'Core"':
        return [LEVEL_WARNING, "Snap Package",
                "You are using the Snap Package. This is a community-supported modified build of OBS Studio; please file issues on the <a href=\"https://github.com/snapcrafters/obs-studio/issues\">Snapcrafters GitHub</a>.<br><br>OBS may be unable to assist with issues arising out of the usage of this package and therefore recommends following our <a href=\"https://obsproject.com/download#linux\">Install Instructions</a>."]


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


def checkX11(lines):
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
                """While technically possible, most Desktop Environments do not implement the PipeWire capture portals on X11. Your captures will therefore likely not work, i.e. you will be unable to pick a window or display, or the selected source will stay empty.<br><br>
                We generally recommend using \"Window Capture (Xcomposite)\" on X11, as \"Display Capture (XSHM)\" can introduce bottlenecks depending on your setup.<br><br>
                From a technical standpoint a Desktop Environment should not advertise the availability of these captures if they are not implemented. This behaviour can therefore be considered a bug in your Desktop Environment."""]

    return [LEVEL_INFO, "X11",
            "Window Capture is available via Xcomposite, while Display Capture is available via XSHM. We generally recommend sticking to \"Window Capture (Xcomposite)\" since \"Display Capture (XSHM)\" can introduce bottlenecks depending on your setup."]


def checkDesktopEnvironment(lines):
    isDistroNix = search('Distribution:', lines)
    isFlatpak = search('Flatpak Runtime:', lines)

    if (len(isDistroNix) <= 0) and (len(isFlatpak) <= 0):
        return

    desktopEnvironmentLine = search('Desktop Environment:', lines)
    desktopEnvironment = desktopEnvironmentLine[0].split()
    desktopEnvironment = desktopEnvironment[3:]
    desktopEnvironment = ' '.join(desktopEnvironment)

    if (len(desktopEnvironment) > 0):
        return [LEVEL_INFO, desktopEnvironment, '']


def checkMissingModules(lines):
    isDistroNix = search('Distribution:', lines)

    if (len(isDistroNix) <= 0):
        return

    modulesMissingList = []
    modulesCheckList = ('obs-browser.so', 'obs-vlc.so', 'obs-websocket.so')

    for module in modulesCheckList:
        if not search(module, lines):
            modulesMissingList.append(module)

    if len(modulesMissingList):
        modulesMissingString = str(modulesMissingList)
        modulesMissingString = modulesMissingString.replace("', '", "</li><li>")
        modulesMissingString = modulesMissingString[2:]
        modulesMissingString = modulesMissingString[:-2]

        return [LEVEL_INFO, "Missing Modules (" + str(len(modulesMissingList)) + ")",
                """You are missing the following default modules:<br><ul><li>""" + modulesMissingString + "</li></ul>"]


def checkLinuxVCam(lines):
    isDistroNix = search('Distribution:', lines)

    if (len(isDistroNix) <= 0):
        return

    hasV4L2Module = search('v4l2loopback not installed', lines)

    if len(hasV4L2Module) > 0:
        return [LEVEL_INFO, "VCam not available",
                """Using the Virtual Camera requires the <code>v4l2loopback</code> kernel module to be installed.<br>
                If required, please refer to our <a href="https://github.com/obsproject/obs-studio/wiki/install-instructions#prerequisites-for-all-versions">Install Instructions</a> on how to install this on your distribution.<br>
                If the module was not already loaded OBS will normally ask you for permission to load it when required. This requires a working <code>polkit</code> setup.<br>
                You can also load the module manually using <code>modprobe v4l2loopback exclusive_caps=1 card_label='OBS Virtual Camera'</code>."""]
