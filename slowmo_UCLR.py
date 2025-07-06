from main import LineGraphVideoOverlay
import h5py

LineGraphVideoOverlay.graph_dpi = 150

overlay = LineGraphVideoOverlay(
    video_file="inputs/UCLR_startup_003.mp4",
    output_path="outputs/UCLR_startup.mp4",
    data_time_at_video_start=-0.09922,
    title="UCLR Startup Pressures",
    ylabel="Pressure (bar)",
    slowmo_amount=16.6666
)

channel_names_to_plot = ['PTX101', 'PTX102', 'PTX103']

f = h5py.File("inputs/UCLR_startup.h5", "r")

for channel_name in channel_names_to_plot:
    time = f["channels"][channel_name]["time"][:]

    data = f["channels"][channel_name]["data"][:]

    full_name = f["channels"][channel_name].attrs["name"]
    print(full_name)

    overlay.add_channel(time, data, full_name)

overlay.render_video()
f.close()
