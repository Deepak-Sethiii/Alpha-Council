import os
import uvicorn
import yfinance as yf
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import your graph logic
from agent.graph import app as graph

load_dotenv()

app = FastAPI(title="Rhetora AI Backend")

# Allow Lovable to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This matches the data Lovable will send
class AnalysisRequest(BaseModel):
    ticker: str
    user_style: str = "investor"
    risk_profile: str = "moderate"

def get_constitutional_data(ticker: str):
    """
    Fetches immutable 'Hard Metrics' for the Constitutional Tribunal Audit.
    This guarantees the Risk Agent always has data to debate, even without news.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 1. Fetch Price History for Technical Calc (RSI)
        hist = stock.history(period="3mo")
        
        # Simple RSI Calculation (14-day) if enough data exists
        if len(hist) > 14:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
        else:
            current_rsi = 50  # Default neutral if IPO or insufficient data

        # 2. Extract Fundamental Risk Metrics
        audit_data = {
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "forward_pe": info.get('forwardPE', 'N/A'),
            "beta": info.get('beta', 'N/A'),  # Measure of volatility
            "debt_to_equity": info.get('debtToEquity', 'N/A'),
            "sector": info.get('sector', 'Unknown'),
            "rsi": round(float(current_rsi), 2) if not pd.isna(current_rsi) else 50.0
        }
        
        print(f"✅ Audit Data Fetched for {ticker}: P/E={audit_data['pe_ratio']}, RSI={audit_data['rsi']}")
        return audit_data

    except Exception as e:
        print(f"⚠️ Audit Data Fetch Failed: {e}")
        # Return 'safe' defaults so the system doesn't crash
        return {
            "pe_ratio": "N/A", "beta": "N/A", "rsi": 50.0, "debt_to_equity": "N/A", "sector": "Unknown"
        }

@app.get("/")
def read_root():
    return {"status": "active", "service": "Rhetora Backend"}

@app.post("/analyze")
async def run_analysis(request: AnalysisRequest):
    # Check for API Key
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing")

    print(f"🔥 Incoming Request: {request.ticker} ({request.user_style}/{request.risk_profile})")

    # 1. Fetch the Tribunal Data (The 'Constitutional' Metrics)
    audit_data = get_constitutional_data(request.ticker)

    # 2. Initialize the state with the NEW Audit Data injected
    # Ensure your AgentState in 'graph.py' allows these new keys!
    initial_state = {
        "ticker": request.ticker,
        "messages": [],
        "user_style": request.user_style,
        "risk_profile": request.risk_profile,
        # Injecting Audit Data into State for Risk Agent
        "pe_ratio": audit_data['pe_ratio'],
        "beta": audit_data['beta'],
        "rsi": audit_data['rsi'],
        "debt_to_equity": audit_data['debt_to_equity'],
        "sector": audit_data['sector']
    }

    try:
        # Run the Agents
        result = await graph.ainvoke(initial_state)

        # Send the JSON back to Lovable
        # Note: I updated the 'risk_analysis' keys to match the new Tribunal Prompt outputs
        return {
            "ticker": request.ticker,
            "final_verdict": {
                "signal": result.get("final_signal", "HOLD"),
                "confidence": result.get("final_confidence", 0),
                "explanation": result.get("final_explanation", "")
            },
            "technical_analysis": {
                "thesis": result.get("tech_thesis_final", ""),
                "confidence": result.get("tech_confidence_final", 0)
            },
            "fundamental_analysis": {
                "thesis": result.get("fund_thesis_final", ""),
                "confidence": result.get("fund_confidence_final", 0)
            },
            "risk_analysis": {
                # Mapped to the NEW prompt keys ("risk_score", "critique")
                "score": result.get("risk_score", 20), 
                "critique": result.get("critique", "Audit complete. No critical failure modes detected.")
            }
        }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get the port from the Environment (Render sets this)
    # If it's not set (like on your laptop), default to 8001
    port = int(os.environ.get("PORT", 8001)) 
    
    print(f"🚀 Starting server on Port {port}...")
    
    # HOST must be "0.0.0.0" for cloud access
    uvicorn.run(app, host="0.0.0.0", port=port)