from .vars import *
from .utils.utils import *


def checkElements(lines):
    if (len(search('obs-streamelements', lines)) > 0):
        return [LEVEL_WARNING, "StreamElements OBS.Live",
                """The obs.live plugin is installed. This overwrites OBS' default browser source and causes a severe performance impact. To get rid of it, first, export your scene collections and profiles, second manually uninstall OBS completely, third reinstall OBS Studio only with the latest installer from <a href="https://obsproject.com/download">https://obsproject.com/download</a>"""]
