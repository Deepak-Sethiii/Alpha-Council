# agents/state.py

import operator
from typing import TypedDict, List, Optional, Annotated

# This is the "Notebook" passed between all agents.
class AgentState(TypedDict):
    
    # --- 1. THE INPUTS (What starts the process) ---
    ticker: str          # The stock symbol (e.g., "AAPL")
    messages: List[str]  # Chat history (standard LangGraph requirement)
    
    # User Persona (Crucial for the math later)
    user_style: str      # "trader" (Short-term) or "investor" (Long-term)
    risk_profile: str    # "aggressive", "moderate", "conservative"
    
    # Metadata
    current_date: str    # Needed to prevent agents from reading old news
    news_cutoff_date: Optional[str] # Added this for safety

    # --- 2. ROUND 1: BLIND DIVERGENCE ---
    tech_thesis_initial: str        # The Chart Guy's first opinion
    tech_confidence_initial: float  # Score 0-100 (How sure is he?)
    
    fund_thesis_initial: str        # The Finance Guy's first opinion
    fund_confidence_initial: float  # Score 0-100
    
    # Temporary storage for raw reports if needed
    tech_report: Optional[str]
    fund_report: Optional[str]

    # --- 3. ROUND 2: THE ATTACK ---
    risk_critique_tech: str         # "Here is why the chart is wrong..."
    risk_critique_fund: str         # "Here is why the financials are misleading..."
    risk_danger_score: float        # Score 0-100 (Higher = MORE DANGER)

    # --- 4. ROUND 3: THE REBUTTAL ---
    tech_thesis_final: str          # "I admit the risk, but the trend is strong."
    tech_confidence_final: float    # Did confidence drop?
    
    fund_thesis_final: str          # "The lawsuit is scary, I'm lowering confidence."
    fund_confidence_final: float

    # --- 5. THE OUTPUT (RENAMED TO MATCH MAIN.PY) ---
    final_signal: str       # Was 'final_verdict' -> Now matches main.py
    final_confidence: float # Was 'final_score'   -> Now matches main.py
    final_explanation: str  # Was 'explanation'   -> Now matches main.py