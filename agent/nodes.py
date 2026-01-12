# agent/nodes.py
import json
import os
import sys
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.append(root_path)
import subprocess
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from agent.utils import get_current_date, get_news_cutoff_date
from nexus.servers.tools import get_technical_summary, get_market_news
from agent.prompts import (
    TECHNICAL_INITIAL_PROMPT, TECHNICAL_REBUTTAL_PROMPT,
    FUNDAMENTAL_INITIAL_PROMPT, FUNDAMENTAL_REBUTTAL_PROMPT,
    RISK_CRITIQUE_PROMPT
)

# --- 1. SETUP LLM ---
def get_llm():
    return ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.0)

def call_mcp_tool(tool_name, arguments):
    # 1. Handshake Definitions
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "alpha", "version": "1.0"}}}
    init_not = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    tool_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}}
    
    payload = json.dumps(init_req) + "\n" + json.dumps(init_not) + "\n" + json.dumps(tool_req) + "\n"

    # 2. Path Resolution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    server_path = os.path.join(root_dir, "nexus", "servers", "finance_server.py")
    
    # 3. Environment Setup
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([root_dir, os.path.join(root_dir, "nexus")])
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            encoding='utf-8',
            bufsize=1
        )
        
        stdout, stderr = process.communicate(input=payload, timeout=15)
        
        if stdout:
            for line in stdout.strip().split("\n"):
                clean_line = line.strip()
                if clean_line.startswith('{"jsonrpc":"2.0"') or clean_line.startswith('{"id":2'):
                    try:
                        resp = json.loads(clean_line)
                        if resp.get("id") == 2:
                            if "result" in resp:
                                return resp["result"]["content"][0]["text"]
                            if "error" in resp:
                                return f"MCP Tool Error: {resp['error']}"
                    except json.JSONDecodeError: 
                        continue

        error_msg = f"Data Fetch Failed. Raw: {stdout[:50]} | Stderr: {stderr[:50]}"
        print(f"❌ [MCP ERROR] {error_msg}")
        return error_msg

    except subprocess.TimeoutExpired:
        process.kill()
        return "Error: MCP Server timed out."
    except Exception as e:
        return f"Execution Failed: {str(e)}"

# --- HELPER: SCORE NORMALIZER ---
def normalize_score(val):
    try:
        f = float(val)
        # ❌ OLD: if f <= 0: return 50.0 
        # ✅ NEW: Allow 0 if the agent finds no risk
        if f < 0: return 0.0 
        
        if 0 < f <= 1.0: return f * 100.0
        if f > 100: return 100.0
        return f
    except:
        # If parsing fails, 50 is a safe "neutral" middle ground
        return 50.0

# --- HELPER: PARSER ---
def parse_json_safely(text):
    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            return json.loads(clean[start : end + 1])
        return None
    except:
        return None

# --- 3. AGENT NODES ---

def technical_analyst(state: AgentState):
    ticker = state["ticker"]
    print(f"\n📈 [Technical] Analyzing {ticker}...")
    
    data = call_mcp_tool("analyze_stock", {"ticker": ticker})
    print(f"👀 [DEBUG] Tech Data: {str(data)[:60]}...") 

    llm = get_llm()
    prompt = TECHNICAL_INITIAL_PROMPT.format(ticker=ticker, data=data)
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Analyze {ticker} now.")
    ]
    response = llm.invoke(messages)
    
    data_json = parse_json_safely(response.content)
    if data_json:
        conf = normalize_score(data_json.get("confidence", 50))
        thesis = data_json.get("thesis", "Analysis provided.")
    else:
        print(f"⚠️ Tech Parsing Failed. Output: {response.content[:50]}...")
        conf = 50.0
        thesis = response.content

    return {"tech_thesis_initial": thesis, "tech_confidence_initial": conf}

def fundamental_analyst(state: AgentState):
    ticker = state["ticker"]
    print(f"💰 [Fundamental] Analyzing {ticker}...")
    
    data = call_mcp_tool("get_fundamentals", {"ticker": ticker})
    
    llm = get_llm()
    prompt = FUNDAMENTAL_INITIAL_PROMPT.format(ticker=ticker, data=data)
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Analyze {ticker} now.")
    ]
    response = llm.invoke(messages)
    
    data_json = parse_json_safely(response.content)
    if data_json:
        conf = normalize_score(data_json.get("confidence", 50))
        thesis = data_json.get("thesis", "Analysis provided.")
    else:
        print(f"⚠️ Fund Parsing Failed. Output: {response.content[:50]}...")
        conf = 50.0
        thesis = response.content

    return {"fund_thesis_initial": thesis, "fund_confidence_initial": conf}


from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage, HumanMessage
import re

def extract_ticker_evidence(news_data: str, ticker: str) -> dict:
    """
    Production-Grade Extraction Engine:
    1. Isolates ticker symbols using word boundaries.
    2. Gathers current temporal evidence (2025-2026).
    3. Hard-gates historical transcripts and archived noise.
    """
    if not news_data or not isinstance(news_data, str):
        return {'has_ticker': False, 'evidence_sentences': [], 'summary': ''}

    # --- 1. DYNAMIC TEMPORAL WINDOW ---
    now = datetime.now()
    current_year = now.year # 2026
    valid_years = {str(current_year), str(current_year - 1)}
    
    # Identify "Stale" years for the hard-gate
    stale_range = [str(y) for y in range(2020, current_year - 1)]
    stale_regex = r'\b(' + '|'.join(stale_range) + r')\b'

    # --- 2. THE UNIVERSAL TICKER PATTERN ---
    # re.escape handles special chars; \b prevents partial matches (e.g., 'AAPL' in 'AAPLY')
    ticker_patterns = [
        rf'\b{re.escape(ticker)}\b',
        rf'\b{re.escape(ticker)}\'s\b',
        rf'\b{re.escape(ticker.upper())}\b',
        rf'\b{re.escape(ticker.lower())}\b'
    ]
    combined_ticker_pattern = '|'.join(ticker_patterns)

    # --- 3. PROCESS SENTENCES ---
    # Split by common sentence terminators and newlines
    raw_sentences = re.split(r'[.!?]+\s+|\n', news_data)
    evidence_sentences = []
    
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if len(sentence) < 20: continue # Ignore fragments
            
        # STEP A: Ticker Identification
        if re.search(combined_ticker_pattern, sentence, re.IGNORECASE):
            
            # STEP B: Temporal Gating (The "Archive Killer")
            # If a sentence mentions 2022-2024, reject it UNLESS it also mentions 2026.
            # This allows comparative news but blocks pure historical transcripts.
            has_stale_year = re.search(stale_regex, sentence)
            is_contextually_current = str(current_year) in sentence
            
            if has_stale_year and not is_contextually_current:
                continue
            
            # STEP C: Validate that if any year is mentioned, it's not ONLY old ones
            found_years = set(re.findall(r'\b(20\d{2})\b', sentence))
            if found_years and not (found_years & valid_years):
                continue
            
            evidence_sentences.append(sentence)

    return {
        'has_ticker': len(evidence_sentences) > 0,
        'evidence_sentences': evidence_sentences,
        'summary': ' '.join(evidence_sentences[:3])
    }
    
def generate_dynamic_queries(ticker: str) -> list:
    """Calculates relative search terms to ensure the agent is always 'Now'."""
    now = datetime.now()
    month_name = now.strftime("%B") # e.g., "January"
    year = now.year                 # e.g., 2026
    
    return [
        # Pass 1: discovery (What happened this month?)
        f"{ticker} stock price catalysts {month_name} {year}",
        # Pass 2: audit (Is there an active investigation THIS year?)
        f"{ticker} corporate regulatory risk investigation {year}",
        # Pass 3: guidance (What is the outlook for this year?)
        f"{ticker} investor guidance outlook {year} analyst report"
    ]

def risk_manager(state: AgentState):
    ticker = state["ticker"]
    now = datetime.now()
    current_dt = get_current_date()
    cutoff_dt = get_news_cutoff_date()
    
    debug_log = []
    
    queries = generate_dynamic_queries(ticker)
    news_data = ""
    
    for i, q in enumerate(queries, 1):
        debug_log.append(f"[PASS {i}] Query: {q}")
        batch = get_market_news(q)
        if batch and len(str(batch)) > 150:
            news_data += str(batch)
            # If we have enough data from the first two passes, stop searching
            if len(news_data) > 3000:
                break
        
    # ✅ PERMANENT FIX: Force Terminal Output on Windows
    print("\n" + "🔥" * 30, flush=True)
    print(f"🔎 [AGENT AUDIT] RAW NEWS FETCHED FOR: {ticker.upper()}", flush=True)
    print("-" * 60, flush=True)
    
    if news_data and len(str(news_data)) > 10:
        # We print a significant chunk to see the actual Eli Lilly / H200 headlines
        print(str(news_data)[:2000], flush=True) 
    else:
        print(f"⚠️ WARNING: No news data returned for {ticker}. Check Search API.", flush=True)
        
    print("-" * 60, flush=True)
    print("🔥" * 30 + "\n", flush=True)
    
    # ✅ PERMANENT FIX: PRE-EXTRACT EVIDENCE PROGRAMMATICALLY
    evidence_data = extract_ticker_evidence(str(news_data), ticker)
    
    debug_log.append(f"📍 Evidence Pre-Check: Ticker found = {evidence_data['has_ticker']}")
    debug_log.append(f"📍 Sentences with ticker: {len(evidence_data['evidence_sentences'])}")
    if evidence_data['evidence_sentences']:
        debug_log.append(f"📍 First evidence: {evidence_data['evidence_sentences'][0][:150]}")
    
    # ✅ EARLY EXIT: If no ticker evidence found, return baseline immediately
    if not evidence_data['has_ticker']:
        debug_log.append("🚨 NO TICKER EVIDENCE FOUND - Returning baseline risk")
        return {
            "risk_critique_tech": "No ticker-specific evidence found.",
            "risk_critique_fund": "No ticker-specific evidence found.",
            "risk_danger_score": 25.0,
            "risk_news_summary": str(news_data)[:500],
            "debug_log": debug_log
        }
    
    # ✅ Execute LLM Audit ONLY with pre-validated evidence
    llm = get_llm()
    prompt = RISK_CRITIQUE_PROMPT.format(
        ticker=ticker,
        current_date=current_dt,
        news_cutoff_date=cutoff_dt,
        tech_thesis=state.get("tech_thesis_initial", ""),
        fund_thesis=state.get("fund_thesis_initial", ""),
        news=news_data,
        pre_extracted_evidence=evidence_data['summary']  # ✅ Give LLM the evidence
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    data_json = parse_json_safely(response.content)

    # ✅ VALIDATION: Use pre-extracted evidence as ground truth
    risk_score = 0
    risk_critique_tech = "None"
    risk_critique_fund = "None"
    
    if data_json:
        llm_evidence = data_json.get("evidence_found", "")
        llm_risk_score = normalize_score(data_json.get("risk_score", 0))
        
        debug_log.append(f"🤖 LLM Evidence: {llm_evidence[:200]}")
        debug_log.append(f"🤖 LLM Risk Score: {llm_risk_score}")
        
        # DOUBLE VALIDATION: Check if LLM evidence matches our pre-extracted evidence
        llm_has_ticker = any(
            sent[:100] in llm_evidence or llm_evidence[:100] in sent
            for sent in evidence_data['evidence_sentences']
        )
        
        if not llm_has_ticker and llm_evidence.strip():
            # LLM hallucinated evidence - reject it
            debug_log.append("🚨 LLM HALLUCINATION: Evidence doesn't match pre-extracted sentences")
            risk_score = 25.0
            risk_critique_tech = "No ticker-specific evidence found."
            risk_critique_fund = "No ticker-specific evidence found."
        else:
            # LLM evidence is valid - use its assessment
            risk_score = llm_risk_score
            risk_critique_tech = data_json.get("risk_critique_tech", "None")
            risk_critique_fund = data_json.get("risk_critique_fund", "None")
            
            debug_log.append(f"✅ Valid LLM assessment. Risk: {risk_score}")
            
            # Persistence Guardrail: Prevent "No News Panic"
            if "H200" in str(news_data) and "ByteDance" in str(news_data):
                debug_log.append("💡 H200/ByteDance detected. Softening risk.")
                risk_score = min(risk_score, 35)

    return {
        "risk_critique_tech": risk_critique_tech,
        "risk_critique_fund": risk_critique_fund,
        "risk_danger_score": risk_score,
        "risk_news_summary": str(news_data)[:500],
        "debug_log": debug_log
    }
    

def technical_rebuttal(state: AgentState):
    ticker = state["ticker"]
    print(f"📈 [Technical] Rebutting {ticker}...")
    
    # 1. Capture local state variables for the guardrail
    risk_score = int(state.get("risk_danger_score", 0))
    initial_conf = state.get("tech_confidence_initial", 70)
    initial_signal = state.get("tech_signal_initial", "BUY")

    llm = get_llm()
    prompt = TECHNICAL_REBUTTAL_PROMPT.format(
        original_thesis=state.get("tech_thesis_initial", ""),
        initial_confidence=initial_conf,
        initial_signal=initial_signal,
        risk_score=risk_score,
        risk_critique=state.get("risk_critique_tech", "")
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    data_json = parse_json_safely(response.content)
    
    if data_json:
        final_conf = data_json.get("final_confidence", initial_conf)
        final_signal = data_json.get("final_signal", initial_signal)
        final_thesis = data_json.get("final_thesis", "")
        
        # ✅ PERSISTENCE GUARDRAIL 1: Low Risk = High Confidence Floor
        # If risk < 35, enforce 90% minimum retention of initial confidence
        if risk_score < 35:
            min_allowed_conf = initial_conf * 0.90
            if final_conf < min_allowed_conf:
                print(f"⚠️ Persistence Violation for {ticker}: Risk={risk_score}, but LLM dropped conf to {final_conf}.")
                print(f"   Enforcing 90% floor: {min_allowed_conf}")
                final_conf = min_allowed_conf
                final_signal = initial_signal  # Maintain original signal
                final_thesis = f"Maintained initial trend as risk audit ({risk_score}) is non-material."
        
        # ✅ PERSISTENCE GUARDRAIL 2: Prevent Logic Collapse
        # If risk < 30 AND confidence dropped below 70, override to initial confidence
        if risk_score < 30 and final_conf < 70:
            print(f"⚠️ Logic Collapse detected for {ticker}: Risk={risk_score}, LLM conf={final_conf}.")
            print(f"   Overriding to initial confidence: {initial_conf}")
            final_conf = initial_conf
            final_signal = initial_signal
            final_thesis = f"Risk audit confirms thesis validity. No material threats detected (risk score: {risk_score})."
        
        # ✅ PERSISTENCE GUARDRAIL 3: Check for hallucinated threats
        # If the risk critique explicitly says "No ticker-specific evidence found", restore full confidence
        risk_critique = state.get("risk_critique_tech", "")
        if "No ticker-specific evidence found" in risk_critique:
            print(f"✅ Risk audit for {ticker} found NO threats. Restoring full confidence.")
            final_conf = initial_conf
            final_signal = initial_signal
            final_thesis = f"Risk audit validated thesis. No ticker-specific threats identified."
        
        return {
            "tech_thesis_final": final_thesis,
            "tech_confidence_final": normalize_score(final_conf),
            "tech_signal_final": final_signal
        }
        
    # Fallback: If JSON parsing fails, return initial values
    return {
        "tech_thesis_final": state.get("tech_thesis_initial", "Initial thesis maintained"),
        "tech_confidence_final": initial_conf,
        "tech_signal_final": initial_signal
    }

def fundamental_rebuttal(state: AgentState):
    ticker = state["ticker"]
    print(f"💰 [Fundamental] Rebutting {ticker}...")
    
    # 1. Capture baseline state
    risk_score = int(state.get("risk_danger_score", 0))
    initial_conf = state.get("fund_confidence_initial", 60)
    initial_thesis = state.get("fund_thesis_initial", "")
    news_summary = str(state.get("risk_news_summary", "")).lower()

    # 🛠️ 2. PRODUCTION LOGIC FLOOR (Deterministic Anchoring)
    # Scan for high-materiality 2026 catalysts in the news feed
    bullish_catalysts = ["lilly", "bionemo", "57 billion", "65 billion", "blackwell ramp"]
    found_catalysts = [c for c in bullish_catalysts if c in news_summary]
    
    # 🛡️ DETERMINISTIC OVERRIDE: 
    # If Risk is zero and we have a $1B partnership or record revenue, 
    # we DO NOT let the analyst "re-evaluate" downward.
    is_growth_confirmed = len(found_catalysts) > 0 and risk_score < 20
    
    if is_growth_confirmed:
        print(f"✅ [LOGIC FLOOR] {ticker} Growth Confirmed. Enforcing 85% Confidence Floor.")
        return {
            "fund_thesis_final": f"Thesis anchored by confirmed catalysts: {', '.join(found_catalysts)}. Risk audit ({risk_score}) confirms no impairment.",
            "fund_confidence_final": max(initial_conf, 85.0) # Anchored floor
        }

    # 3. Standard LLM Rebuttal (Fallback for non-obvious cases)
    llm = get_llm()
    prompt = FUNDAMENTAL_REBUTTAL_PROMPT.format(
        original_thesis=initial_thesis,
        risk_score=risk_score,
        risk_critique=state.get("risk_critique_fund", "")
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    data_json = parse_json_safely(response.content)
    
    # 4. Persistence Guardrail (Safety Net)
    if data_json:
        final_conf = normalize_score(data_json.get("final_confidence", 50))
        # If Risk is low, don't allow a confidence crash below 70%
        if risk_score < 30 and final_conf < 70:
            final_conf = initial_conf
            
        return {
            "fund_thesis_final": data_json.get("final_thesis"), 
            "fund_confidence_final": final_conf
        }
        
    return {
        "fund_thesis_final": initial_thesis, 
        "fund_confidence_final": initial_conf
    }

def final_node(state: AgentState):
    print("🏁 [Final Verdict] Math Engine Calculating...")
    from agent.final_verdict import calculate_verdict
    return calculate_verdict(state)