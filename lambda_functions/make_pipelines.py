import json
import copy


def make_2_pipeline(channeldict):
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


def make_3_pipeline(channeldict, Nuclei_channel, Cells_channel):
    with open(f"/var/task/pipeline.json") as f:
        pipeline = json.load(f)
    f.close()
    # MeasureImageQuality
    pipeline["modules"][2]["settings"][6]["value"] = Nuclei_channel
    pipeline["modules"][2]["settings"][19]["value"] = Cells_channel
    # CorrectIlluminationCalculate
    pipeline["modules"][3]["settings"][0]["value"] = Nuclei_channel.replace("Orig", "")
    # CorrectIlluminationApply
    pipeline["modules"][4]["settings"][0]["value"] = Nuclei_channel.replace("Orig", "")
    # IdentifySecondaryObjects
    pipeline["modules"][6]["settings"][3]["value"] = Cells_channel.replace("Orig", "")
    # MeasureObjectIntensity
    pipeline["modules"][8]["settings"][0]["value"] = ', '.join(list(channeldict.values()))
    # MeasureImageIntensity
    pipeline["modules"][9]["settings"][0]["value"] = ', '.join(list(channeldict.values()))
    # Rescale Intensity
    pipeline["modules"][11]["settings"][0]["value"] = Nuclei_channel
    # Rescale Intensity
    pipeline["modules"][12]["settings"][0]["value"] = Cells_channel


def make_5_pipeline(channeldict, Nuclei_channel, Cells_channel):
    with open(f"/var/task/pipeline.json") as f:
        pipeline = json.load(f)
    f.close()

    CorrectIllumApply = []
    for channel in channeldict.values():
        setting = {
            "name": "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber",
            "text": "Select the input image",
            "value": channel,
        }
        CorrectIllumApply.append(setting)
        setting = {
            "name": "cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName",
            "text": "Name the output image",
            "value": channel.replace("Orig", ""),
        }
        CorrectIllumApply.append(setting)
        setting = {
            "name": "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber",
            "text": "Select the illumination function",
            "value": channel.replace("Orig", "Illum"),
        }
        CorrectIllumApply.append(setting)
        setting = {
            "name": "cellprofiler_core.setting.choice._choice.Choice",
            "text": "Select how the illumination function is applied",
            "value": "Divide",
        }
        CorrectIllumApply.append(setting)
    pipeline["modules"][2]["settings"] = CorrectIllumApply

    # CorrectIlluminationCalculate
    pipeline["modules"][3]["settings"][0]["value"] = Nuclei_channel.replace("Orig", "")
    # CorrectIlluminationApply
    pipeline["modules"][4]["settings"][0]["value"] = Nuclei_channel.replace("Orig", "")
    # IdentifySecondaryObjects
    pipeline["modules"][6]["settings"][3]["value"] = Cells_channel.replace("Orig", "")
    # Rescale Intensity
    pipeline["modules"][8]["settings"][0]["value"] = Nuclei_channel.replace("Orig", "")
    # Rescale Intensity
    pipeline["modules"][9]["settings"][0]["value"] = Cells_channel.replace("Orig", "")

    with open(f"/tmp/5_RunSegment.json", "w") as f:
        json.dump(pipeline, f, indent=4)

def make_7_pipeline(channeldict, Nuclei_channel, Cells_channel):
    with open(f"/var/task/pipeline.json") as f:
        pipeline = json.load(f)
    f.close()
    with open(f"/var/task/pipeline_end.json") as g:
        pipeline = json.load(g)
    g.close()

    orig_channel_list = list(channeldict.values())
    corrected_channel_list = [x.replace('Orig','') for x in channeldict.values()]

    # CorrectIlluminationApply
    CorrectIlluminationApply = []
    for channel in orig_channel_list:
        CorrectIlluminationApply.append(
            {
                "name": "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber",
                "text": "Select the input image",
                "value": f"{channel}",
            }
        )
        CorrectIlluminationApply.append(
            {
                "name": "cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName",
                "text": "Name the output image",
                "value": f"{channel.replace('Orig', '')}",
            }
        )
        CorrectIlluminationApply.append(
            {
                "name": "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber",
                "text": "Select the illumination function",
                "value": f"Illum{channel.replace('Orig', '')}",
            }
        )
        CorrectIlluminationApply.append(
            {
                "name": "cellprofiler_core.setting.choice._choice.Choice",
                "text": "Select how the illumination function is applied",
                "value": "Divide",
            }
        )
    CorrectIlluminationApply.append(
        {
            "name": "cellprofiler_core.setting._binary.Binary",
            "text": "Set output image values less than 0 equal to 0?",
            "value": "Yes",
        }
    )
    CorrectIlluminationApply.append(
        {
            "name": "cellprofiler_core.setting._binary.Binary",
            "text": "Set output image values greater than 1 equal to 1?",
            "value": "Yes",
        }
    )
    pipeline["modules"][2]["settings"] = CorrectIlluminationApply

    # CorrectIlluminationCalculate
    pipeline["modules"][2]["settings"][0]["value"] = Nuclei_channel.replace("Orig", "")
    # CorrectIlluminationApply
    pipeline["modules"][3]["settings"][0]["value"] = Nuclei_channel.replace("Orig", "")
    # IdentifySecondaryObjects
    pipeline["modules"][5]["settings"][3]["value"] = Cells_channel.replace("Orig", "")
    # MeasureColocalization
    pipeline["modules"][8]["settings"][0]["value"] = corrected_channel_list
    # MeasureGranularity
    pipeline["modules"][9]["settings"][0]["value"] = corrected_channel_list
    # MeasureObjectIntensity
    pipeline["modules"][10]["settings"][0]["value"] = corrected_channel_list
    # MeasureObjectIntensityDistribution
    pipeline["modules"][14]["settings"][0]["value"] = corrected_channel_list
    # MeasureTexture
    pipeline["modules"][16]["settings"][0]["value"] = corrected_channel_list
    # Special mito features
    if not any('mito' in x.lower() for x in channeldict.values()):
        pipeline["modules"][17]["attributes"]["enabled"] = False
        pipeline["modules"][18]["attributes"]["enabled"] = False
        pipeline["modules"][19]["attributes"]["enabled"] = False
        pipeline["modules"][20]["attributes"]["enabled"] = False
        pipeline["modules"][21]["attributes"]["enabled"] = False
    # MaskImage
    MaskImageModule = pipeline["modules"][26]
    for channel in corrected_channel_list:
        counter = 0
        MaskImageModule["attributes"]["module_num"] = 27 + counter
        MaskImageModule["settings"][0]["value"] = channel
        MaskImageModule["settings"][1]["value"] = f"{channel}__BackgroundOnly"
        pipeline["modules"][26 + counter] = MaskImageModule
        counter += 1
    # MeasureImageIntensity
    pipeline_end[0]["attributes"]["module_num"] = 27 + counter
    pipeline_end[0]["settings"][0] = corrected_channel_list + [f"{x}__BackgroundOnly" for x in corrected_channel_list]
    pipeline["modules"][26 + counter] = pipeline_end[0]
    # ExportToSpreadsheet
    pipeline_end[1]["attributes"]["module_num"] = 28 + counter
    # HOW TF DO I HANDLE SELECTION??
    pipeline["modules"][27 + counter] = pipeline_end[1]

    with open(f"/tmp/7_Analysis.json", "w") as f:
        json.dump(pipeline, f, indent=4)
