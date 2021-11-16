import boto3
import time

ec2 = boto3.client("ec2")

def check_if_named(instance_id):
    instance_info = ec2.describe_instances(InstanceIds=[instance_id])
    instances = instance_info['Reservations'][0]['Instances']
    for instance in instances:
        if instance['InstanceId'] == instance_id:
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        print (f"{instance_id} has a name - {instance_name}.")
                        return True
            else:
                print (f"{instance_id} does not have a name.")
                return False

def lambda_handler(event, lambda_context):
    instance_id = event['detail']['instance-id']
    time.sleep(60) # Wait 1 minute

    named = check_if_named(instance_id)
    if named:
        return
    else:
        print ("Checking again in 2 minutes.")
        time.sleep(60*2) # Wait 2 minutes

    named = check_if_named(instance_id)
    if named:
        return
    else:
        print ("Checking again in 10 minutes.")
        time.sleep(60*10) # Wait 10 minutes

    named = check_if_named(instance_id)
    if named:
        return
    else:
        print (f"{instance_id} is nameless for too long after launch. Terminating.")
        ec2.terminate_instances(InstanceIds=[instance_id])
