from .vars import *
from .utils.utils import *


def checkAttempt(lines):
    recordingStarts = search('== Recording Start ==', lines)
    streamingStarts = search('== Streaming Start ==', lines)
    if (len(recordingStarts) + len(streamingStarts) == 0):
        return [LEVEL_INFO, "No Output Session",
                "Your log contains no recording or streaming session. Results of this log analysis are limited. Please post a link to a clean log file. " + cleanLog]


def checkMP4(lines):
    writtenFiles = search('Writing file ', lines)
    mp4 = search('.mp4', writtenFiles)
    mov = search('.mov', writtenFiles)
    if (len(mp4) > 0 or len(mov) > 0):
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


def checkStreamSettingsX264(lines):
    streamingSessions = []
    for i, s in enumerate(lines):
        if "[x264 encoder: 'simple_h264_stream'] settings:" in s:
            streamingSessions.append(i)

    if (len(streamingSessions) > 0):
        bitrate = float(lines[streamingSessions[-1] + 2].split()[-1])
        fps_num = float(lines[streamingSessions[-1] + 5].split()[-1])
        fps_den = float(lines[streamingSessions[-1] + 6].split()[-1])
        width = float(lines[streamingSessions[-1] + 7].split()[-1])
        height = float(lines[streamingSessions[-1] + 8].split()[-1])

        bitrateEstimate = (width * height * fps_num / fps_den) / 20000
        if (bitrate < bitrateEstimate):
            return [LEVEL_INFO, "Low Stream Bitrate",
                    "Your stream encoder is set to a video bitrate that is too low. This will lower picture quality especially in high motion scenes like fast paced games. Use the Auto-Config Wizard to adjust your settings to the optimum for your situation. It can be accessed from the Tools menu in OBS, and then just follow the on-screen directions."]


def checkNVENC(lines):
    msgs = search("Failed to open NVENC codec", lines)
    if (len(msgs) > 0):
        # TODO Check whether the user is on Windows before suggesting Windows-specific solutions
        return [LEVEL_WARNING, "NVENC Start Failure",
                """The NVENC Encoder failed to start due of a variety of possible reasons. Make sure that Windows Game Bar and Windows Game DVR are disabled and that your GPU drivers are up to date. <br><br>You can perform a clean driver installation for your GPU by following the instructions at <a href="http://obsproject.com/forum/resources/performing-a-clean-gpu-driver-installation.65/"> Clean GPU driver installation</a>. <br>If this doesn't solve the issue, then it's possible your graphics card doesn't support NVENC. You can change to a different Encoder in Settings > Output."""]


def checkStreamSettingsNVENC(lines):
    streamingSessions = []
    for i, s in enumerate(lines):
        if "[NVENC encoder: 'streaming_h264'] settings:" in s:
            streamingSessions.append(i)
    if (len(streamingSessions) > 0):
        bitrate = 0
        fps_num = 0
        width = 0
        height = 0
        for i in range(12):
            chunks = lines[streamingSessions[-1] + i].split()
            if (chunks[-2] == 'bitrate:'):
                bitrate = float(chunks[-1])
            elif (chunks[-2] == 'keyint:'):
                fps_num = float(chunks[-1])
            elif (chunks[-2] == 'width:'):
                width = float(chunks[-1])
            elif (chunks[-2] == 'height:'):
                height = float(chunks[-1])
        bitrateEstimate = (width * height * fps_num) / 20000
        if (bitrate < bitrateEstimate):
            return [LEVEL_INFO, "Low Stream Bitrate",
                    "Your stream encoder is set to a video bitrate that is too low. This will lower picture quality especially in high motion scenes like fast paced games. Use the Auto-Config Wizard to adjust your settings to the optimum for your situation. It can be accessed from the Tools menu in OBS, and then just follow the on-screen directions."]


def checkEncodeError(lines):
    if (len(search('Error encoding with encoder', lines)) > 0):
        return [LEVEL_INFO, "Encoder start error",
                """An encoder failed to start. This could result in a bitrate stuck at 0 or OBS stuck on "Stopping Recording". Depending on your encoder, try updating your drivers. If you're using QSV, make sure your iGPU is enabled. If that still doesn't help, try switching to a different encoder in Settings -> Output."""]


def checkEncoding(lines):
    drops = search('skipped frames', lines)
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
        return [severity, "{}% Encoder Overload".format(val),
                """The encoder is skipping frames because of CPU overload. Read about <a href="https://obsproject.com/wiki/General-Performance-and-Encoding-Issues">General Performance and Encoding Issues</a>."""]
