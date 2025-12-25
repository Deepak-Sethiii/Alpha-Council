# agents/nodes.py
import json
import os
import sys
import subprocess
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState
from agents.prompts import (
    TECHNICAL_INITIAL_PROMPT, TECHNICAL_REBUTTAL_PROMPT,
    FUNDAMENTAL_INITIAL_PROMPT, FUNDAMENTAL_REBUTTAL_PROMPT,
    RISK_CRITIQUE_PROMPT, get_current_date
)

# --- 1. SETUP LLM (Groq Only) ---
def get_llm():
    # Ensure GROQ_API_KEY is in your .env file
    # You can change the model name if needed (e.g., "llama3-70b-8192")
    return ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)

# --- 2. THE BRIDGE (Synchronous MCP Tool Call) ---
def call_mcp_tool(tool_name, arguments):
    """
    Manually calls the finance_server.py script to get data.
    """
    # Point to the server file relative to the root
    server_path = os.path.join("nexus", "servers", "finance_server.py")
    cmd = [sys.executable, server_path]
    
    # JSON-RPC Request
    request = {
        "jsonrpc": "2.0", 
        "id": 1, 
        "method": "tools/call", 
        "params": {"name": tool_name, "arguments": arguments}
    }
    
    # Setup Env
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        # Run subprocess
        process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env, encoding='utf-8'
        )
        stdout, stderr = process.communicate(input=json.dumps(request) + "\n")
        
        if stdout:
            response = json.loads(stdout)
            if "result" in response:
                return response["result"]["content"][0]["text"]
            else:
                return f"MCP Error: {response}"
        else:
            return f"Connection Error: {stderr}"
    except Exception as e:
        return f"Execution Failed: {str(e)}"

# --- 3. THE AGENT NODES (Matched to graph.py) ---

def technical_analyst(state: AgentState):
    ticker = state["ticker"]
    print(f"\n📈 [Technical] Analyzing {ticker}...")
    
    # 1. Get Data
    data = call_mcp_tool("analyze_stock", {"ticker": ticker})
    
    # 2. Think
    llm = get_llm()
    prompt = TECHNICAL_INITIAL_PROMPT.format(current_date=get_current_date(), ticker=ticker)
    messages = [SystemMessage(content=prompt), HumanMessage(content=f"Data: {data}")]
    response = llm.invoke(messages)
    
    # 3. Parse JSON
    try:
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
    except:
        result = {"thesis": response.content, "confidence": 50}

    return {
        "tech_thesis_initial": result.get("thesis"),
        "tech_confidence_initial": result.get("confidence", 50)
    }

def fundamental_analyst(state: AgentState):
    ticker = state["ticker"]
    print(f"💰 [Fundamental] Analyzing {ticker}...")
    
    data = call_mcp_tool("get_fundamentals", {"ticker": ticker})
    
    llm = get_llm()
    prompt = FUNDAMENTAL_INITIAL_PROMPT.format(current_date=get_current_date(), ticker=ticker)
    messages = [SystemMessage(content=prompt), HumanMessage(content=f"Data: {data}")]
    response = llm.invoke(messages)
    
    try:
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
    except:
        result = {"thesis": response.content, "confidence": 50}

    return {
        "fund_thesis_initial": result.get("thesis"),
        "fund_confidence_initial": result.get("confidence", 50)
    }

def risk_manager(state: AgentState):
    ticker = state["ticker"]
    print(f"🚨 [Risk] Critiquing {ticker}...")
    
    news = call_mcp_tool("search_news", {"query": ticker})
    
    llm = get_llm()
    prompt = RISK_CRITIQUE_PROMPT.format(
        current_date=get_current_date(), 
        tech_thesis=state["tech_thesis_initial"],
        fund_thesis=state["fund_thesis_initial"],
        ticker=ticker
    )
    messages = [SystemMessage(content=prompt), HumanMessage(content=f"News: {news}")]
    response = llm.invoke(messages)
    
    try:
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
    except:
        result = {"risk_critique_tech": "None", "risk_critique_fund": "None", "risk_score": 50}

    return {
        "risk_critique_tech": result.get("risk_critique_tech"),
        "risk_critique_fund": result.get("risk_critique_fund"),
        "risk_danger_score": result.get("risk_score", 50)
    }

def technical_rebuttal(state: AgentState):
    print("📈 [Technical] Rebutting...")
    llm = get_llm()
    prompt = TECHNICAL_REBUTTAL_PROMPT.format(risk_critique=state["risk_critique_tech"])
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Original: {state['tech_thesis_initial']}")
    ]
    response = llm.invoke(messages)
    return {
        "tech_thesis_final": response.content,
        "tech_confidence_final": state["tech_confidence_initial"]
    }

def fundamental_rebuttal(state: AgentState):
    print("💰 [Fundamental] Rebutting...")
    llm = get_llm()
    prompt = FUNDAMENTAL_REBUTTAL_PROMPT.format(risk_critique=state["risk_critique_fund"])
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Original: {state['fund_thesis_initial']}")
    ]
    response = llm.invoke(messages)
    return {
        "fund_thesis_final": response.content,
        "fund_confidence_final": state["fund_confidence_initial"]
    }

def final_node(state: AgentState):
    # Calls your Math Engine
    from agents.final_verdict import calculate_verdict
    return calculate_verdict(state)