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

def lambda_handler(event, lambda_context):
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

    spot_request_id_list = []
    instance_id_list = []
    for msg in queue_messages:
        spot_request_id = msg["Body"].split(" ")[1]
        spot_request_id_list.append(spot_request_id)
        instance_id = msg["Body"].split(" ")[0]
        instance_id_list.append(instance_id)

    # If more than 2 nameless machines killed in the same spot fleet
    countdict = Counter(spot_request_id_list)
    for spot_request_id in countdict:
        if countdict[spot_request_id] > 2:
            activeinstances = ec2.describe_spot_fleet_instances(
                SpotFleetRequestId=spot_request_id
            )
            has_named_instance = False
            for active in activeinstances["ActiveInstances"]:
                instance_id = active["InstanceId"]
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
                    msg = f'Spot fleet request {spot_request_id} in {bucket} was cancelled by Kill_Nameless_Machines.'
                    sns.publish(TopicArn=sns_arn, Message=msg)
                except:
                    print ('Failed at email notification of cancelled spot fleet request')

    print(f"{instance_id_list} were nameless for too long after launch. Terminating.")
    for instance_id in instance_id_list:
        try:
            ec2.terminate_instances(InstanceIds=[instance_id])
        except:
            continue
    sqs.purge_queue(QueueUrl=queue_url)

    if len(instance_id_list) > 0:
        try:
            msg = f'{len(instance_id_list)} instances terminated in {bucket} by Kill_Nameless_Machines'
            sns.publish(TopicArn=sns_arn, Message=msg)
        except:
            print ('Failed at email notification of killed instance')
