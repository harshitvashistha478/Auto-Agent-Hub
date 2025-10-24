from src.utils.state import AgentHubState

def error_check_router(state: AgentHubState):
    """
    Router function to determine if errors are present.
    """
    if state["errors"] == {}:
        return "testing"
    else:
        return "handle_errors"