import boto3

s3 = boto3.client("s3")

def lambda_handler(event, lambda_context):
    prefix = f"projects/{event['project_name']}/{event['batch']}/images/"
    bucket = event['bucket']
    platedict = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")

    exclude_plates = event['exclude_plates']
    include_plates = event['include_plates']

    if len(platedict["CommonPrefixes"]) >= 1:
        triggerlist = []
        for item in platedict["CommonPrefixes"]:
            fullplatename = item["Prefix"].rsplit("/", 2)[1]
            shortplatename = fullplatename.split("__")[0]
            if exclude_plates:
                if shortplatename not in exclude_plates:
                    minidict = {"plate": fullplatename}
                    triggerlist.append(minidict)
            elif include_plates:
                if shortplatename in include_plates:
                    minidict = {"plate": fullplatename}
                    triggerlist.append(minidict)
            else:
                minidict = {"plate": fullplatename}
                triggerlist.append(minidict)
        if len(triggerlist) >= 1:
            return triggerlist
        else:
            print ("Your include/exclude list filtered out all plates. Try again.")
            return
    else:
        print ("Didn't find images. Check batch listed in config is correct.")
        return
