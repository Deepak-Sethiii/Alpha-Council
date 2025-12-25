# agent/nodes.py
import json
import os
import sys
import subprocess
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from agent.utils import get_current_date, get_news_cutoff_date
from agent.prompts import (
    TECHNICAL_INITIAL_PROMPT, TECHNICAL_REBUTTAL_PROMPT,
    FUNDAMENTAL_INITIAL_PROMPT, FUNDAMENTAL_REBUTTAL_PROMPT,
    RISK_CRITIQUE_PROMPT
)

# --- 1. SETUP LLM ---
def get_llm():
    return ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.0)

# --- 2. MCP TOOL CALL ---
def call_mcp_tool(tool_name, arguments):
    server_path = os.path.join("nexus", "servers", "finance_server.py")
    cmd = [sys.executable, server_path]
    
    init_req = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize", 
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "alpha", "version": "1.0"}}
    }
    init_not = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    tool_req = {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call", 
        "params": {"name": tool_name, "arguments": arguments}
    }
    
    payload = json.dumps(init_req) + "\n" + json.dumps(init_not) + "\n" + json.dumps(tool_req) + "\n"
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env, encoding='utf-8'
        )
        stdout, stderr = process.communicate(input=payload)
        
        if stdout:
            for line in stdout.strip().split("\n"):
                try:
                    resp = json.loads(line)
                    if resp.get("id") == 2:
                        if "error" in resp: return f"Error: {resp['error']}"
                        if "result" in resp: return resp["result"]["content"][0]["text"]
                except: continue
            return "No response."
        return f"Error: {stderr}"
    except Exception as e:
        return f"Failed: {str(e)}"

# --- HELPER: SCORE NORMALIZER ---
def normalize_score(val):
    try:
        f = float(val)
        if 0 < f <= 1.0: return f * 100.0
        if f <= 0: return 50.0
        if f > 100: return 100.0
        return f
    except:
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

def risk_manager(state: AgentState):
    ticker = state["ticker"]
    print(f"🚨 [Risk] Critiquing {ticker}...")
    
    news = call_mcp_tool("search_news", {"query": f"{ticker} risks"})
    llm = get_llm()
    
    prompt = RISK_CRITIQUE_PROMPT.format(
        ticker=ticker,
        current_date=get_current_date(),
        news_cutoff_date=get_news_cutoff_date(),
        tech_thesis=state.get("tech_thesis_initial", ""),
        fund_thesis=state.get("fund_thesis_initial", ""),
        news=news
    )
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Assess risks for {ticker}.")
    ]
    response = llm.invoke(messages)
    
    data_json = parse_json_safely(response.content)
    if data_json:
        score = normalize_score(data_json.get("risk_score", 50))
        # --- KEY FIX HERE ---
        # We now grab "risk_critique_tech" which matches the Prompt exactly
        return {
            "risk_critique_tech": data_json.get("risk_critique_tech", "None"),
            "risk_critique_fund": data_json.get("risk_critique_fund", "None"),
            "risk_danger_score": score
        }
    else:
        print(f"⚠️ Risk Parsing Failed. Output: {response.content[:50]}...")
        return {
            "risk_critique_tech": "Error parsing risk.",
            "risk_critique_fund": "Error parsing risk.",
            "risk_danger_score": 50.0
        }

def technical_rebuttal(state: AgentState):
    print("📈 [Technical] Rebutting...")
    llm = get_llm()
    prompt = TECHNICAL_REBUTTAL_PROMPT.format(
        original_thesis=state.get("tech_thesis_initial", ""),
        risk_score=int(state.get("risk_danger_score", 50)),
        risk_critique=state.get("risk_critique_tech", "")
    )
    response = llm.invoke([SystemMessage(content=prompt)])
    
    data_json = parse_json_safely(response.content)
    if data_json:
        return {
            "tech_thesis_final": data_json.get("final_thesis"), 
            "tech_confidence_final": normalize_score(data_json.get("final_confidence", 50))
        }
    return {
        "tech_thesis_final": response.content, 
        "tech_confidence_final": state.get("tech_confidence_initial", 50)
    }

def fundamental_rebuttal(state: AgentState):
    print("💰 [Fundamental] Rebutting...")
    llm = get_llm()
    prompt = FUNDAMENTAL_REBUTTAL_PROMPT.format(
        original_thesis=state.get("fund_thesis_initial", ""),
        risk_score=int(state.get("risk_danger_score", 50)),
        risk_critique=state.get("risk_critique_fund", "")
    )
    response = llm.invoke([SystemMessage(content=prompt)])
    
    data_json = parse_json_safely(response.content)
    if data_json:
        return {
            "fund_thesis_final": data_json.get("final_thesis"), 
            "fund_confidence_final": normalize_score(data_json.get("final_confidence", 50))
        }
    return {
        "fund_thesis_final": response.content, 
        "fund_confidence_final": state.get("fund_confidence_initial", 50)
    }

def final_node(state: AgentState):
    print("🏁 [Final Verdict] Math Engine Calculating...")
    from agent.final_verdict import calculate_verdict
    return calculate_verdict(state)