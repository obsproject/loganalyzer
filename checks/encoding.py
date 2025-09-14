from .vars import *
from .utils.utils import *
import re


params_re = re.compile(r"\t(?P<key>\w+):\s*(?P<value>\S+)")


def checkAttempt(lines):
    recordingStarts = search('== Recording Start ==', lines)
    streamingStarts = search('== Streaming Start ==', lines)
    replaybufferStarts = search('== Replay Buffer Start ==', lines)
    if (len(recordingStarts) + len(streamingStarts) + len(replaybufferStarts) == 0):
        return [LEVEL_INFO, "No Output Session",
                "Your log contains no recording or streaming session. Results of this log analysis are limited. Please post a link to a clean log file. " + cleanLog]


def checkMP4(lines):
    writtenFiles = search('Writing file ', lines)
    mp4 = search('.mp4', writtenFiles)
    mov = search('.mov', writtenFiles)
    fragmentedFlag = search('movflags=frag_keyframe+empty_moov+delay_moov', lines)
    if (mp4 or mov) and not fragmentedFlag:
        return [LEVEL_CRITICAL, "MP4/MOV Recording",
                "Record to FLV or MKV. If you record to MP4 or MOV and the recording is interrupted, the file will be corrupted and unrecoverable. <br><br>If you require MP4 files for some other purpose like editing, remux them afterwards by selecting File > Remux Recordings in the main OBS Studio window."]


def checkPreset(lines):
    encoderLines = search('x264 encoder:', lines)
    presets = search('preset: ', lines)
    sensiblePreset = True
    for ln in presets:
        if (not (('veryfast' in ln) or ('superfast' in ln) or ('ultrafast' in ln))):
            sensiblePreset = False

    if ((len(encoderLines) > 0) and (not sensiblePreset)):
        return [LEVEL_INFO, "Non-Default x264 Preset",
                "A slower x264 preset than 'veryfast' is in use. It is recommended to leave this value on veryfast, as there are significant diminishing returns to setting it lower. It can also result in very poor gaming performance on the system if you're not using a 2 PC setup."]


def checkCustom(lines):
    encoderLines = search("'adv_ffmpeg_output':", lines)
    if (len(encoderLines) > 0):
        return [LEVEL_WARNING, "Custom FFMPEG Output",
                """Custom FFMPEG output is in use. Only absolute professionals should use this. If you got your settings from a YouTube video advertising "Absolute best OBS settings" then we recommend using one of the presets in Simple output mode instead."""]


def checkStreamSettings(lines):
    streamingSessions = searchWithIndex("stream'] settings:", lines)
    if streamingSessions:
        encode_params = {"bitrate": None,
                         "height": None,
                         "width": None,
                         "fps_num": None,
                         "fps_den": None,
                         }
        line = streamingSessions[-1][1]
        match = params_re.search(lines[line + 1])
        while match:
            for key in encode_params:
                if key in match.group("key"):
                    try:
                        encode_params[key] = float(match.group("value"))
                    except (ValueError, OverflowError):
                        pass
            line += 1
            try:
                match = params_re.search(lines[line])
            except IndexError:
                match = False

        # If bitrate isn't listed in the encode parameters or isn't a number, don't perform the check
        if encode_params["bitrate"] is None:
            return

        # If fps or resolution aren't listed in encode parameters or aren't a number, fetch them from the video settings
        line = searchWithIndex("video settings reset:", lines[:line])[-1][1]
        try:
            if encode_params["height"] is None or encode_params["width"] is None:
                encode_params["width"], encode_params["height"] = (int(_) for _ in (lines[line + 2].split()[-1]).split("x"))
            if encode_params["fps_den"] is None or encode_params["fps_num"] is None:
                encode_params["fps_num"], encode_params["fps_den"] = (int(_) for _ in (lines[line + 4].split()[-1]).split("/"))
        except (ValueError, OverflowError):
            return                             # If fetching them from the video settings fails, don't perform the check

        bitrateEstimate = (encode_params["width"] * encode_params["height"] * encode_params["fps_num"] / encode_params["fps_den"]) / 20000
        if (encode_params["bitrate"] < bitrateEstimate):
            return [LEVEL_INFO, "Low Stream Bitrate",
                    "Your stream encoder is set to a video bitrate that is too low. This will lower picture quality especially in high motion scenes like fast paced games. Use the Auto-Config Wizard to adjust your settings to the optimum for your situation. It can be accessed from the Tools menu in OBS, and then just follow the on-screen directions."]


def checkNVENC(lines):
    msgs = search("Failed to open NVENC codec", lines)
    if (len(msgs) > 0):
        # TODO Check whether the user is on Windows before suggesting Windows-specific solutions
        return [LEVEL_WARNING, "NVENC Start Failure",
                """The NVENC Encoder failed to start due of a variety of possible reasons. Make sure that Windows Game Bar and Windows Game DVR are disabled and that your GPU drivers are up to date. <br><br>You can perform a clean driver installation for your GPU by following the instructions at <a href="http://obsproject.com/forum/resources/performing-a-clean-gpu-driver-installation.65/"> Clean GPU driver installation</a>. <br>If this doesn't solve the issue, then it's possible your graphics card doesn't support NVENC. You can change to a different Encoder in Settings > Output."""]


def checkEncodeError(lines):
    if (len(search('Error encoding with encoder', lines)) > 0):
        return [LEVEL_INFO, "Encoder start error",
                """An encoder failed to start. This could result in a bitrate stuck at 0 or OBS stuck on "Stopping Recording". Depending on your encoder, try updating your drivers. If you're using QSV, make sure your iGPU is enabled. If that still doesn't help, try switching to a different encoder in Settings -> Output."""]


def checkEncoding(lines):
    hasSoftware = search('[x264 encoder:', lines) or search('[AV1 encoder:', lines)
    hasHardware = (search('[obs-nvenc:', lines)
                   or search('[texture-amf-', lines)
                   or search('[qsv encoder:', lines)
                   or searchExclude('[VideoToolbox ', lines, ["[VideoToolbox encoder]: "]))
    drops = search('skipped frames', lines)
    val = 0
    severity = 9000
    for drop in drops:
        try:
            v = float(drop[drop.find("(") + 1: drop.find(")")
                           ].strip('%').replace(",", "."))
        except (ValueError, OverflowError):
            v = 0
        if (v > val):
            val = v
    if (val != 0):
        if (val >= 15):
            severity = LEVEL_CRITICAL
        elif (15 > val and val >= 5):
            severity = LEVEL_WARNING
        else:
            severity = LEVEL_INFO
        if (hasSoftware and hasHardware):
            return [severity, "{}% Encoder Overload".format(val),
                    """Encoder overload may be related to your CPU or GPU being overloaded, depending on the encoder in question. If you are using a software encoder (x264) please see the <a href="https://obsproject.com/kb/encoding-performance-troubleshooting">CPU Overload Guide</a>. If you are using a hardware encoder (AMF, QSV/Quicksync, NVENC) please see the <a href="https://obsproject.com/kb/encoding-performance-troubleshooting">GPU Overload Guide</a>."""]
        elif hasSoftware:
            return [severity, "{}% CPU Encoder Overload".format(val),
                    """The encoder is skipping frames because of CPU overload. Read about <a href="https://obsproject.com/kb/encoding-performance-troubleshooting">General Performance and Encoding Issues</a>."""]
        elif hasHardware:
            return [severity, "{}% GPU Encoder Overload".format(val),
                    """The encoder is skipping frames because of GPU overload. Read about troubleshooting tips in our <a href="https://obsproject.com/kb/encoding-performance-troubleshooting">GPU Overload Guide</a>."""]
        else:
            return [severity, "{}% Encoder Overload".format(val),
                    """Encoder overload may be related to your CPU or GPU being overloaded, depending on the encoder in question. If you are using a software encoder (x264) please see the <a href="https://obsproject.com/kb/encoding-performance-troubleshooting">CPU Overload Guide</a>. If you are using a hardware encoder (AMF, QSV/Quicksync, NVENC) please see the <a href="https://obsproject.com/kb/encoding-performance-troubleshooting">GPU Overload Guide</a>."""]


unknownenc_re = re.compile(r"Encoder\sID\s'(?P<name>.+)'\snot\sfound")


def checkUnknownEncoder(lines):
    encLines = search('Encoder ID', lines)
    outdatedEncMac = ['vt_h264_sw', 'vt_h264_hw']
    if (len(encLines) > 0):
        for i in encLines:
            m = unknownenc_re.search(i)
            if m:
                encName = m.group("name")
                if encName in outdatedEncMac:
                    return [LEVEL_CRITICAL, "Outdated Encoder Set",
                            "In OBS v27, the Apple VT encoder was changed to better support the Apple M1 platform, which resulted in the existing encoder becoming unrecognised. Manually navigate to Settings -> Output and set the 'Encoder' to fix this."]
                return [LEVEL_WARNING, "Unrecognised Encoder",
                        "One of the configured encoders is not recognised. This can result in failure to go live or to record. To fix this, go to Settings -> Output and change the 'Encoder' option."]
