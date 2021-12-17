from ij import IJ
import os
import subprocess


# @String bucket
# @String project
# @String batch
# @String plate

localtemp = "temp"
outfolder = "montaged"

if not os.path.exists(localtemp):
    os.mkdir(localtemp)
if not os.path.exists(outfolder):
    os.mkdir(outfolder)

result_folder = f"s3://{str(bucket)}/projects/{str(project)}/workspace/segment/{str(batch)}/results/"
montage_folder = f"s3://{str(bucket)}/projects/{str(project)}/workspace/segment/{str(batch)}/montage/"

cmd = [
    "aws",
    "s3",
    "sync",
    "--exclude",
    "*",
    "--include",
    f"{plate}*/*.png",
    result_folder,
    localtemp,
]
print("Running", cmd)
subp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
while True:
    output = subp.stdout.readline()
    if output == "" and subp.poll() is not None:
        break
    if output:
        print(output.strip())

folderlist = os.listdir(localtemp)
for eachfolder in folderlist:
    if "-" in eachfolder:
        plate = eachfolder.split("-")[0]
        if not os.path.exists(os.path.join(localtemp, plate)):
            os.mkdir(os.path.join(localtemp, plate))
        for eachfile in os.listdir(os.path.join(localtemp, eachfolder)):
            if ".png" in eachfile:
                os.rename(
                    os.path.join(localtemp, eachfolder, eachfile),
                    os.path.join(localtemp, plate, eachfile),
                )

thisfolder = os.path.join(localtemp, plate)
sampleimage = os.listdir(thisfolder)[0]
IJ.run("Image Sequence...", "open=" + os.path.join(thisfolder, sampleimage) + " sort")
IJ.run("Make Montage...", "columns=24 rows=16 scale=1")
im = IJ.getImage()
IJ.saveAs("Tiff", os.path.join(outfolder, f"{plate}.tif"))
IJ.run("Close All")

cmd = ["aws", "s3", "sync", outfolder, montage_folder]
print("Running", cmd)
subp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
while True:
    output = subp.stdout.readline()
    if output == "" and subp.poll() is not None:
        break
    if output:
        print(output.strip())

print("Done making montages.")
