import datetime
import os, sys
import json
import boto3
import numpy
import pandas

sys.path.append("/opt/jump-cellpainting-lambda")

import run_DCP
import create_batch_jobs
import helpful_functions

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Step information
metadata_file_name = "/tmp/metadata.json"
step = "5"

# AWS Configuration Specific to this Function
config_dict = {
    "DOCKERHUB_TAG": "cellprofiler/distributed-cellprofiler:2.0.0_4.1.3",
    "TASKS_PER_MACHINE": "1",
    "MACHINE_TYPE": ["m4.xlarge"],
    "MACHINE_PRICE": "0.10",
    "EBS_VOL_SIZE": "22",
    "DOWNLOAD_FILES": "False",
    "DOCKER_CORES": "4",
    "MEMORY": "15000",
    "SECONDS_TO_START": "180",
    "SQS_MESSAGE_VISIBILITY": "1800",
    "CHECK_IF_DONE_BOOL": "False",
    "EXPECTED_NUMBER_FILES": "5",
    "MIN_FILE_SIZE_BYTES": "1",
    "NECESSARY_STRING": "",
}


def lambda_handler(event, context):
    prefix = f"projects/{event['project_name']}/{event['batch']}/images/"
    bucket = event['bucket']
    config_dict["APP_NAME"] = event["project_name"] + "_Segment"
    pipeline_name = event["SegmentPipelineName"]
    project_name = event["project_name"]

    # Include/Exclude Plates
    exclude_plates = event['exclude_plates']
    include_plates = event['include_plates']
    platelist = event["platelist"]
    if "exclude_plates":
        platelist = [i for i in platelist if i not in exclude_plates]
    if "include_plates":
        platelist = include_plates

    # now let's do our stuff!
    app_name = run_DCP.run_setup(bucket_name, prefix, batch, config_dict)

    # make the jobs
    create_batch_jobs.create_batch_jobs_5(
        image_prefix, batch, pipeline_name, plate_and_well_list, app_name
    )

    # Start a cluster
    run_DCP.run_cluster(
        bucket_name, prefix, batch, len(plate_and_well_list), config_dict,
    )

    # Run the monitor
    run_DCP.run_monitor(bucket_name, prefix, batch, step, config_dict)
    monitor_name = boto3_setup.upload_monitor(bucket_name, prefix, batch, step, config_dict)
    return (monitor_name)
