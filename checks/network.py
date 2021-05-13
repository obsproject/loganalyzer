import re

from .vars import *
from .utils.utils import *


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


def checkKiller(lines):
    if (len(search('Interface: Killer', lines)) > 0):
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


x264stream_re = re.compile(r"stream")


def checkDynamicBitrate(lines):
    dynBrLines = search('Dynamic bitrate enabled', lines)
    if (len(dynBrLines) > 0):
        x264Lines = search('x264 encoder: ', lines)
        for i in x264Lines:
            if x264stream_re.search(i):
                return [LEVEL_INFO, "Dynamic Bitrate", "Dynamic Bitrate is enabled. Instead of dropping frames when network issues are detected, OBS will automatically reduce the stream quality to compensate. The bitrate will adjust back to normal once the connection becomes stable. In some (very specific) situations, Dynamic Bitrate can get stuck at a low bitrate. If this happens frequently, it is recommended to turn off Dynamic Bitrate in Settings -> Advanced -> Network."]
        else:
            return [LEVEL_WARNING, "Dynamic Bitrate",
                    """Dynamic Bitrate is enabled and a hardware encoder is potentially in use. This can cause issues with hardware encoders if bitrate changes happen too frequently, or drops too low. Should you experience bitrate dropping to zero, or no output even if OBS says its streaming, either change your Encoder to x264 or turn off Dynamic Bitrate in Settings -> Advanced -> Network."""]
    return None
