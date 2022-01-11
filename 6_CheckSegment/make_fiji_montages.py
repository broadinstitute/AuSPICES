#@String bucket
#@String project
#@String batch
#@String plate

from ij import IJ
import os
import subprocess

localtemp = "temp"
outfolder = "montaged"

if not os.path.exists(localtemp):
    os.mkdir(localtemp)
if not os.path.exists(outfolder):
    os.mkdir(outfolder)

s3_start_path = "s3://" + bucket + "/projects/" + project + "/workspace/segment/" + batch

cmd = [
    "aws",
    "s3",
    "sync",
    "--exclude",
    "*",
    "--include",
    (plate + "*/*.png"),
    os.path.join(s3_start_path, "results"),
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
outname = plate + '.tif'
IJ.saveAs("Tiff", os.path.join(outfolder, outname))
IJ.run("Close All")

cmd = ["aws", "s3", "sync", outfolder, os.path.join(s3_start_path, montages)]
print("Running", cmd)
subp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
while True:
    output = subp.stdout.readline()
    if output == "" and subp.poll() is not None:
        break
    if output:
        print(output.strip())

print("Done making montages.")
