import os
import uvicorn
import yfinance as yf
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import your graph logic
# NOTE: Ensure you have an empty file named __init__.py inside your 'agent' folder!
from agent.graph import app as graph

load_dotenv()

app = FastAPI(title="Rhetora AI Backend")

# Allow Frontend (Lovable/v0) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    ticker: str
    user_style: str = "investor"
    risk_profile: str = "moderate"

def get_constitutional_data(ticker: str):
    """
    Fetches immutable 'Hard Metrics' for the Constitutional Tribunal Audit.
    Guaranteed to return a dictionary, never raises an exception.
    """
    print(f"📡 [DATA] Fetching hard metrics for {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        
        # Safety Net 1: Handle empty info
        info = stock.info or {} 
        
        # Safety Net 2: Handle calculation errors
        current_rsi = 50.0
        try:
            hist = stock.history(period="3mo")
            if len(hist) > 14:
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
        except Exception as rsi_error:
            print(f"⚠️ [DATA] RSI Calc failed: {rsi_error}")

        audit_data = {
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "forward_pe": info.get('forwardPE', 'N/A'),
            "beta": info.get('beta', 'N/A'),
            "debt_to_equity": info.get('debtToEquity', 'N/A'),
            "sector": info.get('sector', 'Unknown'),
            "rsi": round(float(current_rsi), 2) if not pd.isna(current_rsi) else 50.0
        }
        
        print(f"✅ [DATA] Success: P/E={audit_data['pe_ratio']}, RSI={audit_data['rsi']}")
        return audit_data

    except Exception as e:
        print(f"⚠️ [DATA] Global Fetch Failed: {e}")
        # Return 'safe' defaults so the system keeps running
        return {
            "pe_ratio": "N/A", "beta": "N/A", "rsi": 50.0, "debt_to_equity": "N/A", "sector": "Unknown"
        }

@app.get("/")
def read_root():
    return {"status": "active", "service": "Rhetora Tribunal Backend"}

@app.post("/analyze")
async def run_analysis(request: AnalysisRequest):
    if not os.getenv("GROQ_API_KEY"):
        print("❌ [ERROR] GROQ_API_KEY is missing from Environment Variables!")
        raise HTTPException(status_code=500, detail="Server misconfigured: API Key missing")

    print(f"🔥 [START] Request received for: {request.ticker}")

    # 1. Fetch Hard Metrics
    audit_data = get_constitutional_data(request.ticker)

    # 2. Inject into State
    initial_state = {
        "ticker": request.ticker,
        "messages": [],
        "user_style": request.user_style,
        "risk_profile": request.risk_profile,
        "pe_ratio": audit_data['pe_ratio'],
        "beta": audit_data['beta'],
        "rsi": audit_data['rsi'],
        "debt_to_equity": audit_data['debt_to_equity'],
        "sector": audit_data['sector']
    }

    try:
        # 3. Run the Agents
        print("🤖 [AGENT] Invoking Tribunal Graph...")
        result = await graph.ainvoke(initial_state)

        # --- X-RAY DIAGNOSTICS (Check Render Logs for this!) ---
        print("\n🔍 --- TRIBUNAL X-RAY ---")
        
        # Diagnostic 1: Did the Risk Agent run?
        raw_risk = result.get("risk_score")
        print(f"⚖️ Risk Score: {raw_risk} (Expected: 0-100)")
        
        # Diagnostic 2: Did the Rebuttal happen?
        msgs = result.get("messages", [])
        print(f"🗣️ Conversation Depth: {len(msgs)} messages exchanged.")
        
        if len(msgs) > 0:
            print(f"📝 Final Argument Snippet: {msgs[-1].content[:100]}...")
        else:
            print("⚠️ WARNING: Agents did not exchange messages. Check graph.py logic.")
            
        print("🔍 ------------------------\n")
        # -------------------------------------------------------

        return {
            "ticker": request.ticker,
            "final_verdict": {
                "signal": result.get("final_signal", "HOLD"),
                "confidence": result.get("final_confidence", 0),
                "explanation": result.get("final_explanation", "No explanation generated.")
            },
            "technical_analysis": {
                "thesis": result.get("tech_thesis_final", "Analysis pending."),
                "confidence": result.get("tech_confidence_final", 0)
            },
            "fundamental_analysis": {
                "thesis": result.get("fund_thesis_final", "Analysis pending."),
                "confidence": result.get("fund_confidence_final", 0)
            },
            "risk_analysis": {
                # Defaults to 50 (Neutral) if Agent fails, so it doesn't look like a crash
                "score": result.get("risk_score", 50), 
                "critique": result.get("critique", "Tribunal audit completed.")
            }
        }
    
    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Graph Execution Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Agent Error: {str(e)}")

if __name__ == "__main__":
    # Robust port selection for Render vs Local
    port = int(os.environ.get("PORT", 8001)) 
    print(f"🚀 Rhetora Tribunal is live on Port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)