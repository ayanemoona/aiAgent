import asyncio
from openai import OpenAI
import base64
import dotenv
dotenv.load_dotenv()  # Load environment variables from .env file
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool, ImageGenerationTool, CodeInterpreterTool
 
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
        - Code Interpreter Tool: Use this tool when you need to write and run code to answer the user's question.
        """,
    tools = [ WebSearchTool(), 
             FileSearchTool(vector_store_ids=[VECTOR_STORE_ID], max_num_results=3),
             ImageGenerationTool( tool_config = {
                    "type":"image_generation",
                    "quality":"low",
                    "output_format":"jpeg" ,
                    "moderation": "low",
                    "partial_images": 1
                 }, ),
            CodeInterpreterTool(
                tool_config={
                    "type" : "code_interpreter",
                    "container":{"type":"auto"}
                }
            ),
                 ]
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
                    content = message["content"] 
                    if isinstance(content, str):
                        st.write(message["content"])
                    elif isinstance(content, list) :
                        for part in content:
                            if "image_url" in part :
                                st.write(part["image_url"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "  \$"))
        if "type" in message :
            message_type = message["type"]
            if  message_type == "web_search_call":
                with st.chat_message("ai"):
                    st.write( "Searched the web ...")
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write( "Searched the files ...")
            elif message_type == "image_generation_call":   
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.image(image)
            elif message_type == "code_interpreter_call":
                with st.chat_message("ai"):
                    st.code(message["code"])

asyncio.run(paint_history())

def update_status(status_container, event):
    status_messages = {
        'response.web_search_call.completed': ("웹 검색 성공 ", "complete"),
        'response.web_search_call.in_progress': (" 웹 검색 시작 함", "running"),
        'response.web_search_call.searched': ("웹 검색 중", "running"),
        "response.completed" : ("성공 ", "complete"),

        'response.file_search_call.completed': ("파일 검색 성공 ", "complete"),
        'response.file_search_call.in_progress': (" 파일 검색 시작 함", "running"),
        'response.file_search_call.searched': ("파일 검색 중", "running"),

        'response.image_generation_call.in_progress': ("이미지 생성 시작 함", "running"),
        'response.image_generation_call.generationg': ("이미지 생성 중", "running"),

        'response.code_interpreter_call_code.done':("Rancode","complete"),
        'response.code_interpreter_call_code.completed':("Rancode","complete"),
        'response.code_interpreter_call_code.in_progress':("Running code", "running"),
        'response.code_interpreter_call_code.interpreting':("Running code", "running"),


    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)




async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("로딩", expanded=False)
        image_placeholder = st.empty()
        code_placeholder = st.empty()
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
                    text_placeholder.write(response.replace("$", "  \$"))

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


