Kill_Old_Cloudwatch_Infrastructure is a lambda function that removes old CloudWatch Dashboards, Log Groups and Alarms.

Kill_Old_Cloudwatch_Infrastructure is triggered once per day (timing is configurable in the EventBridge rule). 
It removes any Cloudwatch Dashboards (excluding those with 'keep' in their name) that were created more than 3 days before (timing is configurable in the lambda function).
It removes any empty Cloudwatch Log Groups.
It also removes any alarms with a state of `INSUFFICIENT_DATA` that reached that state more than 1 day before (timing is configurable in the lambda function).

# Setup Lambda Function

*Create a new lambda functions.*

## Function Kill_Old_Dashboards

### Basic information
**Function name**:`Kill_Old_Cloudwatch_Infrastructure`  
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
* Copy Kill_Old_Cloudwatch_Infrastructure/`lambda_function.py` into the code area.
* If you would like for the Dashboard removal age to be anything other than 3 days, edit the `timedelta`
* Deploy.

# Setup EventBridge Rules

*Create a new rule in Amazon EventBridge that will trigger the lambda function.*

### Rule detail
**Name**: every_day
**Rule type**: Schedule

### Schedule pattern:
**A regular rate**: 1 Days

### Target 1:
**Target type**: AWS service
**Select a target**: Lambda function
**Function**: Kill_Old_Cloudwatch_Infrastructure