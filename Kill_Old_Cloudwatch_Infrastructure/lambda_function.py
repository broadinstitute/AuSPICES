import boto3
from datetime import datetime, timezone, timedelta
from dateutil.tz import tzutc

CloudWatch = boto3.client("cloudwatch")
CloudWatchLogs = boto3.client("logs")

def lambda_handler(event, lambda_context):
    # Kill Old Dashboards
    dashboard_list = CloudWatch.list_dashboards()

    todel_list = []
    for entry in dashboard_list["DashboardEntries"]:
        if "keep" not in entry["DashboardName"].lower():
            age = datetime.now(timezone.utc) - entry["LastModified"]
            if age > timedelta(days=3):
                todel_list.append(entry["DashboardName"])

    CloudWatch.delete_dashboards(DashboardNames=todel_list)

    # Kill Old Log Groups
    log_groups = CloudWatchLogs.describe_log_groups()
    for group in log_groups['logGroups']:
        streams = CloudWatchLogs.describe_log_streams(logGroupName=group['logGroupName'])
        if streams['logStreams'] == []:
            CloudWatchLogs.delete_log_group(logGroupName=group['logGroupName'])
            print (f"Deleted empty log group {group['logGroupName']}")