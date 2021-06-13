from .vars import *
from .utils.utils import *


def checkElements(lines):
    if (len(search('obs-streamelements', lines)) > 0):
        return [LEVEL_INFO, "StreamElements OBS.Live",
                """StreamElements' OBS.live plugin is installed. This interferes with OBS' browser source and can cause performance impacts. If you want to remove it, follow their <a href="https://streamelements.elevio.help/en/articles/4-how-do-i-uninstall-the-obs-live-plugin">uninstall instructions</a> (make sure that "User Settings" is <b>not</b> selected), then reinstall OBS Studio using only the latest installer from <a href="https://obsproject.com/download">https://obsproject.com/download</a>."""]
