from agents import Agent, output_guardrail, Runner, RunContextWrapper, GuardrailFunctionOutput, input_guardrail
from models import InputGuardRailOutput, UserAccountContext

input_guardrail_agent = Agent(
    name="Restaurant input Guardrail",
    instructions="""

    You are an input guardrail for a restaurant AI assistant.

    Your only task is to determine whether the customer's request is related to restaurant services.

    Do not answer the customer's question.
    Analyze the customer's request.
    Determine whether the customer's request
    is related to restaurant services.
    Restaurant-related requests include:

    - Menu questions
    - Food ingredients
    - Allergens
    - Dietary restrictions
    - Food recommendations
    - Orders
    - Reservations
    - Restaurant location
    - Business hours
    - Parking information
    - Contact information
    - General restaurant inquiries

    If the request is unrelated to restaurant services,
    set is_off_topic to true.

    Otherwise set is_off_topic to false.

    Provide a short reason explaining your decision.

    Examples:

    Restaurant reservation request
    → is_off_topic = false

    Menu question
    → is_off_topic = false

    Weather question
    → is_off_topic = true

    Programming question
    → is_off_topic = true
    """,
    output_type=InputGuardRailOutput,
)

@input_guardrail
async def restaurant_input_guardrail(
     wrapper : RunContextWrapper[UserAccountContext],
     agent:Agent,
     user_input:str
):
    result = await Runner.run (
        input_guardrail_agent,
        user_input,
        context= wrapper.context
    )

    validation = result.final_output
    triggered = (validation.is_off_topic)

    return GuardrailFunctionOutput(
        output_info = validation,
        tripwire_triggered = triggered,
    )