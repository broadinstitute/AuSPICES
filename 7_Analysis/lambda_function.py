import sys

sys.path.append("/opt/jump-cellpainting-lambda")

import run_DCP
import create_batch_jobs

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
    project_name = event["project_name"]
    batch = event["batch"]
    prefix = f"projects/{project_name}/workspace/"
    bucket = event["bucket"]
    config_dict["APP_NAME"] = f"{project_name}_Analysis"
    pipeline_name = event["AnalysisPipelineName"]

    # Include/Exclude Plates
    exclude_plates = event["exclude_plates"]
    include_plates = event["include_plates"]
    platelist = []
    for x in event["Output_0"]["Payload"]:
        shortplate = x["plate"].split('__')[0]
        platelist.append(shortplate)
    if exclude_plates:
        platelist = [i for i in platelist if i not in exclude_plates]
    if include_plates:
        platelist = include_plates

    # Run DCP
    run_DCP.run_setup(bucket, prefix, batch, config_dict)

    create_batch_jobs.create_batch_jobs_7(project_name, pipeline_name, platelist, batch)

    run_DCP.run_cluster(bucket, prefix, batch, len(platelist)*384, config_dict)

    run_DCP.setup_monitor(bucket, prefix, config_dict)
