from agents import Agent, RunContextWrapper, function_tool, AgentHooks
from models import UserAccountContext
from tools import (
    get_all_menu,
    get_menu_info,
    AgentToolUsageLoggingHooks,
)



def dynamic_menu_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    You are a Menu Specialist helping {wrapper.context.name}.

    YOUR ROLE:
    Help customers with menu-related questions.

    You can help with:
    - Available menu items
    - Ingredients used in menu items
    - Allergen information
    - Dietary restrictions
    - Food recommendations

    PROCESS:
    1. Understand the customer's question.
    2. Use the menu tool when menu information is needed.
    3. Explain ingredients clearly.
    4. Inform customers about allergens.
    5. Recommend menu items when appropriate.
    """


menu_agent = Agent(
    name="Menu Support Agent",
    instructions=dynamic_menu_agent_instructions,
    tools=[get_all_menu,
    get_menu_info,],
    hooks=AgentToolUsageLoggingHooks(),
)