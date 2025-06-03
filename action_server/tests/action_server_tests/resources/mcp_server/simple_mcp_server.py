import sys


def run_mcp_server(port: int):
    from mcp.server.fastmcp import FastMCP

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

    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    port = int(sys.argv[1])
    run_mcp_server(port=port)
