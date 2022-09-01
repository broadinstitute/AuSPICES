Kill_Useless_Alarms is a lambda function that removes CloudWatch Alarms related to instances that no longer exist.

Kill_Useless_Alarms checks for defunct CloudWatch Alarms every day.
Instances that were recently killed (such that they exist in state "Terminated" as opposed to don't exist at all) will be deleted the following day.

# Setup Lambda Function

*Create a new lambda functions.*

## Function Kill_Useless_Alarms

### Basic information
**Function name**:`Kill_Useless_Alarms`  
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
**Existing rules:** every_day

#### Asynchronous invocation:
**Retry attempts**: 0

### Configure the lambda function code
* Copy Kill_Useless_Alarms/`lambda_function.py` into the code area.
* Deploy.

# Setup EventBridge Rules

*Create a new rule in Amazon EventBridge that will trigger the lambda function. If you are using both Kill_Old_Dashboards and Kill_Useless_Alarms, they can share the same EventBridge rule.*

### Rule detail
**Name**: every_day
**Rule type**: Schedule

### Schedule pattern:
**A regular rate**: 1 Days

### Target 1:
**Target type**: AWS service
**Select a target**: Lambda function
**Function**: Kill_Useless_Alarms
