import boto3
import time
from collections import Counter

ec2 = boto3.client("ec2")
sqs = boto3.client("sqs")
sns = boto3.client("sns")

# Set for each implementation of function
queue_url = 'https://sqs.region.amazonaws.com/123456789123/Killed_Machines_List'
bucket = 'bucket-name'
sns_arn = 'arn:aws:sns:region:123456789123:Kill_Nameless_Machines_Email_Notification'


def check_if_named_or_spot(instance_id):
    instance = ec2.describe_instances(InstanceIds=[instance_id])
    if instance["Reservations"][0]["Instances"][0]["State"]["Name"] == 'terminated':
        print (f"{instance_id} already killed")
        return True, False
        
    if "Tags" in instance["Reservations"][0]["Instances"][0]:
        tagkeys = []
        for tag in instance["Reservations"][0]["Instances"][0]["Tags"]:
            tagkeys.append(tag['Key'])
            if tag['Key'] == 'Name':
                instance_name = tag["Value"]
            if tag['Key'] == 'aws:ec2spot:fleet-request-id':
                spot_request_id = tag["Value"]

        if "Name" in tagkeys:
            print(f"{instance_id} has a name - {instance_name}.")
            named = True
        else:
            print(f"{instance_id} does not have a name.")
            named = False

        if 'aws:ec2spot:fleet-request-id' in tagkeys:
            print(f"{instance_id} is in spot fleet {spot_request_id}.")
        else:
            spot_request_id = False
            print(f"{instance_id} is not in a spot fleet.")
    else:
        print(f"{instance_id} does not have a name and is not in a spot fleet.")
        named = False
        spot_request_id = False
    return named, spot_request_id


def lambda_handler(event, lambda_context):
    instance_id = event["detail"]["instance-id"]
    time.sleep(60)  # Wait 1 minute

    named, spot_request_id = check_if_named_or_spot(instance_id)
    if named:
        return
    else:
        print("Checking again in 2 minutes.")
        time.sleep(60 * 2)  # Wait 2 minutes

    named, spot_request_id = check_if_named_or_spot(instance_id)
    if named:
        return
    else:
        print("Checking again in 10 minutes.")
        time.sleep(60 * 10)  # Wait 10 minutes

    named, spot_request_id = check_if_named_or_spot(instance_id)
    if named:
        return
    else:
        if spot_request_id:
            # Add nameless instance to sqs queue
            message = f"{instance_id} {spot_request_id}"
            sqs.send_message(QueueUrl=queue_url, MessageBody=message)

        else:
            print(f"{instance_id} is nameless for too long after launch. Terminating.")
            ec2.terminate_instances(InstanceIds=[instance_id])

            try:
                msg = f'On-Demand {instance_id} in {bucket} terminated by Kill_Nameless_Machines'
                sns.publish(TopicArn=sns_arn, Message=msg)
            except:
                print ('Failed at email notification of killed instance')
