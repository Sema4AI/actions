import difflib

from sema4ai.tasks import task


@task
def check_difflib_log():
    diff = difflib.ndiff("aaaa bbb ccc ddd".split(), "aaaa bbb eee ddd".split())
    print("".join(diff))
