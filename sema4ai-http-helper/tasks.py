from invoke import Context, task

TAG = "sema4ai-http-helper-{tag}"


@task
# @task(name="check-tag-version")
def check_tag_version(ctx: Context):
    current_version = str(ctx.run("poetry version -s", hide=True).stdout.strip())
    # will error our it git describes errors out
    ctx.run(
        f"git describe --exact-match --tags {TAG.format(tag=current_version)}",
        echo=False,
    )


@task
def create_tag(ctx: Context):
    current_version = str(ctx.run("poetry version -s", hide=True).stdout.strip())
    tag = TAG.format(tag=current_version)
    ctx.run(f"git tag {tag}")
    ctx.run(f"git push origin {tag}")
