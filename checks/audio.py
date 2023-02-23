import re

from .vars import *
from .utils.utils import *


audiobuf_re = re.compile(r"""
    (?i)
    adding \s (?P<added> \d+) \s milliseconds \s of \s audio \s buffering
    , \s
    total \s audio \s buffering \s is \s now \s (?P<total> \d+) \s milliseconds
    (
        \s
        \( source: (?P<source> .*) \)
    )?
    $
    """, re.VERBOSE)


def checkMonitoringDevice(lines):
    if search('audio_monitor_init_wasapi: Failed', lines):
        return [LEVEL_CRITICAL, "Audio Monitoring Device Failure",
                "Your audio monitoring device failed to load. To correct this:<br><br>1) Go to Settings > Audio and set your monitoring device to something other than what it is now. Press Apply.<br>2) Restart OBS.<br>3) Go to Settings > Audio and set your monitoring device to the correct one. Press Apply."]


def checkAudioBuffering(lines):
    maxBuffering = searchWithIndex('Max audio buffering reached!', lines)
    if (len(maxBuffering) > 0):
        # This doesn't correspond to a specific amount of time -- it's
        # emitted if the delay is greater than MAX_BUFFERING_TICKS, and that
        # amount of time varies by sample rate. Unfortunately, the max
        # buffering reached message doesn't directly say which audio source
        # was the offender. Is it worth just ditching this check and using
        # the "greater than 500ms" check, which could potentially also easily
        # know the specific device?
        append = ""
        for line, index in maxBuffering:
            if (len(lines) > index):
                m = audiobuf_re.search(lines[index + 1].replace('\r', ''))
                if m.group("source"):
                    append += "<br><br>Source affected (potential cause):<strong>" + m.group("source") + "</strong>"
                    break
        return [LEVEL_CRITICAL, "Max Audio Buffering",
                "Audio buffering hit the maximum value. This is an indicator of very high system load, will affect stream latency, and may even cause individual audio sources to stop working. Keep an eye on CPU usage especially, and close background programs if needed. <br><br>Occasionally, this can be caused by incorrect device timestamps. Restart OBS to reset buffering." + append]

    buffering = search('total audio buffering is now', lines)
    vals = [0, ]
    if (len(buffering) > 0):
        for i in buffering:
            m = audiobuf_re.search(i)
            if m:
                vals.append(int(m.group("total")))

        if (max(vals) > 500):
            return [LEVEL_WARNING, "High Audio Buffering",
                    "Audio buffering reached values above 500ms. This is an indicator of very high system load and will affect stream latency. Keep an eye on CPU usage especially, and close background programs if needed. Restart OBS to reset buffering."]

    return None
