from mcp.server.fastmcp import FastMCP
from nexus.servers.tools import get_technical_summary

# Initialize the Server
mcp = FastMCP("Nexus Finance")

@mcp.tool()
def analyze_stock(ticker: str) -> dict:
    """
    Returns deterministic technical indicators (RSI, SMA) for a stock.
    Currently uses the Deterministic Engine v1.
    """
    # Call the registry-based tool you just verified
    return get_technical_summary(ticker)

if __name__ == "__main__":
    mcp.run()