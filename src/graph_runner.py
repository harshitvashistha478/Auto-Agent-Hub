from langgraph.graph import END, StateGraph
from src.utils.state import AgentHubState
from src.utils.nodes import get_architecture, generate_code, check_errors, testing, handle_errors
from src.utils.routers import error_check_router

app = StateGraph(AgentHubState)
app.add_node("get_architecture", get_architecture)
app.add_node("generate_code", generate_code)
app.add_node("check_errors", check_errors)
app.add_node("testing", testing)
app.add_node("handle_errors", handle_errors)

app.set_entry_point("get_architecture")
app.add_edge("get_architecture", "generate_code")
app.add_edge("generate_code", "check_errors")
app.add_conditional_edges(
    "check_errors",
    error_check_router,
    {
        "testing": "testing",
        "handle_errors": "handle_errors",
    },
)
app.add_edge("testing", END)
app.add_edge("handle_errors", "check_errors")

graph = app.compile()