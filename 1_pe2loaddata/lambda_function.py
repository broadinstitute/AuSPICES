import boto3
import botocore
import os
import sys
import subprocess
import xml.etree.ElementTree as ET
from pe2loaddata.__main__ import headless as pe2loaddata

s3 = boto3.client("s3")


def lambda_handler(event, lambda_context):
    fullplate = event["trigger"]["plate"]
    plate = fullplate.split("__")[0]
    project_name = event["project_name"]
    batch = event["batch"]
    bucket = event["bucket"]

    # (Eventually) Update config.yml based on Index.ids.xml file
    s3xmlfilepath = (
        f"projects/{project_name}/{batch}/images/{fullplate}/Images/Index.idx.xml"
    )
    localxmlfilepath = "/tmp/Index.idx.xml"

    with open(localxmlfilepath, "wb") as f:
        try:
            s3.download_fileobj(bucket, s3xmlfilepath, f)
        except botocore.exceptions.ClientError as error:
            print("Can't find the xml file. Something's up.")
            return
    with open(localxmlfilepath, "r") as input_xml:
        xmlfile = ET.parse(input_xml)
        root = xmlfile.getroot()

    yamlpath = "./config.yml"
    # (Eventually) Open yaml
    # (Eventually) Edit yaml to match xml

    # Trigger pe2loaddata
    output = f"/tmp/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data.csv"
    index_directory = f"s3://{bucket}/projects/{project_name}/{batch}/images/"
    index_file = f"s3://{bucket}/projects/{project_name}/{batch}/images/{plate}/Images/Index.idx.xml"
    illum_directory = (
        f"s3://{bucket}/projects/{project_name}/{batch}/illum/{plate}"
    )
    illum_output = f"/tmp/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data_with_illum.csv"
    sub_string_out = f"s3://"
    sub_string_in = f"bucket/"

    pe2loaddata(
    yamlpath,
    output,
    index_directory=index_directory,
    index_file=index_file,
    illum=True,
    illum_directory=illum_directory,
    plate_id=plate,
    illum_output=illum_output,
    sub_string_out=sub_string_out,
    sub_string_in=sub_string_in
    )
