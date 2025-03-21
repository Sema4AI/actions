import sys

if __name__ == "__main__":
    from sema4ai.action_server.cli import main

    args = None
    # args = "start --https --ssl-self-signed --full-openapi-spec".split()
    # args = "start --full-openapi-spec".split()
    # args = ["start", "--full-openapi"]
    # import os

    # os.chdir(r"d:\x\temp\check-action-server\oauth-google")
    # args = ["start", "--expose"]

    # args = "start --port 61080 --actions-sync=false --datadir=/Users/fabioz/.sema4ai/.sema4ai_code/oauth2/datadir".split()

    try:
        main(args)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
