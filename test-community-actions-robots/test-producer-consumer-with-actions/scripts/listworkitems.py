from robocorp import workitems
from robocorp.tasks import task



@task
def list_work_items():
    for item in workitems.inputs:
        payload = item.payload
        print(payload)



