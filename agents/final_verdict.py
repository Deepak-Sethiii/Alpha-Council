# agents/final_verdict.py
from agents.state import AgentState

def get_weights(style: str, risk: str):
    """
    Returns weight dictionary based on User Style and Risk Tolerance.
    """
    style = style.lower().strip()
    risk = risk.lower().strip()

    # --- TRADER LOGIC (Technicals lead) ---
    if style == "trader":
        if risk == "aggressive":
            # "I want momentum, I don't care if the company makes money."
            return {"tech": 0.60, "fund": 0.10, "risk": 0.30}
        elif risk == "conservative":
            # "I want a quick trade, but only if it's safe."
            return {"tech": 0.40, "fund": 0.20, "risk": 0.40}
        else: # Moderate (Default)
            return {"tech": 0.50, "fund": 0.20, "risk": 0.30}

    # --- INVESTOR LOGIC (Fundamentals lead) ---
    elif style == "investor":
        if risk == "aggressive":
            # "I want high-growth startups. Ignore the chart noise."
            return {"tech": 0.10, "fund": 0.60, "risk": 0.30}
        elif risk == "conservative":
            # "I want boring, safe dividend stocks. Safety is #1."
            return {"tech": 0.10, "fund": 0.40, "risk": 0.50}
        else: # Moderate (Default)
            return {"tech": 0.20, "fund": 0.50, "risk": 0.30}
    
    # Fallback
    return {"tech": 0.33, "fund": 0.33, "risk": 0.34}

def calculate_verdict(state: AgentState) -> dict:
    """
    The Math Engine: Combines scores using the weights.
    """
    # 1. Get Weights based on the user's profile in the state
    user_style = state.get("user_style", "investor")
    risk_profile = state.get("risk_profile", "moderate")
    weights = get_weights(user_style, risk_profile)
    
    # 2. Get Scores (Default to 50 if missing)
    tech_score = state.get("tech_confidence_final", 50)
    fund_score = state.get("fund_confidence_final", 50)
    risk_score = state.get("risk_danger_score", 50)

    # 3. The Formula
    # We ADD confidence from Tech/Fund.
    # We SUBTRACT danger from Risk.
    weighted_score = (
        (tech_score * weights["tech"]) + 
        (fund_score * weights["fund"]) - 
        (risk_score * weights["risk"])
    )
    
    # 4. Normalize logic
    # Since we subtract risk, the score might be low (e.g., 20-30 is actually good).
    # If the result is positive (> 15), it means the strengths outweighed the risks.
    threshold = 15 
    
    verdict = "NO"
    if weighted_score > threshold: 
        verdict = "YES"

    return {
        "final_verdict": verdict, 
        "final_score": round(weighted_score, 2)
    }