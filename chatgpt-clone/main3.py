import asyncio
from openai import OpenAI
import dotenv
dotenv.load_dotenv()  # Load environment variables from .env file
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

client = OpenAI()

VECTOR_STORE_ID = "vs_6a32d758ade481919396c8fc95061bf3"

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
    name="ChatGPT Clone",
    instructions = """
        You are a helpful assistant. 

        You have access to the following tools:
        - WebSearchTool: Use this when the user asks a question that isn't in your training data. Use this tool when the users asks about current or future events, when you thing you don't know the answer, try searching tor it in the web first.
        - FileSearchTool: Use this tool when the user asks a question about facts related to themselves. Or when they ask question about specific files
    """,
    tools = [WebSearchTool(), FileSearchTool(vector_store_ids=[VECTOR_STORE_ID], max_num_results=3)],
    )
agent = st.session_state["agent"]
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")
session = st.session_state["session"]


async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message and message["type"] == "web_search_call":
            with st.chat_message("ai"):
                st.write( "Searched the web ...")

def update_status(status_container, event):
    status_messages = {
        'response.web_search_call.completed': ("웹 검색 성공 ", "complete"),
        'response.web_search_call.in_progress': (" 웹 검색 시작 함", "running"),
        'response.web_search_call.searched': ("웹 검색 중", "running"),
        "response.completed" : ("성공 ", "complete"),

        'response.file_search_call.completed': ("파일 검색 성공 ", "complete"),
        'response.file_search_call.in_progress': (" 파일 검색 시작 함", "running"),
        'response.file_search_call.searched': ("파일 검색 중", "running"),

    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


asyncio.run(paint_history())

async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("로딩", expanded=False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
        )

        async for event in stream.stream_events():
            if event.type == "raw_response_event":

                update_status(status_container, event.data.type)
                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response )




prompt = st.chat_input("Write a message for your assistant", accept_file = True, file_type=["txt"])
if prompt:
    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("uploading file ...") as status:
                    upload_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose = "user_data"
                    )
                    status.update(label="Attaching file...")
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=upload_file.id,
                    )
                    status.update(label="File uploaded", state="complete")

    if prompt.text:
        with st.chat_message("user"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))



with st.sidebar:
    reset = st.button("Reset Memory")
    if reset :
        asyncio.run(session.clear_session())
    st.write(asyncio.run( session.get_items()))


