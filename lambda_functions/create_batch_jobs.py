import json
import boto3
import string
import os


class JobQueue:
    def __init__(self, name=None):
        self.sqs = boto3.resource("sqs")
        self.queue = self.sqs.get_queue_by_name(QueueName=name)
        self.inProcess = -1
        self.pending = -1

    def scheduleBatch(self, data):
        msg = json.dumps(data)
        response = self.queue.send_message(MessageBody=msg)
        print(("Batch sent. Message ID:", response.get("MessageId")))


# 384 Well Plate, 9 sites/well
rows = list(string.ascii_uppercase)[0:16]
columns = range(1, 25)
sites = range(1, 10)


def create_batch_jobs_2(project_name, pipeline_name, platelist, batchsuffix):
    illumqueue = JobQueue(project_name + "_Illum")
    startpath = os.path.join("projects", project_name)
    for toillum in platelist:
        templateMessage_illum = {
            "Metadata": "Metadata_Plate=" + toillum,
            "pipeline": os.path.join(
                startpath, "workspace/pipelines", batchsuffix, pipeline_name
            ),
            "output": os.path.join(startpath, batchsuffix, "illum"),
            "input": os.path.join(startpath, "workspace/qc", batchsuffix, "rules"),
            "data_file": os.path.join(
                startpath,
                "workspace/load_data_csv",
                batchsuffix,
                toillum,
                "load_data.csv",
            ),
        }
        illumqueue.scheduleBatch(templateMessage_illum)
    print("Illum job submitted. Check your queue")


def create_batch_jobs_3(project_name, pipeline_name, platelist, batchsuffix):
    qcqueue = JobQueue(project_name + "_QC")
    startpath = os.path.join("projects", project_name)
    for toqc in platelist:
        for eachrow in rows:
            for eachcol in columns:
                templateMessage_qc = {
                    "Metadata": "Metadata_Plate="
                    + toqc
                    + ",Metadata_Well="
                    + eachrow
                    + "%02d" % eachcol,
                    "pipeline": os.path.join(
                        startpath, "workspace/pipelines", batchsuffix, pipeline_name
                    ),
                    "output": os.path.join(
                        startpath, "workspace/qc/", batchsuffix, "results"
                    ),
                    "output_structure": "Metadata_Plate/Metadata_Plate-Metadata_Well",
                    "input": os.path.join(
                        startpath, "workspace/qc", batchsuffix, "rules"
                    ),
                    "data_file": os.path.join(
                        startpath,
                        "workspace/load_data_csv",
                        batchsuffix,
                        toqc,
                        "load_data.csv",
                    ),
                }
                qcqueue.scheduleBatch(templateMessage_qc)
    print("QC job submitted. Check your queue")


def create_batch_jobs_4():
    print()


def create_batch_jobs_5(project_name, pipeline_name, platelist, batchsuffix):
    qcqueue = JobQueue(projectname + "_Segment")
    startpath = os.path.join("projects", project_name)
    for toqc in platelist:
        for eachrow in rows:
            for eachcol in columns:
                templateMessage_qc = {
                    "Metadata": "Metadata_Plate="
                    + toqc
                    + ",Metadata_Well="
                    + eachrow
                    + "%02d" % eachcol,
                    "pipeline": os.path.join(
                        startpath, "workspace/pipelines", batchsuffix, pipeline_name
                    ),
                    "output": os.path.join(
                        startpath, "workspace/segment", batchsuffix, "results"
                    ),
                    "input": os.path.join(
                        startpath, "workspace/qc", batchsuffix, "rules"
                    ),
                    "data_file": os.path.join(
                        startpath,
                        "workspace/load_data_csv",
                        batchsuffix,
                        toqc,
                        "load_data_with_illum.csv",
                    ),
                }
                qcqueue.scheduleBatch(templateMessage_qc)
    print("QC job submitted. Check your queue")


def create_batch_jobs_6():
    print()


def create_batch_jobs_7(project_name, pipeline_name, platelist, batchsuffix):
    analysisqueue = JobQueue(projectname + "_Analysis")
    startpath = os.path.join("projects", project_name)
    for toanalyze in platelist:
        for eachrow in rows:
            for eachcol in columns:
                for eachsite in sites:
                    templateMessage_analysis = {
                        "Metadata": "Metadata_Plate="
                        + toanalyze
                        + ",Metadata_Well="
                        + eachrow
                        + "%02d" % eachcol
                        + ",Metadata_Site="
                        + str(eachsite),
                        "pipeline": os.path.join(
                            startpath, "workspace/pipelines", batchsuffix, pipeline_name
                        ),
                        "output": os.path.join(
                            startpath, "workspace/analysis", batchsuffix
                        ),
                        "output_structure": "Metadata_Plate/analysis/Metadata_Plate-Metadata_Well-Metadata_Site",
                        "input": os.path.join(
                            startpath, "workspace/qc", batchsuffix, "rules"
                        ),
                        "data_file": os.path.join(
                            startpath,
                            "workspace/load_data_csv",
                            batchsuffix,
                            toanalyze,
                            "load_data_with_illum.csv",
                        ),
                    }
                    analysisqueue.scheduleBatch(templateMessage_analysis)
    print("Analysis job submitted. Check your queue")
