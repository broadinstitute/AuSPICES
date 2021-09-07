import json
import os
import sys
import boto3

sys.path.append("/opt/jump-cellpainting-lambda")

import run_DCP
import create_batch_jobs
import helpful_functions

s3 = boto3.client("s3")

# Step information
metadata_file_name = "/tmp/metadata.json"


def lambda_handler(event, lambda_context):

    monitorInfo = loadConfig(monitor_name)
    monitorcluster = monitorInfo["MONITOR_ECS_CLUSTER"]
    monitorapp = monitorInfo["MONITOR_APP_NAME"]
    fleetId = monitorInfo["MONITOR_FLEET_ID"]
    queueId = monitorInfo["MONITOR_QUEUE_NAME"]

    ec2 = boto3.client("ec2")
    cloud = boto3.client("cloudwatch")
    # Step 1: Create job and count messages periodically
    queue = JobQueue(name=queueId)
    while queue.pendingLoad():
        # Once an hour (except at midnight) check for terminated machines and delete their alarms.
        # This is slooooooow, which is why we don't just do it at the end
        curtime = datetime.datetime.now().strftime("%H%M")
        if curtime[-2:] == "00":
            if curtime[:2] != "00":
                killdeadAlarms(fleetId, monitorapp, ec2, cloud)
        # Once every 10 minutes, check if all jobs are in process, and if so scale the spot fleet size to match
        # the number of jobs still in process WITHOUT force terminating them.
        # This can help keep costs down if, for example, you start up 100+ machines to run a large job, and
        # 1-10 jobs with errors are keeping it rattling around for hours.
        if curtime[-1:] == "9":
            downscaleSpotFleet(queue, fleetId, ec2)
        time.sleep(MONITOR_TIME)

    # Step 2: When no messages are pending, stop service
    # Reload the monitor info, because for long jobs new fleets may have been started, etc
    monitorInfo = loadConfig(monitor_name)
    monitorcluster = monitorInfo["MONITOR_ECS_CLUSTER"]
    monitorapp = monitorInfo["MONITOR_APP_NAME"]
    fleetId = monitorInfo["MONITOR_FLEET_ID"]
    queueId = monitorInfo["MONITOR_QUEUE_NAME"]
    bucketId = monitorInfo["MONITOR_BUCKET_NAME"]
    loggroupId = monitorInfo["MONITOR_LOG_GROUP_NAME"]
    starttime = monitorInfo["MONITOR_START_TIME"]

    ecs = boto3.client("ecs")
    ecs.update_service(
        cluster=monitorcluster, service=monitorapp + "Service", desiredCount=0
    )
    print("Service has been downscaled")

    # Step3: Delete the alarms from active machines and machines that have died since the last sweep
    # This is in a try loop, because while it is important, we don't want to not stop the spot fleet
    try:
        result = ec2.describe_spot_fleet_instances(SpotFleetRequestId=fleetId)
        instancelist = result["ActiveInstances"]
        while len(instancelist) > 0:
            to_del = instancelist[:100]
            del_alarms = [monitorapp + "_" + x["InstanceId"] for x in to_del]
            cloud.delete_alarms(AlarmNames=del_alarms)
            time.sleep(10)
            instancelist = instancelist[100:]
        killdeadAlarms(fleetId, monitorapp)
    except:
        pass

    # Step 4: Read spot fleet id and terminate all EC2 instances
    print("Shutting down spot fleet", fleetId)
    ec2.cancel_spot_fleet_requests(
        SpotFleetRequestIds=[fleetId], TerminateInstances=True
    )
    print("Job done.")

    # Step 5. Release other resources
    # Remove SQS queue, ECS Task Definition, ECS Service
    ECS_TASK_NAME = monitorapp + "Task"
    ECS_SERVICE_NAME = monitorapp + "Service"
    print("Deleting existing queue.")
    removequeue(queueId)
    print("Deleting service")
    ecs.delete_service(cluster=monitorcluster, service=ECS_SERVICE_NAME)
    print("De-registering task")
    deregistertask(ECS_TASK_NAME, ecs)
    print("Removing cluster if it's not the default and not otherwise in use")
    removeClusterIfUnused(monitorcluster, ecs)

    # Step 6: Export the logs to S3
    logs = boto3.client("logs")

    print("Transfer of CellProfiler logs to S3 initiated")
    export_logs(logs, loggroupId, starttime, bucketId)

    print("Transfer of per-instance to S3 initiated")
    export_logs(logs, loggroupId + "_perInstance", starttime, bucketId)

    print("All export tasks done")


    # Send success notification
    aws stepfunctions send-task-success --task-token $token
