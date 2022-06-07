import sys

sys.path.append("/opt/jump-cellpainting-lambda")

import run_DCP
import create_batch_jobs

# AWS Configuration Specific to this Function
config_dict = {
    "DOCKERHUB_TAG": "cellprofiler/distributed-fiji:latest",
    "SCRIPT_DOWNLOAD_URL": "https://raw.githubusercontent.com/broadinstitute/AuSPICEs/main/6_CheckSegment/make_fiji_montages.py",
    "TASKS_PER_MACHINE": "1",
    "MACHINE_TYPE": ["m4.2xlarge"],
    "MACHINE_PRICE": "0.25",
    "EBS_VOL_SIZE": "40",
    "DOWNLOAD_FILES": "False",
    "MEMORY": "31000",
    "SQS_MESSAGE_VISIBILITY": "600",
    "MIN_FILE_SIZE_BYTES": "1",
    "NECESSARY_STRING": "",
}


def lambda_handler(event, context):
    prefix = f"projects/{event['project_name']}/workspace/"
    bucket = event["bucket"]
    batch = event["batch"]
    config_dict["APP_NAME"] = event["project_name"] + "_Montage"
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

    config_dict["EXPECTED_NUMBER_FILES"] = 0

    run_DCP.run_setup(bucket, prefix, batch, config_dict, type="FIJI")

    # make the jobs
    create_batch_jobs.create_batch_jobs_6(
        bucket, project_name, batch, platelist,
    )

    # Start a cluster
    run_DCP.run_cluster(bucket, prefix, batch, len(platelist), config_dict)

    run_DCP.setup_monitor(bucket, prefix, config_dict)
