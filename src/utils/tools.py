from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from src.llm.llms import codegen_llm
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os


load_dotenv()


def setup_search_tools():
    """Initialize search tools for the agent"""
    tools = []
    
    # Try to add Tavily (better for technical content)
    try:
        tavily_search = TavilySearchResults(
            api_key=os.getenv("TAVILY_API_KEY"),
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )
        tools.append(tavily_search)
        print("✅ Tavily search tool loaded")
    except Exception as e:
        print(f"⚠️  Tavily not available: {e}")
    
    # Add DuckDuckGo as fallback
    try:
        ddg_search = DuckDuckGoSearchRun()
        tools.append(ddg_search)
        print("✅ DuckDuckGo search tool loaded")
    except Exception as e:
        print(f"⚠️  DuckDuckGo not available: {e}")
    
    return tools


def create_error_fixing_agent():
    """Creates a ReAct agent with search tools for fixing errors"""
    
    tools = setup_search_tools()
    
    system_prompt = """You are an expert code fixer with access to web search tools.

Your task is to fix code errors by:
1. Analyzing the error carefully
2. Searching the web for solutions when needed (use search tools!)
3. Applying the fix with minimal changes
4. Ensuring the code remains functional

WHEN TO USE SEARCH TOOLS:
- For library-specific errors (import errors, API changes)
- For unfamiliar error messages
- To find best practices for specific frameworks
- To verify syntax or API usage
- For security vulnerabilities

SEARCH STRATEGY:
- Search for: "[error message] [language/framework] solution"
- Look for Stack Overflow, GitHub issues, official docs
- Prioritize recent solutions (check dates)

FIXING GUIDELINES:
1. Make MINIMAL changes - don't refactor
2. Add missing imports at the top
3. Fix syntax errors precisely
4. Preserve original logic and structure
5. Add error handling only if needed for the specific error
6. Test your mental model: will this code run?

IMPORTANT:
- Return ONLY the fixed code, no explanations
- Don't wrap in markdown code blocks
- Keep all comments and docstrings
- Don't change working functionality"""
    
    # Create the agent with tools
    agent = create_react_agent(
        model=codegen_llm,
        tools=tools,
        prompt=system_prompt
    )
    
    return agent