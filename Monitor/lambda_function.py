import boto3
import datetime
import botocore
import json

s3 = boto3.client("s3")
ecs = boto3.client("ecs")
ec2 = boto3.client("ec2")
cloudwatch = boto3.client("cloudwatch")
sqs = boto3.client("sqs")

bucket = "BUCKET_NAME"


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
    queueId = event["Trigger"]["Dimensions"][0]["value"]
    project = queueId.rsplit("_", 1)[0]

    # Download monitor file
    monitor_file_name = f"{queueId.split('Queue')[0]}SpotFleetRequestId.json"
    monitor_local_name = f"/tmp/{monitor_file_name}"
    monitor_on_bucket_name = (
        f"projects/{project}/workspace/monitors/stepfunctions/{monitor_file_name}"
    )

    with open(monitor_local_name, "wb") as f:
        try:
            s3.download_fileobj(bucket, monitor_on_bucket_name, f)
        except botocore.exceptions.ClientError as error:
            print("Error retrieving monitor file.")
            return
    with open(monitor_local_name, "r") as input:
        monitorInfo = json.load(input)

    monitorcluster = monitorInfo["MONITOR_ECS_CLUSTER"]
    monitorapp = monitorInfo["MONITOR_APP_NAME"]
    fleetId = monitorInfo["MONITOR_FLEET_ID"]
    loggroupId = monitorInfo["MONITOR_LOG_GROUP_NAME"]
    starttime = monitorInfo["MONITOR_START_TIME"]

    # If no visible messages, downscale machines
    if event["Trigger"]["MetricName"] == "ApproximateNumberOfMessagesVisible":
        killdeadAlarms(fleetId, monitorapp)
        downscaleSpotFleet(queueId, fleetId)

    # If no messages in progress, cleanup
    if event["Trigger"]["MetricName"] == "ApproximateNumberOfMessagesNotVisible":
        ecs.update_service(
            cluster=monitorcluster, service=f"{monitorapp}Service", desiredCount=0,
        )
        print("Service has been downscaled")

        # Delete the alarms from active machines and machines that have died.
        active_dictionary = ec2.describe_spot_fleet_instances(
            SpotFleetRequestId=fleetId
        )
        # active_instances needs to be list of alarms
        cloudwatch.delete_alarms(AlarmNames=active_instances)
        killdeadAlarms(fleetId, monitorapp)

        # Read spot fleet id and terminate all EC2 instances
        ec2.cancel_spot_fleet_requests(
            SpotFleetRequestIds=[fleetId], TerminateInstances=True
        )
        print("Fleet shut down.")

        # Remove SQS queue, ECS Task Definition, ECS Service
        ECS_TASK_NAME = monitorapp + "Task"
        ECS_SERVICE_NAME = monitorapp + "Service"

        print("Deleting existing queue.")
        queueoutput=sqs.list_queues(QueueNamePrefix=queueId)
        try:
            if len(queueoutput["QueueUrls"])==1:
                queueUrl=queueoutput["QueueUrls"][0]
            else: #In case we have "AnalysisQueue" and "AnalysisQueue1" and only want to delete the first of those
                for eachUrl in queueoutput["QueueUrls"]:
                    if eachUrl.split('/')[-1] == queueName:
                        queueUrl=eachUrl
            sqs.delete_queue(QueueUrl=queueUrl)
        except KeyError:
            print("Can't find queue to delete.")

        print("Deleting service")
        try:
            ecs.delete_service(cluster=monitorcluster, service=ECS_SERVICE_NAME)
        except:
            print ("Couldn't delete service.")

        print("De-registering task")
        taskArns = ecs.list_task_definitions()
        for eachtask in taskArns["taskDefinitionArns"]:
            fulltaskname = eachtask.split("/")[-1]
            ecs.deregister_task_definition(taskDefinition=fulltaskname)

        print("Removing cluster if it's not the default and not otherwise in use")
        if monitorcluster != "default":
            result = ecs.describe_clusters(clusters=[monitorcluster])
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
            ecs.delete_cluster(cluster=monitorcluster)

        # Remove alarms that triggered monitor
        print ("Removing alarms that triggered Monitor")
        cloudwatch.delete_alarms(
            AlarmNames=[
                "ApproximateNumberOfMessagesVisibleisZero",
                "ApproximateNumberOfMessagesNotVisibleisZero",
            ]
        )
