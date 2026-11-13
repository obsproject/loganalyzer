import html
import re

from .vars import *
from .utils.utils import *


def checkCPUInfo(lines):
    for label in ('CPU Name:', 'Processor:'):
        cpuLines = search(label, lines)
        for line in cpuLines:
            name = line.split(label, 1)[1].strip()
            if not name or (label == 'Processor:' and name.endswith(' logical cores')):
                continue

            name = html.escape(name)
            return [LEVEL_SYSTEM, "CPU: " + name,
                    "CPU reported by OBS: " + name + "."]


def checkGPUInfo(lines):
    gpuLines = search('Loading up ', lines)
    for line in reversed(gpuLines):
        if 'Loading up D3D11 on adapter' not in line and 'Loading up OpenGL on adapter' not in line:
            continue

        name = line.split(' on adapter', 1)[1].strip()
        if 'Loading up D3D11' in line:
            name = re.sub(r'(^|\s+)\(\d+\)$', '', name).strip()
        if not name:
            continue

        name = html.escape(name)
        return [LEVEL_SYSTEM, "GPU: " + name,
                "Adapter selected for OBS rendering: " + name + "."]


def checkRAMInfo(lines):
    memoryLines = search('Physical Memory:', lines)
    for line in memoryLines:
        match = re.search(r'Physical Memory:\s*([0-9]+)\s*MB\s+Total\b', line)
        if match:
            total = match.group(1)
            return [LEVEL_SYSTEM, "RAM: " + total + " MB",
                    "Total physical memory reported by OBS: " + total + " MB."]
