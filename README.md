# AuSPICES
Automated System Processing Infinite Cellpainting Experiments with Step functions

## Setup:
Set up AWS environment, lambda functions, and step functions as detailed in SETUP.md.

## Run:
- Upload pipelines to s3://{bucket}/projects/{project}/workspace/pipelines/{batch}/  
- Upload configAWS.py and configFleet.json to s3://{bucket}/projects/{project}/workspace/lambda/{batch}/  
- Update metadatatemplate.json for your experiment.
- Step Functions => State machines => AuSPICES  
  Name = Description_of_trigger (optional)  
  Input = Paste in your metadata.json.
