from typing import TypedDict, Dict, Any, List

class AgentHubState(TypedDict):
    user_idea: str
    architecture: Dict[str, Any]
    code_generated: bool
    errors: Dict[Any, Any]
    iteration_count: int
    error_history: Dict[str, List[str]]
    fix_history: Dict[str, List[str]]

