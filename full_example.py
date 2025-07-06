from main import LineGraphVideoOverlay
import h5py

airborne_ID = "20250625-008"
test_title = f"Test 3 {airborne_ID}"

f = h5py.File(f"inputs/SF5/{airborne_ID}-release.h5", "r")
video_file = f"inputs/SF5/{airborne_ID}B_2160p60.mp4"
data_time_at_video_start = -3.4992

output_folder = "inputs/SF5/processed"


def create_video(output_path, channel_list, title, ylabel):
    overlay = LineGraphVideoOverlay(
        video_file=video_file,
        output_path=output_path,
        data_time_at_video_start=data_time_at_video_start,
        title=title,
        ylabel=ylabel,
    )

    for channel_name in channel_list:
        time = f["channels"][channel_name]["time"][:]
        data = f["channels"][channel_name]["data"][:]

        full_name = f["channels"][channel_name].attrs["name"]
        print(full_name)

        overlay.add_channel(time, data, full_name)

    overlay.render_video()


create_video(
    output_path=f"{output_folder}/{test_title} Pressures.mp4",
    channel_list=['PTX101', 'PTX102', 'PTX103', 'PTX104', 'PTX105', 'PTX106'],
    ylabel="Pressure (bar)",
    title=f"{test_title}: Experiment Pressures"
)

create_video(
    output_path=f"{output_folder}/{test_title} Temperatures.mp4",
    channel_list=['TCX101', 'TCX102', 'TCX103', 'TCX104', 'TCX105', 'TCX106', 'TCX107', 'TCX108', 'TCX109', 'TCX110', 'TCX111'],
    ylabel="Temperature (C)",
    title=f"{test_title}: Experiment Temperatures"
)

create_video(
    output_path=f"{output_folder}/{test_title} Mass Flows.mp4",
    channel_list=['M730', 'M801'],
    ylabel="Mass Flow Rate (kg/s)",
    title=f"{test_title}: Mass Flows"
)

create_video(
    output_path=f"{output_folder}/{test_title} Thrust.mp4",
    channel_list=['LC190'],
    ylabel="Thrust (N)",
    title=f"{test_title}: Thrust"
)

create_video(
    output_path=f"{output_folder}/{test_title} Thrust.mp4",
    channel_list=['LC190'],
    ylabel="Thrust (N)",
    title=f"{test_title}: Thrust"
)

f.close()
