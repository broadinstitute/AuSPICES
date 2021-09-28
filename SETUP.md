# To create AuSPICES:

## AWS setup:
### Create deadletter queue.  
### Create sns.  
### Create IAM role:
Create an IAM Role for your step functions.  
Entity = AWS service  
Use case = Step Functions  
(Automatically adds permission policy AWSLambdaRole)  
Role name = StepFunctions  
Attach permissions policies: CloudWatchLogsFullAccess  

### Create layers:
Create a t2.micro instance in EC2 for lambda layer creation. AME = Amazon Linux 2 AMI (HVM), SSD Volume Type. Use the same network, subnet, and IAM as you usually use. Install python3 and update it to 3.8 or 3.9.  
Use this script for pe2loaddata layer creation.
```
mkdir pe2loaddata
# install package
python3.8 -m pip install pyyaml click -t pe2loaddata
python3.8 -m pip install pe2loaddata -t pe2loaddata --no-deps
# publish layer to lambda
mv pe2loaddata python
zip -r pe2loaddata.zip python/
chmod 400 pe2loaddata.zip
aws lambda publish-layer-version --layer-name pe2loaddata --zip-file fileb://pe2loaddata.zip --compatible-runtimes python3.8 python3.9
mv python pe2loaddata
```


## Lambda Setup:

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

## Step Function Setup:

Create State Machine  
Type = Standard  
Permissions = existing role = StepFunctions  
Logging = ALL  

(Copy and paste in code from FILENAME. In visual editor, for each Lambda:Invoke step, select the correct function name.)
