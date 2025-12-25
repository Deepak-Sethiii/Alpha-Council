# agents/graph.py

from langgraph.graph import StateGraph, END
from agent.state import AgentState

# Import the nodes (The brains Teammate B built/stubbed)
# If this line errors, it means Teammate B hasn't named their functions exactly like this!
from agent.nodes import (
    technical_analyst, 
    fundamental_analyst, 
    risk_manager, 
    technical_rebuttal, 
    fundamental_rebuttal, 
    final_node
)

# 1. Initialize the Graph (The Board)
workflow = StateGraph(AgentState)

# 2. Add the Nodes (The Workers)
# We give each node a name (e.g., "technical_analyst") and connect it to a function
workflow.add_node("technical_analyst", technical_analyst)
workflow.add_node("fundamental_analyst", fundamental_analyst)
workflow.add_node("risk_manager", risk_manager)
workflow.add_node("technical_rebuttal", technical_rebuttal)
workflow.add_node("fundamental_rebuttal", fundamental_rebuttal)
workflow.add_node("final_node", final_node)

# 3. Define the Edges (The Assembly Line)
# Start here:
workflow.set_entry_point("technical_analyst")

# The path:
workflow.add_edge("technical_analyst", "fundamental_analyst")
workflow.add_edge("fundamental_analyst", "risk_manager")
workflow.add_edge("risk_manager", "technical_rebuttal")
workflow.add_edge("technical_rebuttal", "fundamental_rebuttal")
workflow.add_edge("fundamental_rebuttal", "final_node")

# End here:
workflow.add_edge("final_node", END)

# 4. Compile the Application
app = workflow.compile()