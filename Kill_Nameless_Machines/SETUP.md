Kill_Nameless_Machines is a two-part lambda function that checks both on-demand and spot EC2 instances and kills them if they aren't named within 15 minutes.

ID_Nameless_Machines is triggered every time an EC2 instance is turned on (i.e. instance state changes to `running`).
It checks to see if the instance has a name.
If not, it will wait 2 minutes and check again, and then 10 minutes and try again.
If the machine is an on-demand machine and does not have a name after 3 checks and ~15 minutes, it terminates the machine.
If the machine is part of a spot fleet and does not have a name after 3 checks and ~15 minutes, it sends the machine info to Killed_Machines_List, an SQS Queue.

Kill_Nameless_Fleets checks the Killed_Machines_List every 10 minutes.
It kills every machine in the list.
If two nameless machines from the same spot fleet request are in the list, it will check to see if that spot fleet request has any named machines.
If the spot request has no named machines, it will cancel the spot fleet request.

Any time that Kill_Nameless_Machines kills a machine or cancels a spot fleet request, it sends an email with notification of that action.


# Setup Killed_Machines_List Queue

*Create a new SQS queue that will keep track of killed instances.*

## Create Queue
Standard  
**Name**: Killed_Machines_List

### Configuration
**Visibility timeout**: 5 minutes

Copy the URL for the Killed_Machines_List SQS queue so that you can paste it into your lambda function (e.g. https://sqs.us-east-1.amazonaws.com/123456789123/Killed_Machines_List)

# Setup Email Notifications

*Create a new SNS topic and subscription for email notifications.*

Create an SNS topic  
**Topic Name**: Kill_Nameless_Machines_Email_Notification  
**Type**: Standard

Create an SNS subscription  
**Topic ARN**: arn:aws:sns:us-east-1:123456789123:Kill_Nameless_Machines_Email_Notification  
**Protocol**: Email  
**Endpoint**: email_address_you_want_to_notify@yourdomain.com

Your endpoint email address will get an automated notification from AWS requesting confirmation.
Confirm it.

Copy the Topic Arn for the SNS topic so that you can paste it into your lambda function (e.g. arn:aws:sns:us-east-1:123456789123:Kill_Nameless_Machines_Email_Notification)

# Setup Lambda Functions

*Create two new lambda functions.*

## Function 1: ID_Nameless_Machines

### Basic information
**Function name**:`ID_Nameless_Machines`  
**Runtime**: Python 3.8 or Python 3.9  
**Permissions**: **Execution role**: Use an existing role:  `LambdaFullAccess`

### Configuration
#### General configuration:  
**Timeout**: 15 min  

#### Triggers:
Trigger should auto-populate with the EventBridge event you create in the next step.
If it does not:  
**Trigger Configuration**: EventBridge  
**Rule**: Existing rules
**Existing rules:** launch_ec2_instance

#### Asynchronous invocation:
**Retry attempts**: 0

### Configure the lambda function code
* Copy Kill_Nameless_Machines/ID_Nameless_Machines/`lambda_function.py` into the code area.
* Edit `queue_url = 'https://sqs.region.amazonaws.com/123456789123/Killed_Machines_List'` to match your queue.
* Edit `bucket = 'yourbucket'` to match your bucket.
* Edit `sns_arn = 'arn:aws:sns:region:123456789123:Kill_Nameless_Machines_Email_Notification'` to match your Topic ARN.
* Deploy.

## Function 2: Kill_Nameless_Fleets

### Basic information
**Function name**:`Kill_Nameless_Fleets`  
**Runtime**: Python 3.8 or Python 3.9  
**Permissions**: **Execution role**: Use an existing role:  `LambdaFullAccess`

### Configuration
#### General configuration:  
**Timeout**: 15 min  

#### Triggers:
Trigger should auto-populate with the EventBridge event you create in the next step.
If it does not:  
**Trigger Configuration**: EventBridge  
**Rule**: Existing rules
**Existing rules:** every_10_minutes

#### Asynchronous invocation:
**Retry attempts**: 0

### Configure the lambda function code
* Copy Kill_Nameless_Machines/Kill_Nameless_Fleets/`lambda_function.py` into the code area.
* Edit `queue_url = 'https://sqs.region.amazonaws.com/123456789123/Killed_Machines_List'` to match your queue.
* Edit `bucket = 'yourbucket'` to match your bucket.
* Edit `sns_arn = 'arn:aws:sns:region:123456789123:Kill_Nameless_Machines_Email_Notification'` to match your Topic ARN.
* Deploy.

# Setup EventBridge Rules

*Create two new rules in Amazon EventBridge that will trigger the lambda functions.*

## Rule 1:

### Rule detail:
**Name**: launch_ec2_instance
**Event bus**: default
Enable the rule on the selected event bus.
**Rule type**: Rule with an event pattern

### Event source:
AWS events or EventBridge partner events

### Event pattern:
**Event source**: AWS services
**AWS Service**: EC2  
**Event type**: EC2 Instance State-change Notification  
**Specific state(s)**: running  
Any instance  

### Select targets:
**Target**: Lambda function  
**Function**: ID_Nameless_Machines

## Rule 2:

### Rule detail:
**Name**: every_10_minutes
**Event bus**: default
Enable the rule on the selected event bus.
**Rule type**: Schedule

### Schedule pattern:
**A regular rate**:  10 minutes

### Select event bus:
AWS default event bus  
Enable the rule on the selected event bus.

### Select targets:
**Target type**: AWS service
**Select a target**: Lambda function
**Function**: Kill_Nameless_Fleets
