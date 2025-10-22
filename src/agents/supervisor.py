from src.llm.supervisor_llms import structured_supervisor_llm
from src.prompts.supervisor_prompt import return_supervisor_prompt


user_input = "Build an agent that reviews and refactors code repeatedly until it reaches high quality."
structured_supervisor_llm.invoke(return_supervisor_prompt(user_input))