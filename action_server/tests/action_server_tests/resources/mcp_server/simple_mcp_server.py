import sys


def run_mcp_server(port: int):
    import logging

    from mcp.server.fastmcp import FastMCP
    from mcp.types import CancelledNotification

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    mcp = FastMCP(name="EchoServer", stateless_http=True, port=port)

    @mcp.tool()
    def greet(name: str, title="Mr.") -> str:
        """
        Provides a greeting for a person.

        Args:
            name: The name of the person to greet.
            title: The title for the persor (Mr., Mrs., ...).

        Returns:
            The greeting for the person.
        """
        return f"Hello {title} {name}."

    @mcp.tool()
    async def long_running_tool(duration: float) -> str:
        """
        Does a long running task.

        Args:
            duration: The duration to wait in seconds.

        Returns:
            The result of the long running task.
        """
        # We'd like to cancel this, but it's just not possible with the current SDK!
        import asyncio

        await asyncio.sleep(duration)
        return "ok"

    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    port = int(sys.argv[1])
    run_mcp_server(port=port)
