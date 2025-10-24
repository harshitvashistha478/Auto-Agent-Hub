from typing import List


def architecture_prompt(user_input: str) -> str:
    return f'''
You are **LangGraph Supervisor**, an expert architect responsible for translating a user's natural language idea into a detailed LangGraph graph-level design.

GOAL: produce a **single valid JSON** that exactly matches this schema:
- summary: str
- graph_overview: {{"nodes": [{{"name": str, "description": str, "inputs": [str], "outputs": [str]}}], "edges": [{{"source": str, "target": str, "condition": Optional[str]}}]}}
- flow_description: str

NO OTHER KEYS, NO EXPLANATIONS, NO EXTRA TEXT. Output must be only the JSON object.

--- INSTRUCTIONS ---
1) Understand the user's input: "{user_input}"
   - Identify goal, required inputs, expected outputs, success criteria, and failure modes.

2) Produce nodes:
   - Each node = single logical responsibility (e.g., "Parse Intent", "Schema Introspection", "Generate Code Skeleton").
   - For each node include:
     - name (short unique label)
     - description (1–2 sentences about responsibility)
     - inputs (list of named inputs the node expects)
     - outputs (list of named outputs the node emits)
   - Avoid implementation details, frameworks, or deployment.

3) Produce edges:
   - Edges connect node names. Each edge include:
     - source, target
     - optional condition (string) describing when edge is taken (e.g., "if validation fails", "if confidence < 0.7")

4) Flow description:
   - One concise paragraph describing the end-to-end flow, including reasoning/validation steps, retries, and checkpoints.

--- ERROR-PROOFING CHECKLIST (MUST RUN BEFORE OUTPUT) ---
Before returning the JSON, run these validations internally (the supervisor should self-check and fix issues):
- The JSON contains exactly the three top-level keys: summary, graph_overview, flow_description.
- graph_overview.nodes is a non-empty array; node names are unique.
- graph_overview.edges only references node names that exist.
- No circular dependency without an explicit retry/loop node (if cycles exist, include explanation in flow_description).
- Each node lists at least one input or output where appropriate.
- Any conditional edge that implies retries must include a max retry hint in its condition text (e.g., "retry up to 3 times").
- Ensure the flow covers failure handling and validation paths (e.g., "validation -> error handler -> supervisor").
- Keep outputs stable and deterministically structured (no placeholders).
- No mention of LLM providers, libraries, infra, or deployment.

--- STYLE / OUTPUT RULES ---
- Output strictly the JSON object and nothing else.
- Strings must be JSON-safe (no newlines in keys; flow_description may contain newlines).
- Keep descriptions precise and actionable (1–3 sentences each).
- Use human-readable names for nodes (Pascal/Title Case preferred).

Now analyze the idea and output the JSON. USER IDEA: "{user_input}"
'''


def fix_errors_prompt(filename, history_context, errors_formatted, original_code) -> str:
    """Enhanced fixing prompt with better context"""
    
    return f"""
Fix the following code file.

Filename: {filename}
{history_context}

ERRORS TO FIX:
{errors_formatted}

CURRENT CODE:
```
{original_code}
```

INSTRUCTIONS:
1. For each error, decide if you need to search for a solution
2. If unfamiliar or library-specific, USE THE SEARCH TOOL
3. Apply fixes with minimal changes
4. Return ONLY the complete fixed code (no markdown, no explanations)

Think step by step:
- Analyze each error
- Search if needed (use tools!)
- Apply fix
- Verify mentally

Begin fixing"""


def codegen_prompt(architecture: dict) -> str:
    return f"""
You are an expert software engineer.

Given the following architecture description:
{architecture}

Generate production-ready Python project code following this architecture.

Return output in this **strict format**:

<file:path/to/file.py>
```python
# file content here
</file>
Include all important modules, utils, entrypoints, and a README if needed.
Do NOT add explanations or extra text — only structured file blocks.
"""


def error_analysis_prompt(filename: str, code_content: str, previous_errors: List[str] = None) -> str:
    """Enhanced prompt that considers previous errors"""
    previous_context = ""
    if previous_errors:
        previous_context = f"""
PREVIOUS ERRORS THAT WERE ATTEMPTED TO BE FIXED:
{chr(10).join([f"- {err}" for err in previous_errors])}

IMPORTANT: Check if these were actually fixed or if new errors were introduced.
"""
    
    return f"""You are an expert code reviewer. Analyze the following code file for errors, bugs, and issues.

Filename: {filename}

Code:
```
{code_content}
```

{previous_context}

Carefully analyze this code and identify ONLY REAL ERRORS:
1. Syntax errors (these are critical)
2. Import errors (missing or incorrect imports)
3. Undefined variables or functions
4. Type mismatches
5. Logic errors that will cause crashes

DO NOT report:
- Style issues or minor code smells
- Missing docstrings or comments
- TODO comments unless they indicate broken functionality
- Warnings that don't affect functionality

Be STRICT and CONSERVATIVE. Only report errors that will actually break the code.

Return your response as a JSON array of error strings. Each error should be specific with line numbers.

Example format:
[
    "Line 5: Missing import 'requests'",
    "Line 12: Variable 'user_data' is undefined",
    "Line 18: Function 'process()' is called but not defined"
]

If there are NO REAL ERRORS, return an empty array: []

IMPORTANT: Return ONLY the JSON array, nothing else."""
