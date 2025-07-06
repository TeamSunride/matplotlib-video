from main import LineGraphVideoOverlay
import h5py

LineGraphVideoOverlay.graph_dpi = 150

overlay = LineGraphVideoOverlay(
    video_file="inputs/20250625-005.mp4",
    output_path="outputs/slowmo_Pc.mp4",
    data_time_at_video_start=-0.09922,
    # data_time_at_video_start=-1.6536,
    title="Chamber Pressure (1000fps)",
    ylabel="Pressure (bar)",
    slowmo_amount=16.6666
)

channel_names_to_plot = ['PTX103']

f = h5py.File("inputs/20250625-005-release.h5", "r")

for channel_name in channel_names_to_plot:
    time = f["channels"][channel_name]["time"][:]

    data = f["channels"][channel_name]["data"][:]

    full_name = f["channels"][channel_name].attrs["name"]
    print(full_name)

    overlay.add_channel(time, data, full_name)

overlay.render_video()
f.close()