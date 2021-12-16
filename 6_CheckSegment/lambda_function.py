import json
import os
import sys
import time
import numpy as np

import boto3

sys.path.append("/opt/pooled-cell-painting-lambda")

import run_DCP
import create_batch_jobs
import helpful_functions

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Step Information
metadata_file_name = "/tmp/metadata.json"
step = "4"

# AWS Configuration Specific to this Function
config_dict = {
    "DOCKERHUB_TAG": "cellprofiler/distributed-fiji:latest",
    "SCRIPT_DOWNLOAD_URL": "https://raw.githubusercontent.com/broadinstitute/pooled-cell-painting-image-processing/master/FIJI/BatchStitchPooledCellPainting_StitchAndCrop_Headless.py",
    "TASKS_PER_MACHINE": "1",
    "MACHINE_TYPE": ["m4.2xlarge"],
    "MACHINE_PRICE": "0.25",
    "EBS_VOL_SIZE": "400",
    "DOWNLOAD_FILES": "False",
    "MEMORY": "31000",
    "SQS_MESSAGE_VISIBILITY": "43200",
    "MIN_FILE_SIZE_BYTES": "1",
    "NECESSARY_STRING": "",
}


def lambda_handler(event, context):
    if event["run_segment"]:
        prefix = f"projects/{event['project_name']}/workspace/"
        bucket = event["bucket"]
        batch = event["batch"]
        config_dict["APP_NAME"] = event["project_name"] + "_Stitch"
        project_name = event["project_name"]

        # Include/Exclude Plates
        exclude_plates = event["exclude_plates"]
        include_plates = event["include_plates"]
        platelist = []
        for x in event["Output_0"]["Payload"]:
            shortplate = x["plate"].split("__")[0]
            platelist.append(shortplate)
        if exclude_plates:
            platelist = [i for i in platelist if i not in exclude_plates]
        if include_plates:
            platelist = include_plates

        run_DCP.run_setup(bucket, prefix, batch, config_dict, cellprofiler=False)

        # make the jobs
        create_batch_jobs.create_batch_jobs_4(
            bucket, project_name, batch, platelist,
        )

        # Start a cluster
        run_DCP.run_cluster(bucket, prefix, batch, len(platelist), config_dict)

        run_DCP.setup_monitor(bucket, prefix, config_dict)
