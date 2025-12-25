import asyncio
import os
from dotenv import load_dotenv

# 1. LOAD API KEYS (CRITICAL STEP)
load_dotenv()

# Verify key exists
if not os.getenv("GROQ_API_KEY"):
    print("❌ ERROR: GROQ_API_KEY not found. Check your .env file!")
    exit(1)

from agent.state import AgentState
from agent.graph import app as graph

async def run_stress_test():
    print("🔥 STARTING STRESS TEST ON AGENT BRAINS 🔥")
    print("="*60)

    # 2. Define Tickers
    tickers = ["TSLA", "KO", "GME"] 

    for ticker in tickers:
        print(f"\n🔎 Analyzing {ticker}...")
        
        initial_state = {
            "ticker": ticker,
            "messages": [],
            "user_style": "investor",
            "risk_profile": "moderate"
        }

        # 3. Run the Graph
        result = await graph.ainvoke(initial_state)
        
        # 4. Print Deep Analysis
        print(f"--- 🧠 AGENT THOUGHTS FOR {ticker} ---")
        
        print(f"\n📈 [Technical Analyst]:")
        print(f"   Thesis: \"{result.get('tech_thesis_final', 'No thesis')}\"")
        print(f"   Confidence: {result.get('tech_confidence_final')}%")

        print(f"\n💰 [Fundamental Analyst]:")
        print(f"   Thesis: \"{result.get('fund_thesis_final', 'No thesis')}\"")
        print(f"   Confidence: {result.get('fund_confidence_final')}%")

        print(f"\n🚨 [Risk Manager]:")
        print(f"   Score: {result.get('risk_danger_score')}/100")
        print(f"   Critique: \"{result.get('risk_critique_tech', 'No critique')}\"")

        print("-" * 30)
        
        # 5. Print Final Verdict
        print(f"🎯 FINAL VERDICT:")
        print(f"   Signal:     {result['final_signal']}") 
        print(f"   Confidence: {result['final_confidence']}%") 
        print(f"   Explanation: {result['final_explanation']}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(run_stress_test())