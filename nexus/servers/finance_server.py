import yfinance as yf
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP
from datetime import datetime
import logging
import os
import re

# 1. Silence all background noise
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
os.environ['YF_NO_PRINTOUT'] = '1'

mcp = FastMCP("AlphaCouncil Finance")

@mcp.tool()
def analyze_stock(ticker: str) -> str:
    """Fetches stock price and trend."""
    try:
        stock = yf.Ticker(ticker)
        # .history does NOT accept progress=False in current versions
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return f"Error: No data found for ticker {ticker}"
            
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        latest = hist.iloc[-1]
        trend = "Bullish" if latest['Close'] > latest['SMA_20'] else "Bearish"
        
        return (
            f"Price: ${latest['Close']:.2f}\n"
            f"Trend: {trend}\n"
            f"Volume: {latest['Volume']}\n"
            f"Note: {'Above' if trend == 'Bullish' else 'Below'} SMA 20"
        )
    except Exception as e:
        return f"Tech Tool Error: {str(e)}"

@mcp.tool()
def get_fundamentals(ticker: str) -> str:
    """Fetches valuation and margin data."""
    try:
        stock = yf.Ticker(ticker)
        # info can be slow or chatty; we use it carefully
        info = stock.info
        
        return (
            f"Market Cap: {info.get('marketCap', 'N/A')}\n"
            f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
            f"Sector: {info.get('sector', 'N/A')}\n"
            f"Margins: {info.get('profitMargins', 'N/A')}"
        )
    except Exception as e:
        return f"Fund Tool Error: {str(e)}"

import time
import random

from datetime import datetime

@mcp.tool()
def search_news(query: str) -> str:
    """Production-grade news search with dynamic temporal gating."""
    try:
        now = datetime.now()
        # 🔒 Hard Constraint: Always include the current year/month in the query
        current_context = now.strftime("%B %Y") 
        dynamic_query = f"{query} {current_context}"
        
        with DDGS() as ddgs:
            # timelimit="m" forces DuckDuckGo to only return results from the last 30 days
            results = list(ddgs.text(
                dynamic_query, 
                timelimit="m",  
                max_results=8
            ))
            
        if not results: return "No news found for the current period."

        # Dynamic valid window: current year and last year (for Q4 transition)
        valid_years = {str(now.year), str(now.year - 1)}
        cleaned_results = []

        for r in results:
            content = (r['title'] + r.get('body', '')).lower()
            # Regex to find any 4-digit numbers starting with '20'
            found_years = set(re.findall(r'\b(20\d{2})\b', content))
            
            # 🛡️ DETERMINISTIC FILTER: If it only mentions old years, it's a ghost result
            if found_years and not (found_years & valid_years):
                continue
                
            cleaned_results.append(f"- {r['title']} ({r['href']})")

        return "\n".join(cleaned_results)
    except Exception as e:
        return f"Tool Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()