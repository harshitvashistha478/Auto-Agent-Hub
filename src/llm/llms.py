from langchain_groq import ChatGroq
from dotenv import load_dotenv
from src.structured_models.architecture import ArchitectureStructuredModel
import os

load_dotenv()

supervisor_llm = ChatGroq(
    model=os.getenv("SUPERVISOR_AGENT"),
    api_key=os.getenv("GROQ_API_KEY")
)


architecture_llm = supervisor_llm.with_structured_output(ArchitectureStructuredModel)


codegen_llm = ChatGroq(
    model=os.getenv("CODEGEN_AGENT"),   
    api_key=os.getenv("GROQ_API_KEY")
)


error_analysis_llm = ChatGroq(
    model=os.getenv("ERROR_ANALYSIS_AGENT"),
    api_key=os.getenv("GROQ_API_KEY")
)