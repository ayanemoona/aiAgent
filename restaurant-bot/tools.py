# tools.py
import streamlit as st
from agents import function_tool, AgentHooks, Agent, Tool, RunContextWrapper
from models import UserAccountContext
import random
from datetime import datetime, timedelta


# =============================================================================
# MENU DATA
# =============================================================================

MENU_DATA = {
    "Burger": {
        "ingredients": ["Beef Patty", "Cheese", "Lettuce", "Tomato"],
        "allergens": ["Milk", "Wheat"]
    },
    "Veggie Burger": {
        "ingredients": ["Veggie Patty", "Lettuce", "Tomato"],
        "allergens": ["Wheat"]
    },
    "Caesar Salad": {
        "ingredients": ["Lettuce", "Chicken", "Parmesan Cheese"],
        "allergens": ["Milk"]
    },
    "Coke": {
        "ingredients": ["Carbonated Water", "Sugar"],
        "allergens": []
    }
}


# =============================================================================
# ORDER DATA
# =============================================================================

ORDERS = {}


# =============================================================================
# RESERVATION DATA
# =============================================================================

RESERVATIONS = {}


# =============================================================================
# MENU TOOLS
# =============================================================================

@function_tool
def get_all_menu() -> str:
    """
    Return all available menu items.
    """

    return "\n".join(MENU_DATA.keys())


@function_tool
def get_menu_info(menu_name: str) -> str:
    """
    Return menu details including ingredients and allergens.
    """

    menu = MENU_DATA.get(menu_name)

    if not menu:
        return "Menu not found."

    return f"""
Menu: {menu_name}

Ingredients:
{", ".join(menu["ingredients"])}

Allergens:
{", ".join(menu["allergens"]) if menu["allergens"] else "None"}
""".strip()


# =============================================================================
# ORDER TOOLS
# =============================================================================

@function_tool
def place_order(
    context: UserAccountContext,
    menu_name: str
) -> str:
    """
    Place an order.
    """

    if menu_name not in MENU_DATA:
        return "Menu not found."

    ORDERS[context.customer_id] = menu_name

    return f"{context.name}님의 {menu_name} 주문이 접수되었습니다."


@function_tool
def check_order(
    context: UserAccountContext
) -> str:
    """
    Check current order.
    """

    order = ORDERS.get(context.customer_id)

    if not order:
        return "현재 주문 내역이 없습니다."

    return f"현재 주문: {order}"


@function_tool
def cancel_order(
    context: UserAccountContext
) -> str:
    """
    Cancel current order.
    """

    if context.customer_id not in ORDERS:
        return "취소할 주문이 없습니다."

    del ORDERS[context.customer_id]

    return "주문이 취소되었습니다."


# =============================================================================
# RESERVATION TOOLS
# =============================================================================

@function_tool
def make_reservation(
    context: UserAccountContext,
    date: str,
    time: str,
    people: int
) -> str:
    """
    Create reservation.
    """

    RESERVATIONS[context.customer_id] = {
        "date": date,
        "time": time,
        "people": people
    }

    return (
        f"{context.name}님 예약 완료\n"
        f"날짜: {date}\n"
        f"시간: {time}\n"
        f"인원: {people}명"
    )


@function_tool
def check_reservation(
    context: UserAccountContext
) -> str:
    """
    Check reservation.
    """

    reservation = RESERVATIONS.get(context.customer_id)

    if not reservation:
        return "예약 내역이 없습니다."

    return (
        f"예약 정보\n"
        f"날짜: {reservation['date']}\n"
        f"시간: {reservation['time']}\n"
        f"인원: {reservation['people']}명"
    )


@function_tool
def cancel_reservation(
    context: UserAccountContext
) -> str:
    """
    Cancel reservation.
    """

    if context.customer_id not in RESERVATIONS:
        return "취소할 예약이 없습니다."

    del RESERVATIONS[context.customer_id]

    return "예약이 취소되었습니다."


class AgentToolUsageLoggingHooks(AgentHooks):

    async def on_tool_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** starting tool: `{tool.name}`")

    async def on_tool_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
        result: str,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** used tool: `{tool.name}`")
            st.code(result)

    async def on_handoff(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        source: Agent[UserAccountContext],
    ):
        with st.sidebar:
            st.write(f"🔄 Handoff: **{source.name}** → **{agent.name}**")

    async def on_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
    ):
        with st.sidebar:
            st.write(f"🚀 **{agent.name}** activated")

    async def on_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        output,
    ):
        with st.sidebar:
            st.write(f"🏁 **{agent.name}** completed")
            