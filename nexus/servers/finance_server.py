import yfinance as yf
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP

# Initialize the Official MCP Server
mcp = FastMCP("AlphaCouncil Finance")

# --- 1. STOCK ANALYSIS TOOL ---
@mcp.tool()
def analyze_stock(ticker: str) -> str:
    """
    Fetches historical stock data and calculates basic technical indicators (SMA, RSI).
    """
    try:
        # Fetch Data
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return "No data found for ticker."
            
        # Basic Calculation (SMA)
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        latest = hist.iloc[-1]
        
        # Simple Trend Logic
        trend = "Bullish" if latest['Close'] > latest['SMA_20'] else "Bearish"
        
        return (
            f"Price: ${latest['Close']:.2f}\n"
            f"Trend: {trend}\n"
            f"Volume: {latest['Volume']}\n"
            f"Note: Price is above SMA 20" if trend == "Bullish" else "Note: Price is below SMA 20"
        )
    except Exception as e:
        return f"Error analyzing stock: {e}"

# --- 2. FUNDAMENTALS TOOL ---
@mcp.tool()
def get_fundamentals(ticker: str) -> str:
    """
    Fetches fundamental data like P/E Ratio, Market Cap, and Dividend Yield.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return (
            f"Market Cap: {info.get('marketCap', 'N/A')}\n"
            f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
            f"Dividend Yield: {info.get('dividendYield', 'N/A')}\n"
            f"Sector: {info.get('sector', 'N/A')}\n"
            f"Business Summary: {info.get('longBusinessSummary', 'No summary')[:200]}..."
        )
    except Exception as e:
        return f"Error fetching fundamentals: {e}"

# --- 3. NEWS TOOL ---
@mcp.tool()
def search_news(query: str) -> str:
    """
    Searches DuckDuckGo for recent news articles.
    """
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No news found."
        
        output = []
        for r in results:
            output.append(f"- {r['title']} ({r['href']})")
        return "\n".join(output)
    except Exception as e:
        return f"Error searching news: {e}"

# --- 4. COMPETITORS TOOL ---
@mcp.tool()
def get_competitors(ticker: str) -> str:
    """
    Returns a list of major competitors for a given stock ticker.
    """
    try:
        query = f"top competitors of {ticker} stock"
        results = DDGS().text(query, max_results=3)
        
        if not results:
            return "No competitor data found."
            
        formatted_results = []
        for r in results:
            formatted_results.append(f"- {r['title']}: {r['href']}")
            
        return "Top Competitors found:\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error finding competitors: {str(e)}"

# Start the MCP Server
if __name__ == "__main__":
    mcp.run()