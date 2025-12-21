# FIX: Use absolute imports starting from 'nexus'
from nexus.servers.registry import registry
from nexus.indicators.rsi import calculate_rsi
from nexus.indicators.sma import calculate_sma

# NOTE: We use a dummy list for now to prove the wiring works without API keys.
# In Phase 3, we will swap this for yfinance data.
MOCK_PRICES = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 110.0, 108.0, 109.0, 111.0, 
               115.0, 120.0, 122.0, 118.0, 119.0, 121.0, 125.0, 130.0, 128.0, 132.0]

@registry.register("get_technical_summary")
def get_technical_summary(ticker: str) -> dict:
    """
    Returns deterministic technical indicators for a ticker.
    Currently uses mock data to ensure system stability.
    """
    # 1. Fetch Data (Mock for now, will be yfinance in Phase 3)
    prices = MOCK_PRICES 
    current_price = prices[-1]

    # 2. Compute Deterministic Indicators (Your Code)
    rsi = calculate_rsi(prices, period=14)
    sma_5 = calculate_sma(prices, period=5)

    # 3. Return Pure JSON
    return {
        "ticker": ticker.upper(),
        "current_price": current_price,
        "indicators": {
            "rsi_14": rsi,
            "sma_5": sma_5,
            "signal": "BUY" if rsi < 30 else "SELL" if rsi > 70 else "HOLD"
        },
        "data_source": "deterministic_engine_v1"
    }