import boto3
import botocore
import shutil
from pe2loaddata.__main__ import headless as pe2loaddata
import yaml
import pandas as pd

s3 = boto3.client("s3")


def lambda_handler(event, lambda_context):
    fullplate = event["trigger"]["plate"]
    plate = fullplate.split("__")[0]
    project_name = event["project_name"]
    batch = event["batch"]
    bucket = event["bucket"]
    channeldict = event["channeldict"]

    # Create channel map
    if channeldict == "Standard_1BF":
        channelmap = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield": "OrigBrightfield",
        }
    elif channeldict == "Standard_1BF_V":
        channelmap = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield CP": "OrigBrightfield",
        }
    elif channeldict == "Standard_3BF":
        channelmap = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield": "OrigBrightfield",
            "Brightfield H": "OrigBrightfield_H",
            "Brightfield L": "OrigBrightfield_L",
        }
    else:
        if type(channeldict) is not dict:
            print(
                "In metadata: enter string for existing map into channeldict enter new map as dictionary."
            )
            return
        else:
            channelmap = channeldict

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
    if event["zproject"]:
        index_directory = (
            f"s3://{bucket}/projects/{project_name}/{batch}/images_unprojected/{plate}"
        )
        index_file = f"s3://{bucket}/projects/{project_name}/{batch}/images_unprojected/{fullplate}/Images/Index.idx.xml"
    else:
        index_directory = (
            f"s3://{bucket}/projects/{project_name}/{batch}/images/{plate}"
        )
        index_file = f"s3://{bucket}/projects/{project_name}/{batch}/images/{fullplate}/Images/Index.idx.xml"
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
    zproj_output_on_bucket_name = f"projects/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data_unprojected.csv"

    if event["zproject"]:
        print("CSVs will include z-projection.")
        with open(output, "rb") as a:
            s3.put_object(Body=a, Bucket=bucket, Key=zproj_output_on_bucket_name)

        csv_df = pd.read_csv(output)
        final_z = max(csv_df["Metadata_PlaneID"].unique())
        csv_df = csv_df.loc[csv_df["Metadata_PlaneID"] == final_z]
        csv_df = csv_df.replace(regex=r"images_unprojected", value="images")

        csv_with_illum_df = pd.read_csv(illum_output)
        csv_with_illum_df = csv_with_illum_df.loc[
            csv_with_illum_df["Metadata_PlaneID"] == final_z
        ]
        csv_with_illum_df = csv_with_illum_df.replace(
            regex=r"images_unprojected", value="images"
        )

        csv_df.to_csv(output, index=False)
        with open(output, "rb") as a:
            s3.put_object(Body=a, Bucket=bucket, Key=output_on_bucket_name)
        csv_with_illum_df.to_csv(illum_output, index=False)
        with open(illum_output, "rb") as a:
            s3.put_object(Body=a, Bucket=bucket, Key=illum_output_on_bucket_name)
    else:
        print("CSVs will not include z-projection.")
        with open(output, "rb") as a:
            s3.put_object(Body=a, Bucket=bucket, Key=output_on_bucket_name)
        with open(illum_output, "rb") as a:
            s3.put_object(Body=a, Bucket=bucket, Key=illum_output_on_bucket_name)
