import boto3

def lambda_handler(event, lambda_context):
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

alarm_killer()