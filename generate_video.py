# Tom Danvers, 2025

video_file = "inputs/input.mp4"
data_file = "inputs/20250625-005-release.h5"
data_time_at_video_start = -3.46

channel_names_to_plot = ['PTX103', 'PTX104', 'PTX105']

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

print(video_duration, video_frames, video_width, video_height)

# STEP 2 - DEFINE PLOT OF DATA

import h5py
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation

f = h5py.File(data_file, "r")

video_time = 0

graph_dpi = 300
graph_width_inches = video_width / graph_dpi
graph_height_inches = video_height / graph_dpi

fig, ax = plt.subplots(figsize=(graph_width_inches, graph_height_inches), dpi=graph_dpi)

channel_lines = []


for channel_name in channel_names_to_plot:
    channel = f["channels"][channel_name]
    time = channel["time"][:]
    data = channel["data"][:]
    start_time = data_time_at_video_start
    end_time = data_time_at_video_start
    line = ax.plot(
        time[(start_time <= time) & (time <= end_time)],
        data[(start_time <= time) & (time <= end_time)]
    )[0]
    channel_lines.append((channel, line))

plt.legend(channel_names_to_plot)

interval = video_duration / video_frames
plt.xlim([data_time_at_video_start, data_time_at_video_start + video_duration])
plt.ylim([-1, 60])
fig.patch.set_alpha(0.0)  # Set figure background alpha
ax.patch.set_alpha(0.0)   # Set axes background alpha

axes_color = "white"

ax.xaxis.label.set_color(axes_color)  # setting up X-axis label color to yellow
ax.yaxis.label.set_color(axes_color)  # setting up Y-axis label color to blue
ax.tick_params(axis='x', colors=axes_color)  # setting up X-axis tick color to red
ax.tick_params(axis='y', colors=axes_color)  # setting up Y-axis tick color to black
ax.spines['left'].set_color(axes_color)
ax.spines['top'].set_color(axes_color)
ax.spines['right'].set_color(axes_color)
ax.spines['bottom'].set_color(axes_color)
plt.grid(linestyle="dashed")


def update(frame):
    start_time = data_time_at_video_start
    end_time = start_time + frame * interval
    for (channel, line) in channel_lines:
        time = channel["time"][:]
        data = channel["data"][:]
        line.set_xdata(time[(start_time <= time) & (time <= end_time)])
        line.set_ydata(data[(start_time <= time) & (time <= end_time)])


def progress(current_frame: int, total_frames: int):
    if current_frame % 10 == 0:
        print(current_frame, total_frames, 100 * current_frame/total_frames, "%")


ani = animation.FuncAnimation(fig=fig, func=update, frames=video_frames, interval=interval*1000)

# Pick a video codec that supports a transparent background
# https://github.com/matplotlib/matplotlib/blob/v3.10.3/lib/matplotlib/animation.py#L524
ani.save(filename="test2.mov", writer="ffmpeg", codec="png", progress_callback=progress)

f.close()
