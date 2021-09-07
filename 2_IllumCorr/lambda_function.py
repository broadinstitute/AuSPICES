import json
import os
import sys
import boto3

sys.path.append("/opt/jump-cellpainting-lambda")

import run_DCP
import create_batch_jobs
import boto3_setup

s3 = boto3.client("s3")

# Step information
metadata_file_name = "/tmp/metadata.json"
step = "2"

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
    "SQS_MESSAGE_VISIBILITY": "28800",
    "CHECK_IF_DONE_BOOL": "True",
    "EXPECTED_NUMBER_FILES": "5",
    "MIN_FILE_SIZE_BYTES": "1",
    "NECESSARY_STRING": "",
}


def lambda_handler(event, lambda_context):
    prefix = f"projects/{event['project_name']}/{event['batch']}/images/"
    bucket = event['bucket']
    config_dict["APP_NAME"] = event["project_name"] + "_Illum"
    pipeline_name = event["IllumPipelineName"]
    project_name = event["project_name"]

    # Include/Exclude Plates
    exclude_plates = event['exclude_plates']
    include_plates = event['include_plates']
    platelist = event["platelist"]
    if "exclude_plates":
        platelist = [i for i in platelist if i not in exclude_plates]
    if "include_plates":
        platelist = include_plates

    # Run DCP
    run_DCP.run_setup(bucket, prefix, batch, config_dict)

    create_batch_jobs.create_batch_jobs_2(
        project_name, pipeline_name, platelist, batchsuffix
    )

    run_DCP.run_cluster(bucket, prefix, batch, len(platelist), config_dict)

    # Write out current monitor
    monitor_name = boto3_setup.upload_monitor(
        bucket_name, prefix, batch, step, config_dict
    )
    return (monitor_name)
