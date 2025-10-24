from src.graph_runner import graph

initial_state = {
    "architecture": {},
    "user_idea": "Build me a sql agent for my database",
    "code_generated": False
}

graph.invoke(initial_state)


