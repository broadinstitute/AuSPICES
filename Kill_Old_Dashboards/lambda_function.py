import boto3
from datetime import datetime, timezone, timedelta
from dateutil.tz import tzutc

CloudWatch = boto3.client("cloudwatch")


def lambda_handler(event, lambda_context):
    dashboard_list = CloudWatch.list_dashboards()

    todel_list = []
    for entry in dashboard_list["DashboardEntries"]:
        if "keep" not in entry["DashboardName"].lower():
            age = datetime.now(timezone.utc) - entry["LastModified"]
            if age > timedelta(days=3):
                todel_list.append(entry["DashboardName"])

    CloudWatch.delete_dashboards(DashboardNames=todel_list)
