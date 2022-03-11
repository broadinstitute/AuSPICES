import json
import copy


def make_2_pipeline(bucket, channeldict):
    with open(f"/var/task/pipeline_pieces.json") as f:
        pipeline_pieces = json.load(f)
    f.close()

    cppipe = copy.deepcopy(pipeline_pieces["cppipe"])

    channel_group = 0
    for channel in channeldict.values():
        Resize_down = copy.deepcopy(pipeline_pieces["Resize_down"])
        CorrectIlluminationCalculate = copy.deepcopy(
            pipeline_pieces["CorrectIlluminationCalculate"]
        )
        Resize_up = copy.deepcopy(pipeline_pieces["Resize_up"])
        Save = copy.deepcopy(pipeline_pieces["Save"])

        # Resize_down
        Resize_down["attributes"]["module_num"] = 2 + channel_group * 4
        for setting in range(0, len(Resize_down["settings"])):
            text = Resize_down["settings"][setting]["text"]
            if "Select the input image" in text:
                Resize_down["settings"][setting]["value"] = channel
            if "Name the output image" in text:
                Resize_down["settings"][setting]["value"] = f"{channel}_resize_down"
        # CorrectIlluminationCalculate
        CorrectIlluminationCalculate["attributes"]["module_num"] = 3 + channel_group * 4
        for setting in range(0, len(CorrectIlluminationCalculate["settings"])):
            text = CorrectIlluminationCalculate["settings"][setting]["text"]
            if "Select the input image" in text:
                CorrectIlluminationCalculate["settings"][setting][
                    "value"
                ] = f"{channel}_resize_down"
            if "Name the output image" in text:
                if "Orig" in channel:
                    illum_name = f'Illum{channel.replace("Orig", "")}'
                else:
                    illum_name = f"Illum{channel}"
                CorrectIlluminationCalculate["settings"][setting]["value"] = illum_name
        # Resize_up
        Resize_up["attributes"]["module_num"] = 4 + channel_group * 4
        for setting in range(0, len(Resize_up["settings"])):
            text = Resize_up["settings"][setting]["text"]
            if "Select the input image" in text:
                Resize_up["settings"][setting]["value"] = illum_name
            if "Name the output image" in text:
                Resize_up["settings"][setting]["value"] = f"Upsampled{illum_name}"
        # Save
        Save["attributes"]["module_num"] = 5 + channel_group * 4
        for setting in range(0, len(Save["settings"])):
            text = Save["settings"][setting]["text"]
            if "Select the image to save" in text:
                Save["settings"][setting]["value"] = f"Upsampled{illum_name}"
            if "Enter single file name" in text:
                Save["settings"][setting]["value"] = f"\\g<Plate>_{illum_name}"

        # Add new modules to file
        cppipe["modules"].append(Resize_down)
        cppipe["modules"].append(CorrectIlluminationCalculate)
        cppipe["modules"].append(Resize_up)
        cppipe["modules"].append(Save)
        channel_group += 1

    cppipe["module_count"] = len(cppipe["modules"])

    with open(f"/tmp/2_IllumCorr.json", "w") as f:
        json.dump(cppipe, f, indent=4)

    return
