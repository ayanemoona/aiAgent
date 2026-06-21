import asyncio, os
from openai import OpenAI
import base64
import dotenv
dotenv.load_dotenv()  # Load environment variables from .env file
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, function_tool, FileSearchTool
client = OpenAI()

VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("life-coach-history", "chat-gpt-clone-memory.db")
session = st.session_state["session"]


async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    content = message["content"] 
                    if isinstance(content, str):
                        st.write(message["content"])
                    elif isinstance(content, list) :
                        for part in content:
                            if "image_url" in part :
                                st.write(part["image_url"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\\$"))
        if "type" in message :
            message_type = message["type"]
            if  message_type == "web_search_call":
                with st.chat_message("ai"):
                    st.write( "Searched the web ...")
            
asyncio.run(paint_history())

def update_status(status_container, event):
    status_messages = {
        'response.web_search_call.completed': ("웹 검색 성공 ", "complete"),
        'response.web_search_call.in_progress': (" 웹 검색 시작 함", "running"),
        'response.web_search_call.searched': ("웹 검색 중", "running"),
        "response.completed" : ("성공 ", "complete"),

        'response.file_search_call.completed': ("[목표 문서 검색]", "complete"),
        'response.file_search_call.in_progress': (" 파일 검색 시작 함", "running"),
        'response.file_search_call.searched': ("파일 검색 중", "running"),

    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


async def run_agent(message):
    
        agent = Agent(
            
        name="Life Coach",
        instructions = """
           You are a supportive and encouraging life coach.

            Available tools:

            - FileSearchTool:
            Use this when the user asks about their goals,
            diary entries, progress, or personal records.

            - WebSearchTool:
            Use this when you need current advice,
            motivation tips, productivity methods,
            or habit-building techniques.

            Rules:

            1. If the user asks about goals, progress,
            diary entries, or personal plans,
            first use FileSearchTool.

            2. Begin your response with:

            [목표 문서 검색]

            3. Summarize the relevant goals found.

            4. Then ALWAYS use WebSearchTool
            to find related advice, motivation tips,
            or best practices.

            5. Before using WebSearchTool,
            include:

            [웹 검색: "<search topic>"]

            6. Combine information from the user's goals
            and web search results to provide
            personalized recommendations.

            7. Always be supportive and encouraging.

            Example:

            [목표 문서 검색]

            업로드된 목표에 따르면
            주 3회 운동을 계획하셨네요.

            [웹 검색: "운동 루틴 유지 방법"]

            목표와 최신 조언을 바탕으로 보면...
                        """,
        tools = [ WebSearchTool(), 
                 FileSearchTool(vector_store_ids=[VECTOR_STORE_ID], max_num_results=3),
                    ]
        )

        with st.chat_message("ai"):
            status_container = st.status("⏳", expanded=False)
            code_placeholder = st.empty()
            image_placeholder = st.empty()

            text_placeholder = st.empty()
            response = ""
            code_response = ""

            st.session_state["code_placeholder"] = code_placeholder
            st.session_state["image_placeholder"] = image_placeholder
            st.session_state["text_placeholder"] = text_placeholder

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
                        text_placeholder.write(response.replace("$", "\\$"))

                    if event.data.type == "response.code_interpreter_call_code.delta": 
                        code_response += event.data.delta
                        code_placeholder.code(code_response)

                    elif event.data.type == "response.image_generation_call.partial_image":
                        image = base64.b64decode(event.data.partial_image_b64)
                        image_placeholder.image(image)


prompt = st.chat_input(
    "Write a message for your assistant", 
    accept_file = True, 
    file_type=["txt","jpg","jpeg","png"])
if prompt:
    if "code_placeholder" in st.session_state:
        st.session_state["code_placeholder"].empty()  
    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty() 

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
        elif file.type.startswith("image/"):
            with st.status("uploading image ...") as status:
                file_bytes = file.getvalue()
                base64_data = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{file.type};base64,{base64_data}"
                
                asyncio.run(
                    session.add_items(
                        [
                            {
                                "role": "user",
                                "content": [{
                                    "type" : "input_image",
                                    "detail" : "auto",
                                    "image_url" : data_uri
                                }],
                                }]
                                ))
                status.update(label="Image uploaded", state="complete")
            with st.chat_message("human"):
                st.image(data_uri)

    if prompt.text:
        with st.chat_message("user"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))



with st.sidebar:
    reset = st.button("Reset Memory")
    if reset :
        asyncio.run(session.clear_session())
    st.write(asyncio.run( session.get_items()))


