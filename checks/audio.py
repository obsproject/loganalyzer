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