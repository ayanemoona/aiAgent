from agents import Agent, RunContextWrapper, function_tool,AgentHooks
from models import UserAccountContext
from tools import (
    place_order,
    check_order,
    cancel_order,
    AgentToolUsageLoggingHooks,
)
from output_guardrails import order_output_guardrail


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    You are an Order Specialist helping {wrapper.context.name}.

    YOUR ROLE:
    Help customers place, check, and cancel orders.

    You can help with:
    - Placing an order
    - Checking order status
    - Cancelling an order

    PROCESS:
    1. Understand the customer's request.
    2. Ask follow-up questions if information is missing.
    3. Use the available tools to manage orders.
    4. Confirm the result with the customer.
    5. Be polite and clear.

    IMPORTANT:
    - If the customer wants to order food, use the order tools.
    - If the customer wants to check an order, use the order tools.
    - If the customer wants to cancel an order, use the order tools.
    """


order_agent = Agent(
    name="Order Agent",
    instructions=dynamic_order_agent_instructions,
    tools=[place_order,
    check_order,
    cancel_order,],
    hooks=AgentToolUsageLoggingHooks(),
    output_guardrails=[
        order_output_guardrail
    ],
)