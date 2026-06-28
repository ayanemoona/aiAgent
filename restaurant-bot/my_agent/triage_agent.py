from agents import Agent, RunContextWrapper, input_guardrail, Runner, GuardrailFunctionOutput, handoff, AgentHooks
from models import UserAccountContext, InputGuardRailOutput, HandoffData
from my_agent.menu_agent import menu_agent
from my_agent.order_agent import order_agent
from my_agent.reservation_agent import reservation_agent
import streamlit as st
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from input_guardrails import restaurant_input_guardrail


@input_guardrail
async def off_topic_guardrail(wrapper : RunContextWrapper[UserAccountContext],
        agent : Agent[UserAccountContext], input:str):
    result = await Runner.run(restaurant_input_guardrail, input, context = wrapper.context)
    return GuardrailFunctionOutput(output_info = result.final_output, tripwire_triggered=result.final_output.is_off_topic)

def dynamic_triage_agent_instructions(
        wrapper : RunContextWrapper[UserAccountContext],
        agent : Agent[UserAccountContext]):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

    You are a restaurant triage agent.

    Your only responsibility is to classify restaurant-related requests
    and route them to the appropriate specialist agent.

    Do not attempt to solve customer requests yourself.

    You route customer requests related to:
    - Menu information
    - Orders
    - Reservations

    Always classify based on the customer's intent, not only on keywords.
    Always address customers by their name.
    Use the customer's name and email from the context whenever possible.
    Do not ask for information already available.

    The customer's name is {wrapper.context.name}.
    The customer's email is {wrapper.context.email}.

    YOUR MAIN JOB:

    1. Understand the customer's request.
    2. Determine the customer's primary intent.
    3. Ask one clarifying question if necessary.
    4. Route the request to ONE specialist agent.
    5. Do not solve the request yourself.

    ISSUE CLASSIFICATION GUIDE:

    🍔 MENU AGENT - Route here for:
    - Menu items
    - Ingredients used in menu items
    - Allergens related to ingredients
    - Dietary restrictions
    - Questions about food and drinks

    📦 ORDER AGENT - Route here for:
    - Placing an order
    - Order confirmation
    - Order status
    - Order modification
    - Order cancellation

    🪑 RESERVATION AGENT - Route here for:
    - Making a reservation
    - Checking a reservation
    - Modifying a reservation
    - Cancelling a reservation

    CLASSIFICATION PROCESS:
    1. Listen to the customer's request.
    2. Ask clarifying questions if the category is unclear.
    3. Classify the request into ONE of the three categories above.
    4. Briefly explain the routing decision in one sentence.
    5. Route the request to the appropriate specialist agent.

    SPECIAL HANDLING:
    - Multiple issues: Handle the most urgent issue first and note any additional issues.
        Never route to multiple specialist agents at the same time.
    - Unclear requests: Ask one short clarifying question before routing.
        Do not guess the customer's intent.

    """

def hadle_handoff(wrapper : RunContextWrapper[UserAccountContext], input_data: HandoffData):
    with st.sidebar:
        
        st.write(f"""
                Handing off to {input_data.to_agent_name}
                 Reason: {input_data.reason}
                 Issue Type : {input_data.issue_type}
                 Description : {input_data.issue_description}
                """)

def make_handoff(agent):
    return handoff(
            agent = agent,
            on_handoff = hadle_handoff,
            input_type = HandoffData,
            input_filter =  handoff_filters.remove_all_tools
        )

triage_agent = Agent(
    name = "Trage Agent",
    instructions = dynamic_triage_agent_instructions,
    input_guardrails=[restaurant_input_guardrail],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ],
)