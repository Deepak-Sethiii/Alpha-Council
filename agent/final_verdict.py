# agent/final_verdict.py
from agent.state import AgentState

def get_weights(style: str, risk: str):
    """
    Returns weight dictionary based on User Style and Risk Tolerance.
    """
    style = style.lower().strip()
    risk = risk.lower().strip()

    # --- TRADER LOGIC (Technicals lead) ---
    if style == "trader":
        if risk == "aggressive":
            return {"tech": 0.60, "fund": 0.10, "risk": 0.30}
        elif risk == "conservative":
            return {"tech": 0.40, "fund": 0.20, "risk": 0.40}
        else: # Moderate (Default)
            return {"tech": 0.50, "fund": 0.20, "risk": 0.30}

    # --- INVESTOR LOGIC (Fundamentals lead) ---
    elif style == "investor":
        if risk == "aggressive":
            return {"tech": 0.10, "fund": 0.60, "risk": 0.30}
        elif risk == "conservative":
            return {"tech": 0.10, "fund": 0.40, "risk": 0.50}
        else: # Moderate (Default)
            return {"tech": 0.20, "fund": 0.50, "risk": 0.30}
    
    # Fallback
    return {"tech": 0.33, "fund": 0.33, "risk": 0.34}

def calculate_verdict(state: AgentState) -> dict:
    """
    The Math Engine: Combines scores using the weights.
    """
    # 1. Get Weights based on the user's profile
    user_style = state.get("user_style", "investor")
    risk_profile = state.get("risk_profile", "moderate")
    weights = get_weights(user_style, risk_profile)
    
    # 2. Get Scores (Safely handle None)
    def clean_score(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return 50.0

    tech_score = clean_score(state.get("tech_confidence_final"))
    fund_score = clean_score(state.get("fund_confidence_final"))
    risk_score = clean_score(state.get("risk_danger_score"))

    # 3. The Formula
    weighted_score = (
        (tech_score * weights["tech"]) + 
        (fund_score * weights["fund"]) - 
        (risk_score * weights["risk"])
    )
    
    # 4. Determine Signal (BUY / SELL / HOLD)
    # Since we subtract Risk, scores can be low. 
    # Example: (80*0.5) + (80*0.2) - (50*0.3) = 40 + 16 - 15 = 41.0
    
    if weighted_score >= 25: 
        signal = "BUY"
    elif weighted_score <= 10:
        signal = "SELL"
    else:
        signal = "HOLD"

    # 5. Generate Explanation
    explanation = (
        f"Math Score: {weighted_score:.1f}. (Tech: {tech_score}, Fund: {fund_score}, Risk: {risk_score}). "
        f"Verdict based on {user_style} style."
    )

    return {
       "final_signal": signal,
       "final_confidence": round(weighted_score, 1),
       "final_explanation": explanation
    }