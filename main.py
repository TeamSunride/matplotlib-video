from pathlib import Path
import ffmpeg as ffmpeg_library
import logging
import matplotlib.pyplot as plt
import matplotlib
import subprocess
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from typing import Callable, List
import h5py
from collections import namedtuple

logging.basicConfig(level=logging.INFO)
matplotlib.use('Agg')

plt.rcParams.update({
    # Legend
    "legend.framealpha": 0.0,
    "legend.labelcolor": "white",

    # Axes background and grid
    "axes.facecolor": "none",  # transparent background
    "axes.edgecolor": "white",  # spine color
    "axes.labelcolor": "white",  # axis label color
    "axes.titlecolor": "white",

    # Tick color
    "xtick.color": "white",
    "ytick.color": "white",

    # Grid style
    "grid.linestyle": "dashed",

    # Figure background
    "figure.facecolor": "none",  # transparent background
})


class VideoOverlay:
    duration: float
    frames: int
    width: int
    height: int
    interval: float
    video_file: Path
    output_path: str

    def __init__(self, video_file: str, output_path: str, slowmo_amount=None):
        self.video_file = Path(video_file)
        self.output_path = output_path

        if not self.video_file.is_file():
            raise ValueError(f"Provided video_file path is not a file: {self.video_file}")

        probe = ffmpeg_library.probe(self.video_file)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        if not video_streams:
            raise ValueError(f"No video stream found in file {self.video_file}")

        video_stream = video_streams[0]
        self.duration = float(video_stream.get("duration"))
        self.frames = int(video_stream.get("nb_frames"))
        self.width = int(video_stream.get("coded_width"))
        self.height = int(video_stream.get("coded_height"))

        if slowmo_amount is not None:
            self.duration /= slowmo_amount

        self.interval = self.duration / self.frames

        logging.info(f"Loaded video: {self.video_file}")
        logging.info(f"Duration: {self.duration:.2f} seconds")
        logging.info(f"Frames: {self.frames}")
        logging.info(f"Dimensions: {self.width}x{self.height}")

    def _run(self, plot_function: Callable[[int], np.ndarray]):
        self.canvas.draw()

        ffmpeg = subprocess.Popen(
            [
                "ffmpeg", "-y",
                "-hwaccel", "d3d11va",
                "-i", str(self.video_file),
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-pix_fmt", "rgba",
                "-s", f"{self.width}x{self.height}",
                "-r", str(60),
                "-i", "-",
                "-filter_complex", "[0:0][1:0]overlay[out]",
                "-shortest",
                "-map", "[out]",
                "-map", "0:1?",
                "-c:a", "copy",
                #        "-vcodec", "h264_amf",
                #        "-crf", "15",
                #        "-preset", "veryfast",
                "-c:v", "h264_amf",
                "-pix_fmt", "yuv420p",
                self.output_path,
            ],
            stdin=subprocess.PIPE,
        )

        for frame in range(self.frames):
            arr = plot_function(frame)
            ffmpeg.stdin.write(arr.tobytes())

        ffmpeg.stdin.close()
        ffmpeg.wait()


LineGraphChannel = namedtuple("Channel", [
    "time", "data", "label", "line"
])


class LineGraphVideoOverlay(VideoOverlay):
    channels: List[LineGraphChannel] = []
    graph_dpi = 300
    ylim_max = 0
    ylim_min = 0
    ylim_margin = 1.1
    user_ylim = None

    def __init__(self, video_file: str, output_path: str, data_time_at_video_start: float, title: str, ylabel: str,
                 ylim=None, slowmo_amount=None):
        super().__init__(video_file=video_file, output_path=output_path, slowmo_amount=slowmo_amount)
        graph_width_inches = self.width / self.graph_dpi
        graph_height_inches = self.height / self.graph_dpi
        plt.figure()
        self.fig, self.ax = plt.subplots(figsize=(graph_width_inches, graph_height_inches), dpi=self.graph_dpi)
        self.canvas = FigureCanvasAgg(self.fig)
        self.data_time_at_video_start = data_time_at_video_start
        self.start_time = data_time_at_video_start
        self.end_time = data_time_at_video_start + self.duration
        self.title = title
        self.ylabel = ylabel
        self.ylim = ylim
        self.channels = []

    def add_channel(self, channel_time, channel_data, channel_label):
        new_line = self.ax.plot(
            channel_time[(self.start_time <= channel_time) & (channel_time <= self.start_time)],
            channel_data[(self.start_time <= channel_time) & (channel_time <= self.start_time)],
        )[0]

        new_channel = LineGraphChannel(time=channel_time, data=channel_data, label=channel_label, line=new_line)

        self.ylim_max = max(self.ylim_max, np.max(new_channel.data))
        self.ylim_min = min(self.ylim_min, np.min(new_channel.data))

        self.channels.append(new_channel)

    def update(self, frame):
        timeslice_start = self.data_time_at_video_start + (frame - 1) * self.interval
        timeslice_end = self.data_time_at_video_start + frame * self.interval
        for c in self.channels:
            c.line.set_xdata(c.time[(timeslice_start <= c.time) & (c.time <= timeslice_end)])
            c.line.set_ydata(c.data[(timeslice_start <= c.time) & (c.time <= timeslice_end)])
            self.ax.draw_artist(c.line)
        self.canvas.blit(self.ax.bbox)
        arr = np.asarray(self.canvas.buffer_rgba())
        return arr

    def render_video(self):
        plt.legend([c.label for c in self.channels])
        plt.xlim([self.data_time_at_video_start, self.data_time_at_video_start + self.duration])
        print([self.ylim_min * self.ylim_margin, self.ylim_max * self.ylim_margin])
        if self.ylim is None:
            plt.ylim([self.ylim_min * self.ylim_margin, self.ylim_max * self.ylim_margin])
        else:
            plt.ylim(self.ylim)
        plt.grid()
        plt.title(self.title)
        plt.ylabel(self.ylabel)
        plt.xlabel("Time (seconds)")

        self._run(self.update)


if __name__ == "__main__":
    overlay = LineGraphVideoOverlay(
        video_file="inputs/input.mp4",
        output_path="outputs/thrust.mp4",
        data_time_at_video_start=-3.46,
        title="Thrust",
        ylabel="Thrust (N)",
        # ylim=[-1, 2]
    )
    channel_names_to_plot = ['LC190']

    f = h5py.File("inputs/20250625-005-release.h5", "r")

    for channel_name in channel_names_to_plot:
        time = f["channels"][channel_name]["time"][:]
        data = f["channels"][channel_name]["data"][:]

        full_name = f["channels"][channel_name].attrs["name"]
        print(full_name)

        overlay.add_channel(time, data, full_name)

    overlay.render_video()
    f.close()

# if __name__ == "__main__2":
#     data_time_at_video_start = -3.46
#     channel_names_to_plot = ['TCX101', 'TCX102', 'TCX103', 'TCX104', 'TCX105', 'TCX106', 'TCX107', 'TCX108', 'TCX109',
#                              'TCX110', 'TCX111']
#
#     overlay = VideoOverlay(video_file="inputs/input.mp4", output_path="outputs/output.mp4")
#
#     fig, ax, canvas = overlay.create_figure()
#
#     f = h5py.File("inputs/20250625-005-release.h5", "r")
#
#     Channel = namedtuple("Channel", [
#         "name", "time", "data", "line"
#     ])
#
#     channels = []
#
#     # Get NumPy arrays declared in advance to speed up processing
#     for channel_name in channel_names_to_plot:
#         # Get NumPy arrays for "time" and "data" for the channel
#         time = f["channels"][channel_name]["time"][:]
#         data = f["channels"][channel_name]["data"][:]
#
#         full_name = f["channels"][channel_name].attrs["name"]
#         print(full_name)
#
#         # Trim the data to the required start and end times and add
#         # to our simplified "Channel" named tuple.
#         start_time = data_time_at_video_start
#         end_time = data_time_at_video_start + overlay.duration
#
#         line = ax.plot(
#             time[(start_time <= time) & (time <= start_time)],
#             data[(start_time <= time) & (time <= start_time)],
#         )[0]
#
#         channel = Channel(
#             full_name,
#             time[(start_time <= time) & (time <= end_time)],
#             data[(start_time <= time) & (time <= end_time)],
#             line
#         )
#         channels.append(channel)
#
#     legend_entries = [channel.name for channel in channels]
#     plt.legend(legend_entries)
#     plt.xlim([data_time_at_video_start, data_time_at_video_start + overlay.duration])
#     plt.ylim([-30, 80])
#     plt.grid()
#
#
#     def update(frame):
#         start_time = data_time_at_video_start + (frame - 1) * overlay.interval
#         end_time = data_time_at_video_start + frame * overlay.interval
#         for channel in channels:
#             time = channel.time
#             data = channel.data
#             line = channel.line
#             line.set_xdata(channel.time[(start_time <= channel.time) & (channel.time <= end_time)])
#             line.set_ydata(channel.data[(start_time <= channel.time) & (channel.time <= end_time)])
#             ax.draw_artist(channel.line)
#         canvas.blit(ax.bbox)
#         arr = np.asarray(canvas.buffer_rgba())
#         return arr
#
#
#     overlay.run(plot_function=update)
