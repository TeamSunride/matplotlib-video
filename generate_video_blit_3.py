# Tom Danvers, 2025

import time as time_library

video_file = "inputs/input.mp4"
data_file = "inputs/20250625-005-release.h5"
data_time_at_video_start = -3.46

channel_names_to_plot = ['TCX101', 'TCX102', 'TCX103', 'TCX104', 'TCX105', 'TCX106', 'TCX107', 'TCX108', 'TCX109', 'TCX110', 'TCX111']

# STEP 1 - LOAD VIDEO DETAILS
import ffmpeg

probe = ffmpeg.probe(video_file)
video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']

if not video_streams:
    raise ValueError("No video stream found")

video_stream = video_streams[0]

video_duration = float(video_stream.get("duration"))
video_frames = int(video_stream.get("nb_frames"))
video_width = int(video_stream.get("coded_width"))
video_height = int(video_stream.get("coded_height"))
interval = video_duration / video_frames
print(video_duration, video_frames, video_width, video_height)

# STEP 2 - LOAD TEST DATA

import h5py
from collections import namedtuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

graph_dpi = 300
graph_width_inches = video_width / graph_dpi
graph_height_inches = video_height / graph_dpi
fig, ax = plt.subplots(figsize=(graph_width_inches, graph_height_inches), dpi=graph_dpi)
canvas = FigureCanvas(fig)

f = h5py.File(data_file, "r")

Channel = namedtuple("Channel", [
    "name", "time", "data", "line"
])

channels = []

# Get NumPy arrays declared in advance to speed up processing
for channel_name in channel_names_to_plot:
    # Get NumPy arrays for "time" and "data" for the channel
    time = f["channels"][channel_name]["time"][:]
    data = f["channels"][channel_name]["data"][:]

    full_name = f["channels"][channel_name].attrs["name"]
    print(full_name)

    # time = time[::100]
    # data = data[::100]

    # Trim the data to the required start and end times and add
    # to our simplified "Channel" named tuple.
    start_time = data_time_at_video_start
    end_time = data_time_at_video_start + video_duration

    line = ax.plot(
        time[(start_time <= time) & (time <= start_time)],
        data[(start_time <= time) & (time <= start_time)],
    )[0]

    channel = Channel(
        full_name,
        time[(start_time <= time) & (time <= end_time)],
        data[(start_time <= time) & (time <= end_time)],
        line
    )
    channels.append(channel)

legend_entries = [channel.name for channel in channels]
print(legend_entries)
plt.legend(legend_entries, framealpha=0, labelcolor="white")
plt.xlim([data_time_at_video_start, data_time_at_video_start + video_duration])
plt.ylim([-30, 80])
plt.grid(linestyle="dashed")

# Transparency
fig.patch.set_alpha(0.0)  # Set figure background alpha
ax.patch.set_alpha(0.0)  # Set axes background alpha

# Axes colours
axes_color = "white"
ax.xaxis.label.set_color(axes_color)  # setting up X-axis label color to yellow
ax.yaxis.label.set_color(axes_color)  # setting up Y-axis label color to blue
ax.tick_params(axis='x', colors=axes_color)  # setting up X-axis tick color to red
ax.tick_params(axis='y', colors=axes_color)  # setting up Y-axis tick color to black
ax.spines['left'].set_color(axes_color)
ax.spines['top'].set_color(axes_color)
ax.spines['right'].set_color(axes_color)
ax.spines['bottom'].set_color(axes_color)


def update(frame):
    #start_time = data_time_at_video_start
    start_time = data_time_at_video_start + (frame - 1) * interval
    end_time = data_time_at_video_start + frame * interval
    for channel in channels:
        time = channel.time
        data = channel.data
        line = channel.line
        line.set_xdata(time[(start_time <= time) & (time <= end_time)])
        line.set_ydata(data[(start_time <= time) & (time <= end_time)])
        ax.draw_artist(line)
    return []

canvas.draw()
image = np.zeros((2160, 3840, 4))

import subprocess

# FFmpeg command
ffmpeg = subprocess.Popen(
    [
        "ffmpeg", "-y",
        "-i", "inputs/input.mp4",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgba",
        "-s", f"{video_width}x{video_height}",
        "-r", str(60),
        "-i", "-",
        "-filter_complex", "[0:0][1:0]overlay[out]",
        "-shortest",
        "-map", "[out]",
        "-map", "0:1",
        "-c:a", "copy",
#        "-vcodec", "h264_amf",
#        "-crf", "15",
#        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "output4.mp4",
    ],
    stdin=subprocess.PIPE,
)

render_start_time = time_library.time()
for j in range(video_frames):
    update(j)
    canvas.blit(ax.bbox)
    arr = np.asarray(canvas.buffer_rgba())
    ffmpeg.stdin.write(arr.tobytes())

render_end_time = time_library.time()

ffmpeg.stdin.close()
ffmpeg.wait()
print(f"Saved in {render_end_time - render_start_time} seconds")
