import boto3
import time
from collections import Counter

ec2 = boto3.client("ec2")
sqs = boto3.client("sqs")
sns = boto3.client("sns")

# Set for each implementation of function
queue_url = "https://sqs.us-east-1.amazonaws.com/500910614606/Killed_Machines_List"
bucket = 'jump-cellpainting'
sns_arn = 'arn:aws:sns:us-east-1:500910614606:Kill_Nameless_Machines_Email_Notification'


def check_if_named_or_spot(instance_id):
    instance = ec2.describe_instances(InstanceIds=[instance_id])
    if "Tags" in instance["Reservations"][0]["Instances"][0]:
        for tag in instance["Reservations"][0]["Instances"][0]["Tags"]:
            if "Name" in tag["Key"]:
                instance_name = tag["Value"]
                print(f"{instance_id} has a name - {instance_name}.")
                named = True
            else:
                print(f"{instance_id} does not have a name.")
                named = False

            if "ec2spot" in tag["Key"]:
                spot_request_id = tag["Value"]
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

            # Must iterate to get all messages in queue
            queue_messages = []
            while True:
                message_set = sqs.receive_message(
                    QueueUrl=queue_url,
                    AttributeNames=["SentTimestamp"],
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                )
                try:
                    queue_messages.extend(message_set["Messages"])
                except:
                    break

            fleetlist = []
            for msg in queue_messages:
                # List nameless spot fleet machines killed in last hour
                if (
                    time.time() - int(msg["Attributes"]["SentTimestamp"]) / 1000
                    < 60 * 60
                ):
                    fleet = msg["Body"].split(" ")[1]
                    fleetlist.append(fleet)
                # Clean up while we're at it: Delete messages that are over a day old
                if (
                    time.time() - int(msg["Attributes"]["SentTimestamp"]) / 1000
                    > 60 * 60 * 24
                ):
                    sqs.delete_message(
                        QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"]
                    )
            # If more than 2 nameless machines killed in last hour in spot fleet
            countdict = Counter(fleetlist)
            if countdict[spot_request_id] > 2:
                activeinstances = ec2.describe_spot_fleet_instances(
                    SpotFleetRequestId=spot_request_id
                )
                has_named_instance = False
                for active in activeinstances["ActiveInstances"]:
                    instance_id = instance["InstanceId"]
                    instance = ec2.describe_instances(InstanceIds=[instance_id])
                    # Check if any machines in spot fleet are named
                    for tag in instance["Reservations"][0]["Instances"][0]["Tags"]:
                        if "Name" in tag["Key"]:
                            has_named_instance = True
                # If no machines in spot fleet are named, kill it
                if not has_named_instance:
                    print(
                        f"{spot_request_id} has no named instances. Cancelling spot request."
                    )
                    ec2.cancel_spot_fleet_requests(
                        SpotFleetRequestIds=[spot_request_id], TerminateInstances=True
                    )

                    try:
                        msg = f'Kill_Nameless_Machines just cancelled spot fleet request {spot_request_id} in {bucket}'
                        sns.publish(TopicArn=sns_arn, Message=msg)
                    except:
                        print ('Failed at email notificaiton of cancelled spot fleet request')

        print(f"{instance_id} is nameless for too long after launch. Terminating.")
        ec2.terminate_instances(InstanceIds=[instance_id])

        try:
            msg = f'Kill_Nameless_Machines just terminated {instance_id} in {bucket}'
            sns.publish(TopicArn=sns_arn, Message=msg)
        except:
            print ('Failed at email notificaiton of killed instance')
