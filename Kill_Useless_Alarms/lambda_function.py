import boto3
import time

def lambda_handler(event, lambda_context):
    
    ## Part 1: let's document all the instances we know about, in any state
    instance_list = []
    alarm_count = 0
    deleted_alarm_count = 0
    ec2 = boto3.client('ec2')
    cw = boto3.client('cloudwatch')
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
    alarms = cw.describe_alarms(AlarmTypes=['MetricAlarm'])
    all_alarms = False
    while all_alarms == False:
        for eachalarm in alarms['MetricAlarms']:
            alarm_count += 1
            for eachdim in eachalarm['Dimensions']:
                if eachdim['Name'] == 'InstanceId':
                    if eachdim['Value'] not in instance_list:
                        deleted_alarm_count += 1
                        print(f"{eachalarm['AlarmName']} belongs to an instance that no longer exists. Deleting")
                        cw.delete_alarms(AlarmNames = [eachalarm['AlarmName']])
                        time.sleep(1) #avoid throttling
                    else:
                        print(f"Not deleting {eachalarm['AlarmName']}, belongs to an instance that still exists")
                else:
                    print(f"Not deleting {eachalarm['AlarmName']}, not an instance alarm")
        if 'NextToken' in alarms.keys():
            token = alarms['NextToken']
            alarms = cw.describe_alarms(AlarmTypes=['MetricAlarm'],NextToken=token)
            all_alarms=False
        else:
            all_alarms=True
    print(f"{deleted_alarm_count} alarms deleted (of {alarm_count} total alarms)")