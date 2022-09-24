from .vars import *
from .utils.utils import *
import re

import_re = re.compile(r"""
    (?i)
    \/
    (?P<plugin>[^\/]+)
    '\sdue\sto\spossible\simport\sconflicts
    """, re.VERBOSE)

def checkImports(lines):
    conflicts = search('due to possible import conflicts', lines)
    if (len(conflicts) > 0):
        append = ""
        for p in conflicts:
            c = import_re.search(p)
            if c and c.group("plugin"):
                append += "<li>" + c.group("plugin").replace('.dll', '') + "</li>"

        if append:
            append = "<br><br>Plugins affected:<ul>" + append + "</ul>"
        return [LEVEL_CRITICAL, "Outdated Plugins (" + str(len(conflicts)) + ")",
        """Some plugins need to be manually updated, as they do not work with this version of OBS. Check our <a href="https://obsproject.com/kb/obs-studio-28-plugin-compatibility">Plugin Compatibility Guide</a> for known updates & download links.""" + append]
