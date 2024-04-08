import boto3
import re
import json

s3 = boto3.client("s3")


def lambda_handler(event, lambda_context):
    bucket = event["bucket"]
    if event["zproject"]:
        print("Images will be z-projected.")
        if bucket == 'cellpainting-gallery':
            prefix = (
            f"{event['project_name']}/broad/{event['batch']}/images/"
            )
        else:
            prefix = (
                f"projects/{event['project_name']}/{event['batch']}/images_unprojected/"
            )
    else:
        print("Images will not be z-projected.")
        if bucket == 'cellpainting-gallery':
            prefix = f"{event['project_name']}/broad/images/{event['batch']}/images/"
        else:
            prefix = f"projects/{event['project_name']}/{event['batch']}/images/"
    
    platename_replacementdict = event["platename_replacementdict"]
    platedict = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")

    exclude_plates = event["exclude_plates"]
    include_plates = event["include_plates"]

    if len(platedict["CommonPrefixes"]) >= 1:
        triggerlist = []
        auto_platedict = {}
        for item in platedict["CommonPrefixes"]:
            fullplatename = item["Prefix"].rsplit("/", 2)[1]
            shortplatename = fullplatename.split("__")[0]

            if exclude_plates:
                if shortplatename in exclude_plates:
                    continue
            if include_plates:
                if shortplatename not in include_plates:
                    continue

            remote_xml_file = f"{prefix}{fullplatename}/Images/Index.idx.xml"
            xml_head_object = s3.get_object(
                Bucket=bucket, Key=remote_xml_file, Range="bytes=0-3000"
            )
            xml_head = xml_head_object["Body"].read().decode("utf-8")
            match = re.search("<Name>(.+?)</Name>", xml_head)
            if match:
                plate_from_xml = match.group(1)
                auto_platedict[fullplatename] = plate_from_xml
            else:
                print(f"Failed at finding replacement name for {fullplatename}")

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

        if platename_replacementdict:
            print(
                f"Platename replacement dictionary auto-generates as {json.dumps(auto_platedict)}"
            )
            print(
                f"Platename replacement dictionary entered as {json.dumps(platename_replacementdict)}"
            )
            replaced_dictionary = auto_platedict.copy()
            for origname, newname in list(platename_replacementdict.items()):
                if origname in list(replaced_dictionary.keys()):
                    replaced_dictionary[origname] = platename_replacementdict[origname]
            print(f"Dictionary with replacements is {json.dumps(replaced_dictionary)}")
            for key, value in replaced_dictionary.items():
                if " " in value:
                    print(
                        f"WARNING: {key} will be named {value} and likely needs fixing using platename_replacementdict."
                    )
        else:
            print(
                f"Platename replacement dictionary auto-generates as {json.dumps(auto_platedict)}"
            )
            for key, value in auto_platedict.items():
                if " " in value:
                    print(
                        f"WARNING: {key} will be named {value} and likely needs fixing using platename_replacementdict."
                    )

        if len(triggerlist) >= 1:
            return triggerlist
        else:
            print("Your include/exclude list filtered out all plates. Try again.")
            return
    else:
        print("Didn't find images. Check batch listed in config is correct.")
        return
