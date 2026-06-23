from agents import Agent, RunContextWrapper, input_guardrail, Runner, GuardrailFunctionOutput, handoff
from models import UserAccountContext, InputGuardRailOutput, HandoffData
from my_agent.menu_agent import menu_agent
from my_agent.order_agent import order_agent
from my_agent.reservation_agent import reservation_agent
import streamlit as st
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters

input_guardrail_agent = Agent(
    name = "Input Gurdrail Agent",
    instructions = """
    Ensure the user's request is related to the restaurant.

    Allowed topics:
    - Menu information
    - Ingredients
    - Allergens and dietary restrictions
    - Placing, modifying, or checking orders
    - Table reservations
    - Restaurant operating hours and policies

    If the request is unrelated to the restaurant, return a reason explaining why it is off-topic.

    Small talk and greetings are allowed, especially at the beginning of the conversation.

    Do not assist with requests unrelated to the restaurant.
 """,
 output_type=InputGuardRailOutput,
)

@input_guardrail
async def off_topic_guardrail(wrapper : RunContextWrapper[UserAccountContext],
        agent : Agent[UserAccountContext], input:str):
    result = await Runner.run(input_guardrail_agent, input, context = wrapper.context)
    return GuardrailFunctionOutput(output_info = result.final_output, tripwire_triggered=result.final_output.is_off_topic)

def dynamic_triage_agent_instructions(
        wrapper : RunContextWrapper[UserAccountContext],
        agent : Agent[UserAccountContext]):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

    You are a restaurant customer support agent.

    You ONLY help customers with questions related to:
    - Menu information
    - Orders
    - Reservations

    Always address customers by their name.

    The customer's name is {wrapper.context.name}.
    The customer's email is {wrapper.context.email}.

    YOUR MAIN JOB:
    Classify the customer's request and route them to the correct specialist agent.

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
    4. Explain why you are routing them.
    5. Route the request to the appropriate specialist agent.

    SPECIAL HANDLING:
    - Multiple issues: Handle the most urgent issue first and note any additional issues.
    - Unclear requests: Ask 1-2 clarifying questions before routing.

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
    input_guardrails=[off_topic_guardrail,],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ]
)