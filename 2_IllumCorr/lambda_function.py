import sys
import boto3

sys.path.append("/opt/jump-cellpainting-lambda")

import run_DCP
import create_batch_jobs

s3 = boto3.client("s3")

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
    prefix = f"projects/{event['input']['project_name']}/workspace/"
    bucket = event["input"]["bucket"]
    batch = event["input"]["batch"]
    config_dict["APP_NAME"] = event["input"]["project_name"] + "_Illum"
    pipeline_name = event["input"]["IllumPipelineName"]
    project_name = event["input"]["project_name"]

    # Include/Exclude Plates
    exclude_plates = event["input"]["exclude_plates"]
    include_plates = event["input"]["include_plates"]
    platelist = []
    for x in event["input"]["Output_0"]["Payload"]:
        platelist.append(x["plate"])
    if exclude_plates:
        platelist = [i for i in platelist if i not in exclude_plates]
    if include_plates:
        platelist = include_plates

    # Run DCP
    run_DCP.run_setup(bucket, prefix, batch, config_dict)

    create_batch_jobs.create_batch_jobs_2(project_name, pipeline_name, platelist, batch)

    run_DCP.run_cluster(bucket, prefix, batch, len(platelist), config_dict)

    run_DCP.create_sqs_alarms(config_dict)
