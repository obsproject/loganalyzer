import html
from pkg_resources import parse_version

from .vars import *
from .utils.utils import *
from .core import *
from .graphics import *
from .utils.windowsversions import *


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
        if (len(adapters) == 2 and ('Intel' in d3dAdapter[0]) and ('Arc' not in d3dAdapter[0])):
            return [LEVEL_CRITICAL, "Wrong GPU",
                    """Your Laptop has two GPUs. OBS is running on the weak integrated Intel GPU. For better performance as well as game capture being available you should run OBS on the dedicated GPU. Check the <a href="https://obsproject.com/wiki/Laptop-Troubleshooting">Laptop Troubleshooting Guide</a>."""]
        if (len(adapters) == 2 and ('Vega' in d3dAdapter[0])):
            return [LEVEL_CRITICAL, "Wrong GPU",
                    """Your Laptop has two GPUs. OBS is running on the weak integrated AMD Vega GPU. For better performance as well as game capture being available you should run OBS on the dedicated GPU. Check the <a href="https://obsproject.com/wiki/Laptop-Troubleshooting">Laptop Troubleshooting Guide</a>."""]
        elif (len(adapters) == 1 and ('Intel' in adapters[0]) and ('Arc' not in adapters[0])):
            return [LEVEL_WARNING, "Integrated GPU",
                    "OBS is running on an Intel iGPU. This hardware is generally not powerful enough to be used for both gaming and running obs. Situations where only sources from e.g. cameras and capture cards are used might work."]


refresh_re = re.compile(r"""
    (?i)
    output \s+ (?P<output_num>[0-9]+):
    .*
    refresh = (?P<refresh> [0-9.]+),
    .*
    name = (?P<name> .*)
    """, re.VERBOSE)


def getMonitorRefreshes(lines):
    refreshes = {}

    refreshLines = search('refresh=', lines)

    for rl in refreshLines:
        m = refresh_re.search(rl)

        if m is not None:
            if m.group("name") is not None:
                output = m.group("name").strip() + " (" + str(int(m.group("output_num")) + 1) + ")"
            else:
                output = "Display " + m.group("output_num")
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

    # FINALLY fixed in Win10/2004
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
        rfrshs = "<br>"
        for output, hz in refreshes.items():
            rfrshs += "<br>" + output + ": <strong>" + str(int(hz)) + "</strong>Hz"
        return [LEVEL_WARNING, "Mismatched Refresh Rates",
                "The version of Windows you are running has a limitation which causes performance issues in hardware accelerated applications (such as games) if multiple monitors with different refresh rates are present. Your system's monitors have " + str(len(r)) + """ different refresh rates, so you are affected by this limitation. <br><br>To fix this issue, we recommend updating to the Windows 10 May 2020 Update. Follow <a href="https://blogs.windows.com/windowsexperience/2020/05/27/how-to-get-the-windows-10-may-2020-update/">these instructions</a> if you're not sure how to update.""" + rfrshs]
    return


samples_re = re.compile(r"""
    (?i)
    samples \sper \ssec:
    \s*
    (?P<samples>\d+)
""", re.VERBOSE)


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


def check940(lines):
    gpu = search('NVIDIA GeForce 940', lines)
    attempt = search('NVENC encoder', lines)
    if (len(gpu) > 0) and (len(attempt) > 0):
        return [LEVEL_CRITICAL, "NVENC Not Supported",
                """The NVENC Encoder is not supported on the NVIDIA 940 and 940MX. Recording fails to start because of this. Please select "Software (x264)" or "Hardware (QSV)" as encoder instead in Settings > Output."""]


# Log line examples:
# win 7: 19:39:17.395: Windows Version: 6.1 Build 7601 (revision: 24535; 64-bit)
# win 10: 15:30:58.866: Windows Version: 10.0 Build 19041 (release: 2004; revision: 450; 64-bit)
def getWindowsVersionLine(lines):
    versionLines = search('Windows Version:', lines)
    if len(versionLines) > 0:
        return versionLines[0]


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
    if verinfo["version"] == "10.0" and verinfo["release"] == 0:
        if verinfo["build"] > 22000:
            msg = "You are running Windows 11 Insider build %d. Some checks that are applicable only to specific Windows versions will not be performed. Also, because Insider builds are test versions, you may have problems that would not happen with release versions of Windows 11." % (
                verinfo["build"])
            return [LEVEL_WARNING, "Windows 11 Insider Build", msg]
        else:
            msg = "You are running an unknown Windows 10 release (build %d), which means you are probably using an Insider build. Some checks that are applicable only to specific Windows versions will not be performed. Also, because Insider builds are test versions, you may have problems that would not happen with release versions of Windows." % (
                verinfo["build"])
            return [LEVEL_WARNING, "Windows 10 Version Unknown", msg]

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
    if (len(winVersion) > 0 and '64-bit' in winVersion[0] and '64-bit' not in obsVersion and '64bit' not in obsVersion):
        # thx to secretply for the bugfix
        return [LEVEL_WARNING, "32-bit OBS on 64-bit Windows",
                "You are running the 32 bit version of OBS on a 64 bit system. This will reduce performance and greatly increase the risk of crashes due to memory limitations. You should only use the 32 bit version if you have a capture device that lacks 64 bit drivers. Please run OBS using the 64-bit shortcut."]
