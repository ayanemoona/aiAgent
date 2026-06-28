from agents import Agent, output_guardrail, Runner, RunContextWrapper, GuardrailFunctionOutput
from models import AgentOutputGuardrail, UserAccountContext

menu_output_guardrail_agent = Agent(
    name="Menu Output Guardrail",
    instructions="""
Analyze the Menu Agent response.

Determine whether the response contains:

- Menu information
- Order information
- Reservation information

Set:

contains_menu_data
contains_order_data
contains_reservation_data

to true or false.

The Menu Agent is allowed to answer ONLY menu-related questions.

If it includes order or reservation information,
set the corresponding field to true.

Normal greetings and polite conversation are allowed.
""",
    output_type=AgentOutputGuardrail,
)


@output_guardrail
async def menu_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        menu_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    triggered = (
    validation.contains_order_data
    or validation.contains_reservation_data
)

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )

order_output_guardrail_agent = Agent(
    name="Order Output Guardrail",
    instructions="""
Analyze the Order Agent response.

Determine whether the response contains:

- Menu information
- Order information
- Reservation information

Set:

contains_menu_data
contains_order_data
contains_reservation_data

to true or false.

The Order Agent is allowed to answer ONLY order-related questions.
""",
    output_type=AgentOutputGuardrail,
)
@output_guardrail
async def order_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        order_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    triggered = (
    validation.contains_menu_data
    or validation.contains_reservation_data
)

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )

reservation_output_guardrail_agent = Agent(
    name="Reservation Output Guardrail",
    instructions="""
Analyze the Reservation Agent response.

Determine whether the response contains:

- Menu information
- Order information
- Reservation information

Set:

contains_menu_data
contains_order_data
contains_reservation_data

to true or false.

The Reservation Agent is allowed to answer ONLY reservation-related questions.
""",
    output_type=AgentOutputGuardrail,
)
@output_guardrail
async def reservation_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        reservation_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    triggered = (
    validation.contains_menu_data
    or validation.contains_order_data
)


    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )