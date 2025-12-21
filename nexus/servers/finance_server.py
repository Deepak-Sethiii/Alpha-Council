from mcp.server.fastmcp import FastMCP

# Initialize the Server
mcp = FastMCP("Nexus Finance")

@mcp.tool()
def get_stock_price(ticker: str) -> dict:
    """
    Returns the current stock price. 
    CURRENTLY A STUB: Returns fake data for testing.
    """
    # This print helps you see when Teammate A's agent calls your tool
    print(f"DEBUG: Tool called for {ticker}")
    
    return {
        "ticker": ticker,
        "price": 150.00, 
        "currency": "USD",
        "status": "STUB_DATA - REAL LOGIC COMING SOON"
    }

if __name__ == "__main__":
    mcp.run()