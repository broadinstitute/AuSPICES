import boto3
from datetime import datetime, timezone, timedelta
from dateutil.tz import tzutc
import time

CloudWatch = boto3.client("cloudwatch")
CloudWatchLogs = boto3.client("logs")
ec2 = boto3.client('ec2')

# from https://aws.amazon.com/blogs/mt/delete-empty-cloudwatch-log-streams/
def get_log_groups(next_token=None):
    log_group_request = {
        'limit': 50  # Maximum
    }
    if next_token:
        log_group_request['nextToken'] = next_token
    log_groups_response = CloudWatchLogs.describe_log_groups(**log_group_request)
    if log_groups_response:
        for log_group in log_groups_response['logGroups']:
            yield log_group
        if 'nextToken' in log_groups_response:
            yield from get_log_groups(log_groups_response['nextToken'])

def lambda_handler(event, lambda_context):
    # Kill Old Dashboards
    dashboard_list = CloudWatch.list_dashboards()

    todel_list = []
    for entry in dashboard_list["DashboardEntries"]:
        if "keep" not in entry["DashboardName"].lower():
            age = datetime.now(timezone.utc) - entry["LastModified"]
            if age > timedelta(days=3):
                todel_list.append(entry["DashboardName"])
    if len(todel_list) > 0:
        CloudWatch.delete_dashboards(DashboardNames=todel_list)

    # Kill Old Log Groups
    for log_group in get_log_groups():
        if 'retentionInDays' not in log_group:
            print(f"Log group {log_group['logGroupName']} has infinite retention, skipping")
            continue
        if log_group['storedBytes']==0:
            CloudWatchLogs.delete_log_group(logGroupName=log_group['logGroupName'])
            print(f"Deleted empty log {log_group['logGroupName']}")
    
    # Kill Old Alarms
    ## With great power comes great responsibility. Enable at your own risk.
    """
    alarms = CloudWatch.describe_alarms(AlarmTypes=['MetricAlarm'],StateValue='INSUFFICIENT_DATA')
    while True:
        for eachalarm in alarms['MetricAlarms']:
            age = datetime.now(timezone.utc) - eachalarm['StateUpdatedTimestamp']
            if age > timedelta(days=1):
                if eachalarm['StateValue'] == 'INSUFFICIENT_DATA':
                    CloudWatch.delete_alarms(AlarmNames = [eachalarm['AlarmName']])
                    time.sleep(1) #avoid throttling
        token = alarms['NextToken']
        alarms = CloudWatch.describe_alarms(AlarmTypes=['MetricAlarm'],StateValue='INSUFFICIENT_DATA',NextToken=token)
    """

    # Kill Useless Alarms
    ## Part 1: let's document all the instances we know about, in any state
    instance_list = []
    alarm_count = 0
    deleted_alarm_count = 0
    
    instances = ec2.describe_instances()
    instances_reservations = instances['Reservations']
    all_instances=False
    while all_instances==False:
        for eachres in instances_reservations:
            for eachinst in eachres['Instances']:
                instance_list.append(eachinst['InstanceId'])
        if 'NextToken' in instances.keys():
            token = instances['NextToken']
            instances = ec2.describe_instances(NextToken=token)
            instances_reservations = instances['Reservations']
            all_instances=False
        else:
            all_instances=True
    print(f"{len(instance_list)} instances found (in any state)")

    ## Part 2: Let's look at all the MetricAlarms we have that are specifically monitoring an instance's functioning in some way
    ## Any alarm that monitors an instances that EC2 doesn't have a record of anymore should be deleted
    alarms = CloudWatch.describe_alarms(AlarmTypes=['MetricAlarm'])
    all_alarms = False
    while all_alarms == False:
        for eachalarm in alarms['MetricAlarms']:
            alarm_count += 1
            for eachdim in eachalarm['Dimensions']:
                if eachdim['Name'] == 'InstanceId':
                    if eachdim['Value'] not in instance_list:
                        deleted_alarm_count += 1
                        print(f"{eachalarm['AlarmName']} belongs to an instance that no longer exists. Deleting")
                        CloudWatch.delete_alarms(AlarmNames = [eachalarm['AlarmName']])
                        time.sleep(1) #avoid throttling
                    else:
                        print(f"Not deleting {eachalarm['AlarmName']}, belongs to an instance that still exists")
                else:
                    print(f"Not deleting {eachalarm['AlarmName']}, not an instance alarm")
        if 'NextToken' in alarms.keys():
            token = alarms['NextToken']
            alarms = CloudWatch.describe_alarms(AlarmTypes=['MetricAlarm'],NextToken=token)
            all_alarms=False
        else:
            all_alarms=True
    print(f"{deleted_alarm_count} alarms deleted (of {alarm_count} total alarms)") 