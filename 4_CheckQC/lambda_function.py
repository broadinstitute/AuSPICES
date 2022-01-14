import boto3
import os
import pandas as pd
import seaborn as sns
import string
import matplotlib as plt
from itertools import groupby

s3 = boto3.client("s3")


def lambda_handler(event, lambda_context):
    fullplate = event["trigger"]["plate"]
    plate = fullplate.split("__")[0]
    project_name = event["project_name"]
    batch = event["batch"]
    bucket = event["bucket"]

    input_folder = f"/home/ubuntu/bucket/projects/{project_name}/workspace/qc/{batch}/results/{plate}"
    output_folder = f"/tmp/qc"

    # Concatenate all QC data for the batch
    cellsdf = pd.DataFrame()
    imagedf = pd.DataFrame()
    nucleidf = pd.DataFrame()
    folderlist = os.listdir(input_folder)
    print("Concatenating folders")
    for folder in folderlist:
        if os.path.isdir(os.path.join(input_folder, folder)):
            nestedfolderlist = os.listdir(os.path.join(input_folder, folder))
            for nestedfolder in nestedfolderlist:
                plate = nestedfolder.split("-")[0]
                well = nestedfolder.split("-")[1][0:3]
                cellpath = os.path.join(
                    input_folder, folder, nestedfolder, "TopLineCells.csv"
                )
                if os.path.isfile(cellpath):
                    stepcellsdf = pd.read_csv(cellpath)
                    stepcellsdf["Metadata_Plate"] = plate
                    stepcellsdf["Metadata_Well"] = well
                    cellsdf = cellsdf.append(stepcellsdf, ignore_index=True)
                else:
                    print(f"TopLineCells.csv missing for {nestedfolder}")
                imagepath = os.path.join(
                    input_folder, folder, nestedfolder, "TopLineImage.csv"
                )
                if os.path.isfile(imagepath):
                    stepimagedf = pd.read_csv(imagepath)
                    stepimagedf["Metadata_Plate"] = plate
                    stepimagedf["Metadata_Well"] = well
                    imagedf = imagedf.append(stepimagedf, ignore_index=True)
                else:
                    print(f"TopLineImage.csv missing for {nestedfolder}")
                nucleipath = os.path.join(
                    input_folder, folder, nestedfolder, "TopLineNuclei.csv"
                )
                if os.path.isfile(nucleipath):
                    stepnucleidf = pd.read_csv(nucleipath)
                    stepnucleidf["Metadata_Plate"] = plate
                    stepnucleidf["Metadata_Well"] = well
                    nucleidf = nucleidf.append(stepnucleidf, ignore_index=True)
                else:
                    print(f"TopLineNuclei.csv missing for {nestedfolder}")
            print(f"{folder} is done")
    print("All folders concatenated")

    # Aggregate all metrics to the site level
    cellsdf = (
        cellsdf.drop(columns=["ObjectNumber"])
        .groupby(["Metadata_Plate", "Metadata_Well", "ImageNumber"])
        .mean()
        .reset_index()
    )
    imagedf = imagedf.drop(columns=["FileName_OrigOverlay2", "PathName_OrigOverlay2"])
    nucleidf = (
        nucleidf.drop(columns=["ObjectNumber"])
        .groupby(["Metadata_Plate", "Metadata_Well", "ImageNumber"])
        .mean()
        .reset_index()
    )

    # Make 384 Well Plate well:location map
    rowstring = string.ascii_uppercase[0:16]
    columns = range(1, 25)
    welllist = []

    location = []
    for i in range(1, len(rowstring) + 1):
        build_seq = list(zip((range(1, len(columns) + 1)), ([i] * len(columns)),))
        location += build_seq
    locdf = pd.DataFrame(location).rename(columns={0: "x_loc", 1: "y_loc"})

    for row in reversed(rowstring):
        for col in columns:
            welllist.append(row + f"{col:02}")
    locdf["Well"] = welllist

    # Aggregate all metrics to the well level
    cellsdf = (
        cellsdf.groupby(["Metadata_Plate", "Metadata_Well"])
        .mean()
        .reset_index()
    )
    # Merge locdf with csvs
    cellsplotdf = cellsdf.merge(locdf, left_on="Metadata_Well", right_on="Well")

    # Plot overview of Cells_Area with all plates scaled together
    sns.set_theme(style="whitegrid")

    g = sns.relplot(
        data=cellsplotdf,
        x="x_loc", y="y_loc", hue="AreaShape_Area", height=10,  sizes=(700,700),
        size="ImageNumber",row = "Metadata_Plate",
        palette="viridis",
    )

    # Correct graph labels
    ylabels = list(string.ascii_uppercase[:16])[::-1]
    yticks = list(range(1,17))
    xticks = list(range(1,25))
    g.ax.set_yticks(ticks=yticks)
    g.ax.set_yticklabels(labels=ylabels)
    g.ax.set_xticks(ticks=xticks)
    g.set(xlabel="", ylabel="", aspect="equal")

    # Correct legend display
    handles, labels = g.ax.get_legend_handles_labels()
    labels = [list(b) for a,b in groupby(labels,lambda x:x=='ImageNumber') if not a][0]
    handles = handles[:(len(labels)+1)]
    labels[0] = 'Cell Area'
    g.legend.remove()
    g.ax.legend(handles,labels, loc='right', bbox_to_anchor=(1.2, .5))

    if not os.path.exists(os.path.join(output_folder, "Cells_Area_plots")):
        os.makedirs(os.path.join(output_folder, "Cells_Area_plots"))
    output_file = os.path.join(
        output_folder, "Cells_Area_plots", f"Cells_Area_Overview.png"
    )
    g.savefig(output_file)

    # Plot a separate Cells_Area plot per plate

    for plate in cellsplotdf["Metadata_Plate"].unique():
        g = sns.relplot(
            data=cellsplotdf,
            x="x_loc", y="y_loc", hue="AreaShape_Area", height=10,  sizes=(700,700),
            size="ImageNumber",
            palette="viridis",
        )

        # Correct graph labels
        ylabels = list(string.ascii_uppercase[:16])[::-1]
        yticks = list(range(1,17))
        xticks = list(range(1,25))
        g.ax.set_yticks(ticks=yticks)
        g.ax.set_yticklabels(labels=ylabels)
        g.ax.set_xticks(ticks=xticks)
        g.set(xlabel="", ylabel="", aspect="equal")

        # Correct legend display
        handles, labels = g.ax.get_legend_handles_labels()
        labels = [list(b) for a,b in groupby(labels,lambda x:x=='ImageNumber') if not a][0]
        handles = handles[:(len(labels)+1)]
        labels[0] = 'Cell Area'
        g.legend.remove()
        g.ax.legend(handles,labels, loc='right', bbox_to_anchor=(1.2, .5))

        output_file = os.path.join(
            output_folder, "Cells_Area_plots", f"Cells_Area_{plate}.png"
        )
        g.savefig(output_file)

    # Upload all files to S3
    for subdir, dirs, files in os.walk(output_folder):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                key = f"projects/{project_name}/workspace/qc/{batch}/qc_analyzed/{full_path}"
                s3.upload_fileobj(data, bucket, key)
