from langgraph.graph import StateGraph,START,END
from agents import generate_mcq, generate_summary
from state import GraphState

workflow = StateGraph(GraphState)
workflow.add_node("generate_mcq", generate_mcq)
workflow.add_node("generate_summary", generate_summary)
workflow.add_edge(START, "generate_summary")
workflow.add_edge(START, "generate_mcq")
workflow.add_edge("generate_mcq", END)
workflow.add_edge("generate_summary", END)

app = workflow.compile()