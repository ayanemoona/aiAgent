from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from .sub_agents.data_analyst import data_analyst
from .sub_agents.financial_analyst import financial_analyst
from .sub_agents.news_analyst import news_analyst   
from .prompt import PROMPT

MODEL = LiteLlm("openai/gpt-4o")

def get_weather(city:str):
    return f"The weather in {city} is 30degrees."

def conver_units(degrees:int):
    return f"That is 40 farenheit"

def save_advice_report():
    pass

financial_advisor = Agent(
    name="FinancialAdvisor",
    instruction = PROMPT,
    model= MODEL,
    tools=[
        AgentTool(agent = financial_analyst),
        AgentTool(agent = data_analyst),
        AgentTool(agent = news_analyst),
        save_advice_report,
    ]

)
root_agent = financial_advisor