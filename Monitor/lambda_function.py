import boto3
import datetime

ecs = boto3.client("ecs")
ec2 = boto3.client("ec2")
cloudwatch = boto3.client("cloudwatch")


def killdeadAlarms(fleetId, monitorapp):
    checkdates = [
        datetime.datetime.now().strftime("%Y-%m-%d"),
        (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
    ]
    todel = []
    for eachdate in checkdates:
        datedead = ec2.describe_spot_fleet_request_history(
            SpotFleetRequestId=fleetId, StartTime=eachdate
        )
        for eachevent in datedead["HistoryRecords"]:
            if eachevent["EventType"] == "instanceChange":
                if eachevent["EventInformation"]["EventSubType"] == "terminated":
                    todel.append(eachevent["EventInformation"]["InstanceId"])
    # used to be a for loop check formatting correct for delete_alarms
    # cmd='aws cloudwatch delete-alarms --alarm-name '+monitorapp+'_'+eachmachine
    cloudwatch.delete_alarms(AlarmNames=todel)
    print("Old alarms deleted")


def seeIfLogExportIsDone(logExportId):
    while True:
        result = cloudwatch.describe_export_tasks(taskId=logExportId)
        if result["exportTasks"][0]["status"]["code"] != "PENDING":
            if result["exportTasks"][0]["status"]["code"] != "RUNNING":
                print(result["exportTasks"][0]["status"]["code"])
                break
                time.sleep(30)


def downscaleSpotFleet(queue, spotFleetID):
    visible, nonvisible = queue.returnLoad()
    status = ec2.describe_spot_fleet_instances(SpotFleetRequestId=spotFleetID)
    if nonvisible < len(status["ActiveInstances"]):
        result = ec2.modify_spot_fleet_request(
            ExcessCapacityTerminationPolicy="noTermination",
            TargetCapacity=str(nonvisible),
            SpotFleetRequestId=spotFleetID,
        )


def lambda_handler(event, lambda_context):
    monitorInfo = loadConfig(sys.argv[2])
    monitorcluster = monitorInfo["MONITOR_ECS_CLUSTER"]
    monitorapp = monitorInfo["MONITOR_APP_NAME"]
    fleetId = monitorInfo["MONITOR_FLEET_ID"]
    queueId = monitorInfo["MONITOR_QUEUE_NAME"]
    bucketId = monitorInfo["MONITOR_BUCKET_NAME"]
    loggroupId = monitorInfo["MONITOR_LOG_GROUP_NAME"]
    starttime = monitorInfo["MONITOR_START_TIME"]

    # if message is visible == 0, downscale machines
    killdeadAlarms(fleetId, monitorapp)
    downscaleSpotFleet(queue, fleetId)
    return

    # if message in progress == 0, cleanup

    ecs.update_service(
        cluster=monitorcluster, service=f"{monitorapp}Service", desiredCount=0,
    )
    print("Service has been downscaled")

    # Delete the alarms from active machines and machines that have died.
    active_dictionary = ec2.describe_spot_fleet_instances(SpotFleetRequestId=fleetId)
    # active_instances needs to be list of alarms
    cloudwatch.delete_alarms(AlarmNames=active_instances)
    killdeadAlarms(fleetId, monitorapp)

    # Read spot fleet id and terminate all EC2 instances
    ec2.cancel_spot_fleet_requests(
        DryRun=False, SpotFleetRequestIds=[fleetId], TerminateInstances=True
    )
    print("Fleet shut down.")

    # Remove SQS queue, ECS Task Definition, ECS Service
    ECS_TASK_NAME = monitorapp + "Task"
    ECS_SERVICE_NAME = monitorapp + "Service"
    print("Deleting existing queue.")
    removequeue(queueId)
    print("Deleting service")
    ecs.delete_service(cluster=monitorcluster, service=ECS_SERVICE_NAME)
    print("De-registering task")
    taskArns = ecs.list_task_definitions()
    for task in taskArns["taskDefinitionArns"]:
        fulltaskname = eachtask.split("/")[-1]
        ecs.deregister_task_definition(taskDefinition=fulltaskname)

    print("Removing cluster if it's not the default and not otherwise in use")
    if clusterName != "default":
        result = ecs.describe_clusters(clusters=[clusterName])
    if (
        sum(
            [
                result["clusters"][0]["pendingTasksCount"],
                result["clusters"][0]["runningTasksCount"],
                result["clusters"][0]["activeServicesCount"],
            ]
        )
        == 0
    ):
        ecs.delete_cluster(cluster=clusterName)

    # Step 6: Export the logs to S3
    cloudwatch.create_export_task(
        taskName=loggroupId,
        logGroupName=loggroupId,
        fromTime=starttime,
        to=%(time.time()*1000),
        destination=bucketId,
        destinationPrefix=f"exportedlogs/{loggroupId}",
    )
    print("Log transfer 1 to S3 initiated")
    seeIfLogExportIsDone(result["taskId"])
    cloudwatch.create_export_task(
        taskName=f"{loggroupId}_perInstance",
        logGroupName=f"{loggroupId}_perInstance",
        fromTime=starttime,
        to=%(time.time()*1000),
        destination=bucketId,
        destinationPrefix=f"exportedlogs/{loggroupId}",
    )
    result = getAWSJsonOutput(cmd)
    print("Log transfer 2 to S3 initiated")
    seeIfLogExportIsDone(result["taskId"])
    print("All export tasks done")

    #Remove alarms that triggered monitor
