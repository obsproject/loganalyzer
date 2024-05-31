#!/usr/bin/env python3

import argparse
import textwrap

from checks.vars import *
from checks.core import *
from checks.audio import *
from checks.encoding import *
from checks.graphics import *
from checks.macos import *
from checks.network import *
from checks.plugins import *
from checks.sources import *
from checks.linux import *
from checks.windows import *

from checks.utils.fetchers import *
from checks.utils.utils import *
from checks.utils.windowsversions import *


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
        gist = matchGist(url)
        haste = matchHaste(url)
        obs = matchObs(url)
        pastebin = matchPastebin(url)
        discord = matchDiscord(url)
        if (gist):
            gistObject = getGist(gist.groups()[-1])
            logLines = getLinesGist(gistObject)
            messages.append(getDescriptionGist(gistObject))
            success = True
        elif (haste):
            hasteObject = getHaste(haste.groups()[-1])
            logLines = getLinesHaste(hasteObject)
            messages.append(getDescription(logLines))
            success = True
        elif (obs):
            obslogObject = getObslog(obs.groups()[-1])
            logLines = getLinesObslog(obslogObject)
            messages.append(getDescription(logLines))
            success = True
        elif (pastebin):
            pasteObject = getRawPaste(pastebin.groups()[-1])
            logLines = getLinesPaste(pasteObject)
            messages.append(getDescription(logLines))
            success = True
        elif (discord):
            attachment = discord.groups()[-1]
            if attachment == "message":
                attachment = discord.groups()[-2]
            pasteObject = getRawDiscord(attachment)
            if len(pasteObject) > 0:
                logLines = getLinesDiscord(pasteObject)
                messages.append(getDescription(logLines))
                success = True

    elif filename is not None:
        logLines = getLinesLocal(filename)
        messages.append(getDescription(logLines))
        success = True

    if (success):
        classic, m = checkClassic(logLines)
        crash, m = checkCrash(logLines)
        messages.append(m)
        if (not classic and not crash):
            messages.extend([
                checkObsVersion(logLines),
                checkDual(logLines),
                checkAutoconfig(logLines),
                checkCPU(logLines),
                checkAMDdrivers(logLines),
                checkNVIDIAdrivers(logLines),
                checkGPU(logLines),
                checkRefreshes(logLines),
                checkInit(logLines),
                checkWayland(logLines),
                checkNVIDIAdriversEGL(logLines),
                checkNVENC(logLines),
                check940(logLines),
                checkKiller(logLines),
                checkWifi(logLines),
                checkBind(logLines),
                checkWindowsVer(logLines),
                checkWindowsARM64(logLines),
                checkMacVer(logLines),
                checkAdmin(logLines),
                checkImports(logLines),
                check32bitOn64bit(logLines),
                checkWindowsARM64EmulationStatus(logLines),
                checkRosettaTranslationStatus(logLines),
                checkAttempt(logLines),
                checkMP4(logLines),
                checkPreset(logLines),
                checkCustom(logLines),
                checkBrowserAccel(logLines),
                checkAudioBuffering(logLines),
                checkDrop(logLines),
                checkRenderLag(logLines),
                checkEncodeError(logLines),
                checkEncoding(logLines),
                checkMulti(logLines),
                checkStreamSettingsX264(logLines),
                checkStreamSettingsNVENC(logLines),
                checkMicrosoftSoftwareGPU(logLines),
                checkWasapiSamples(logLines),
                checkOpenGLonWindows(logLines),
                checkGameDVR(logLines),
                checkGameMode(logLines),
                checkWin10Hags(logLines),
                checkNICSpeed(logLines),
                checkDynamicBitrate(logLines),
                checkNetworkOptimizations(logLines),
                checkTCPPacing(logLines),
                checkStreamDelay(logLines),
                checkUnknownEncoder(logLines),
                checkBrowserSource(logLines),
                checkMonitoringDevice(logLines),
                checkPluginList(logLines),
                checkVantage(logLines),
                checkPortableMode(logLines),
                checkSafeMode(logLines),
                checkDistro(logLines),
                checkFlatpak(logLines),
                checkSnapPackage(logLines),
                checkX11Captures(logLines),
                checkDesktopEnvironment(logLines),
                checkMissingModules(logLines),
                checkMacPermissions(logLines)
            ])
            messages.extend(checkVideoSettings(logLines))
            m = parseScenes(logLines)
            # TODO Verify .extend() can be used for parseScenes
            seenMessages = set()
            for sublist in m:
                if sublist is not None:
                    for item in sublist:
                        itemTuple = tuple(item)
                        if itemTuple not in seenMessages:
                            messages.append(item)
                            seenMessages.add(itemTuple)
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
