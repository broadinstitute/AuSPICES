# To setup AuSPICES in AWS:

## Create deadletter queue.  

## Setup SNS.
### Create `Monitor` Topic
### Create `Email_USER` Topic
For each user that will be using AuSPICEs.
**Topic Name**: Email_USER
**Type**: Standard

Create an SNS subscription  
**Topic ARN**: arn:aws:sns:REGION:123456789123:Email_USER
**Protocol**: Email  
**Endpoint**: email_address_you_want_to_notify@yourdomain.com

Your endpoint email address will get an automated notification from AWS requesting confirmation.
Confirm it.

## Setup IAM.
### Create an IAM Role for your step functions.  
Entity = AWS service  
Use case = Step Functions  
(Automatically adds permission policy AWSLambdaRole)  
Role name = StepFunctions  
Attach permissions policies: CloudWatchLogsFullAccess  
### Create an IAM Role for your lambda functions.
Entity = AWS service
Use case = Lambda
Role name = LambdaFullAccess
Attach permissions policies: AmazonSQSFullAccess, AmazonS3FullAccess, AmazonEC2SpotFleetTaggingRole, AmazonECS_FullAccess, AWSLambdaExecute, AWSLambdaSQSQueueExecutionRole, AmazonSNSFullAccess, AWSLambdaRole, AWSLambda_FullAccess

## Create layers:
### Create instance for layer creation
Create a t2.micro instance in EC2 for lambda layer creation.  
AME = Amazon Linux 2 AMI (HVM), SSD Volume Type.  
Use the same network, subnet, and IAM as you usually use.  
Install python3 and update it to 3.8 or 3.9.  

### Create and publish `pe2loaddata` layer
```
mkdir pe2loaddata
# install packages
python3.8 -m pip install pyyaml click -t pe2loaddata
python3.8 -m pip install pe2loaddata -t pe2loaddata --no-deps
# publish layer to lambda
mv pe2loaddata python
zip -r pe2loaddata.zip python/
chmod 400 pe2loaddata.zip
aws lambda publish-layer-version --layer-name pe2loaddata --zip-file fileb://pe2loaddata.zip --compatible-runtimes python3.8 python3.9
mv python pe2loaddata
```
### Create and publish `data_plotting` layer
```
mkdir data_plotting
# install packages
python3.8 -m pip install pytz  -t data_plotting --no-deps
python3.8 -m pip install pandas  -t data_plotting --no-deps
# publish layer to lambda
mv data_plotting python
zip -r data_plotting.zip python/
chmod 400 data_plotting.zip
aws lambda publish-layer-version --layer-name data_plotting --zip-file fileb://data_plotting.zip --compatible-runtimes python3.8
mv python data_plotting
```

## Lambda Setup:
For each function, step 0-7:
### Create function:
Function name = AUSPICES_{folder_name} (e.g. AUSPICES_0_setup)  
Runtime = Python 3.8 or 3.9  
Use an existing role = LambdaFullAccess  

### Function Code:
Copy step's *lambda_function.py* into lambda_function. Deploy.   
For each necessary function (listed below):
- File => New file
- Paste in function's code.
- File => Save As => {function_name}  


### Configuration:
#### General Configuration:
Memory = 3008 MB  
Timeout = 15 min
#### Asynchronous invocation:
Retry attempts = 0
#### Environment variables:
Key = MY_AWS_ACCESS_KEY_ID, Value = {your_access_key}  
Key = MY_AWS_SECRET_ACCESS_KEY_ID, Value = {your_secret_access_key}
#### Layers:
Add necessary layers (listed below).


Step | Layers Needed | Functions Needed
--|--|--
0_setup | - | -
1_pe2loaddata | pe2loaddata (custom layer) | config.yml
4_checkqc | data_plotting (custom layer) | -

## Step Function Setup:

Create State Machine  
Type = Standard  
Permissions = existing role = StepFunctions  
Logging = ALL  

(Copy and paste in code from FILENAME. In visual editor, for each Lambda:Invoke step, select the correct function name.)
