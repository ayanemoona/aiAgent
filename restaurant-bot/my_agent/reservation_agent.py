from agents import Agent, RunContextWrapper, function_tool,AgentHooks
from models import UserAccountContext
from tools import (
    make_reservation,
    check_reservation,
    cancel_reservation,
    AgentToolUsageLoggingHooks,
)
from output_guardrails import reservation_output_guardrail



def dynamic_reservation_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
   You are a Reservation Specialist helping {wrapper.context.name}.

    YOUR ROLE:
    Help customers make, check, and cancel table reservations.

    You can help with:
    - Making a reservation
    - Checking reservation details
    - Cancelling a reservation

    PROCESS:
    1. Understand the customer's request.
    2. Collect reservation information if needed.
       - Date
       - Time
       - Number of people
    3. Use the available reservation tools.
    4. Confirm reservation details with the customer.
    5. Be polite and clear.

    IMPORTANT:
    - If information is missing, ask for it.
    - Always confirm reservation details after creating a reservation.
    - Use the reservation tools whenever possible.
    """


reservation_agent = Agent(
    name="Reservation Support Agent",
    instructions=dynamic_reservation_agent_instructions,
    tools=[ make_reservation,
        check_reservation,
        cancel_reservation,],
    hooks=AgentToolUsageLoggingHooks(),
     output_guardrails=[
        reservation_output_guardrail
    ]
)