import boto3
import botocore
import shutil
from pe2loaddata.__main__ import headless as pe2loaddata
import yaml
import pandas as pd
import sys

sys.path.append("/opt/jump-cellpainting-lambda")

import channel_dicts

s3 = boto3.client("s3")


def lambda_handler(event, lambda_context):
    platename_replacementdict = event["platename_replacementdict"]
    fullplate = event["trigger"]["plate"]
    plate = fullplate.split("__")[0]
    project_name = event["project_name"]
    batch = event["batch"]
    bucket = event["bucket"]
    channeldict = event["channeldict"]

    # Import channel_dicts
    if type(channeldict) is dict:
        channelmap = channeldict
    else:
        channelmap = channel_dicts.find_map(channeldict)
        if not channelmap:
            print(
                "channeldict in metadata not valid. Enter string for existing map or enter new map as dictionary."
            )
            return

    # Load and edit config file with channel map
    shutil.copy("./config.yml", "/tmp/config.yml")
    config_file = "/tmp/config.yml"
    with open(config_file, "r") as fd:
        config = yaml.load(fd, Loader=yaml.BaseLoader)
    config["channels"] = channelmap
    with open(config_file, "w") as fd:
        yaml.dump(config, fd, Dumper=yaml.Dumper)

    # Trigger pe2loaddata
    output = f"/tmp/load_data.csv"
    index_directory = (
        f"s3://{bucket}/projects/{project_name}/{batch}/images/{plate}"
    )
    try:
        s3.head_object(Bucket=bucket, Key=f"projects/{project_name}/{batch}/images/{fullplate}/Images/Index.idx.xml")
        index_file = f"s3://{bucket}/projects/{project_name}/{batch}/images/{fullplate}/Images/Index.idx.xml"
    except:
        s3.head_object(Bucket=bucket, Key=f"projects/{project_name}/{batch}/images/{fullplate}/Images/Index.xml")
        index_file = f"s3://{bucket}/projects/{project_name}/{batch}/images/{fullplate}/Images/Index.xml"
    illum_directory = f"projects/{project_name}/{batch}/illum/{plate}"
    illum_output = f"/tmp/load_data_with_illum.csv"
    sub_string_out = "projects"
    sub_string_in = "/home/ubuntu/bucket/projects"

    pe2loaddata(
        config_file,
        output,
        index_directory=index_directory,
        index_file=index_file,
        illum=True,
        illum_directory=illum_directory,
        plate_id=plate,
        illum_output=illum_output,
        sub_string_out=sub_string_out,
        sub_string_in=sub_string_in,
        search_subdirectories=True,
    )

    # Upload .csvs to S3
    output_on_bucket_name = (
        f"projects/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data.csv"
    )
    illum_output_on_bucket_name = f"projects/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data_with_illum.csv"
    
    if platename_replacementdict:
        print("Platename in CSVs changed according to platename_replacementdict")
        csv_df = pd.read_csv(output)
        csv_with_illum_df = pd.read_csv(illum_output)
        for origname, newname in list(platename_replacementdict.items()):
            samplepath = [x for x in csv_df.columns if "Path" in x][0]
            if origname in csv_df[samplepath][1]:
                csv_df["Metadata_Plate"] = newname
                csv_df.to_csv(output, index=False)
                csv_with_illum_df["Metadata_Plate"] = newname
                csv_with_illum_df.to_csv(illum_output, index=False)
                plate = newname

    with open(output, "rb") as a:
        s3.put_object(Body=a, Bucket=bucket, Key=output_on_bucket_name)
    with open(illum_output, "rb") as a:
        s3.put_object(Body=a, Bucket=bucket, Key=illum_output_on_bucket_name)

    if event["zproject"]:
        print("CSVs will include z-projection.")
        zproj_output_on_bucket_name = f"projects/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data_projected.csv"

        final_z = max(csv_df["Metadata_PlaneID"].unique())
        csv_df = csv_df.loc[csv_df["Metadata_PlaneID"] == final_z]
        csv_df = csv_df.replace(regex=r"images", value="images_projected")
        csv_df = csv_df.replace(regex=fullplate, value=plate)
        csv_df.to_csv(output, index=False)
        with open(output, "rb") as a:
            s3.put_object(Body=a, Bucket=bucket, Key=zproj_output_on_bucket_name)
