Kill_Nameless_Machines is a lambda function that is triggered every time an EC2 instance is turned on (i.e. instance state changes to `running`).
It checks to see if the instance has a name.
If not, it will wait 2 minutes and check again, and then 10 minutes and try again.
If the machine does not have a name after 3 checks and ~15 minutes, it terminates the machine.

Kill_Nameless_Machines will handle on-demand EC2 instances or instances created through a spot request.
If two nameless machines from the same spot fleet request are killed within an hour, it will check to see if that spot fleet request has any named machines.
If the spot request has no named machines, it will cancel the spot fleet request.


# Setup Killed_Machines_List Queue

Create a new SQS queue that will keep track of killed instances.

## Create queue
Standard
**Name**:Killed_Machines_List

###Configuration
**Visibility timeout**: 5 minutes

Copy the URL for the Killed_Machines_List SQS queue (e.g. https://sqs.us-east-1.amazonaws.com/############/Killed_Machines_List)

# Setup Lambda Function

Create a new lambda function.

### Basic information
**Function name**:`Kill_Nameless_Machines`  
**Runtime**: Python 3.8 or Python 3.9  
**Permissions**: **Execution role**: Use an existing role:  `LambdaFullAccess`

### Configuration
#### General configuration:  
**Timeout**: 15 min  
#### Triggers:
(Triggers will auto-populate with the EventBridge event you create in the next step.)
#### Asynchronous invocation:
**Retry attempts**: 0

Copy Kill_Nameless_Machines/`lambda_function.py` into the code area.
Edit `queue_url = https://sqs.us-east-1.amazonaws.com/123456789123/Killed_Machines_List` to match your queue.
Deploy.


# Setup EventBridge

Create a new rule in Amazon EventBridge that will trigger the lambda function.

### Name and description:
**Name**: launch_ec2_instance

### Define pattern:
Event pattern  
**Event matching pattern**: Pre-defined pattern by service  
**Service provider**: AWS  
**Service name**: EC2  
**Event type**: EC2 Instance State-change Notification  
**Specific state(s)**: running  
Any instance  

### Select event bus:
AWS default event bus  
Enable the rule on the selected event bus.

### Select targets:
**Target**: Lambda function  
**Function**: Kill_Nameless_Machines
