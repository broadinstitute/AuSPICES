import boto3
import os
import sys
import json
from pe2loaddata.__main__ import main as pe2loaddata

s3 = boto3.client("s3")

def lambda_handler(event, lambda_context):
    fullplate = event['trigger']['plate']
    plate = fullplate.split("__")[0]
    project_name = event['project_name']
    batch = event['batch']
    bucket = event['bucket']

    # Update config.yml based on Index.ids.xml file
    s3xmlfilepath = f"projects/{project_name}/{batch}/images/{fullplate}/Images/Index.idx.xml"
    localxmlfilepath = "/tmp/Index.idx.xml"
    #s3.download_file(bucket, s3xmlfilepath, localxmlfilepath)
    with open(localxmlfilepath, 'wb') as f:
        try:
            s3.download_fileobj(bucket, s3xmlfilepath, f)
        except botocore.exceptions.ClientError as error:
            print("Can't find the xml file. Something's up.")
            return
    with open(localxmlfilepath, encoding='utf-8-sig') as input_xml:
        xmlfile = json.load(input_xml)
    xmlfile
    """
    localyamlpath = "/tmp/config.yml"
    # open yaml
    # edit yaml to match xml

    # Trigger pe2loaddata
    pe2loaddata(config.yml f"~/efs/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data.csv" \
    --index-directory f"~/efs/{project_name}/workspace/images/{batch}/{fullplate}/Images" \
    --illum \
    --illum-directory f"/home/ubuntu/bucket/projects/{project_name}/{batch}/illum/{plate}" \
    --plate-id f"{plate}" \
    --illum-output f"~/efs/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data_with_illum.csv" \
    --sub-string-out f"efs/{project_name}/workspace/images/{batch}" \
    --sub-string-in f"bucket/projects/{project_name}/{batch}/images")
    """




"""
mkdir -p ~/efs/${PROJECT_NAME}/workspace/scratch/${BATCH_ID}/
PLATES=$(readlink -f ~/efs/${PROJECT_NAME}/workspace/scratch/${BATCH_ID}/plates_to_process.txt)
FULL_PLATES=$(readlink -f ~/efs/${PROJECT_NAME}/workspace/scratch/${BATCH_ID}/full_plates_to_process.txt)
ls ~/efs/${PROJECT_NAME}/workspace/images/${BATCH_ID}/ | cut -d '_' -f 1 >> $PLATES
ls ~/efs/${PROJECT_NAME}/workspace/images/${BATCH_ID}/ >> $FULL_PLATES
Check that your plate names are correct by nano $PLATES and nano $FULL_PLATES. If your plate names contain underscores, you may need to fix the simplified plate names. Both should have the same number of rows as the number of plates in your batch.

SAMPLE_PLATE_ID=PLATE_NAME_1
This can be any single plate name, again using the portion of the name that is before the double underscore __.
SAMPLE_FULL_PLATE_NAME=FULL_PLATE_NAME_1
This can be any single plate name, this time using the full name.
"""
