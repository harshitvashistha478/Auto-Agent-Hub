from langchain_groq import ChatGroq
from dotenv import load_dotenv
from src.structured_models.supervisor_structured_model import SupervisorStructuredModel
import os

load_dotenv()

supervisor_llm = ChatGroq(
    model=os.getenv("SUPERVISOR_AGENT"),
    api_key=os.getenv("GROQ_API_KEY")
)


structured_supervisor_llm = supervisor_llm.with_structured_output(SupervisorStructuredModel)