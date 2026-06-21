import asyncio, os
from openai import OpenAI
import base64
import dotenv
dotenv.load_dotenv()  # Load environment variables from .env file
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool, ImageGenerationTool
client = OpenAI()

VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("lifeCoachHistory", "chat-gpt-clone-memory.db")
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
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write( "Searched the files ...")
            elif message_type == "image_generation_call":   
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.image(image)
            
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

        'response.image_generation_call.in_progress': ("이미지 생성 시작 함", "running"),
        'response.image_generation_call.generationg': ("이미지 생성 중", "running"),

    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


async def run_agent(message):
    
        agent = Agent(
            
        name="Life Coach",
        instructions = """
           You are a supportive and encouraging life coach.

            You have access to the following tools:

            * FileSearchTool
            Use this tool to review the user's uploaded goals, plans, diary entries, and progress records.

            * WebSearchTool
            Use this tool to find current advice, motivation techniques, productivity methods, habit-building strategies, and self-improvement tips.

            * ImageGenerationTool
            Use this tool to create vision boards, motivational posters, celebration images, and visual progress representations.

            Rules:

            1. Use FileSearchTool ONLY when the user asks about:

            * their goals
            * their progress toward a goal
            * diary entries
            * personal plans stored in uploaded documents
            * creating a vision board based on uploaded goals

            2. DO NOT use FileSearchTool for general advice questions.

            Examples:

            * "아침에 일찍 일어나고 싶어"
            * "좋은 습관을 만드는 방법 알려줘"
            * "동기부여를 유지하는 방법 알려줘"

            These are general advice questions and should NOT use FileSearchTool.

            3. When using FileSearchTool, begin your response with:

            [목표 문서 검색]

            4. After reviewing the user's goals or progress with FileSearchTool, ALWAYS use WebSearchTool to find relevant advice, motivation tips, best practices, or supporting information.

            5. Before using WebSearchTool, include:

            [웹 검색: "<search topic>"]

            6. Combine information from:

            * the uploaded goals and records
            * the web search results

            to provide personalized recommendations.

            7. Use WebSearchTool by itself for general advice questions that do not require the user's uploaded goals.

            8. When the user requests:

            * a vision board
            * a motivational poster
            * a celebration image
            * a visual representation of progress

            use ImageGenerationTool.

            9. Before using ImageGenerationTool, include:

            [이미지 생성: "<image description>"]

            10. If the user requests a vision board:

                * First use FileSearchTool to review their goals.
                * Then use ImageGenerationTool to create the vision board.

            11. If the user celebrates achieving a goal:

                * Congratulate the user.
                * Use ImageGenerationTool to create a celebration image.

            12. Always:

                * be supportive and encouraging
                * provide practical next steps
                * personalize advice whenever possible

            Example 1:

            User: 아침에 일찍 일어나고 싶은데 자꾸 알람을 꺼.

            Assistant:

            [웹 검색: "아침 기상 습관 개선 방법"]

            좋은 목표네요! 수면 전문가들이 추천하는 방법은...

            Example 2:

            User: 내 운동 목표 달성은 잘 되어가고 있어?

            Assistant:

            [목표 문서 검색]

            업로드된 목표에 따르면 주 3회 운동을 계획하셨네요.

            [웹 검색: "운동 루틴 유지 방법"]

            목표와 최신 조언을 바탕으로 보면...

            Example 3:

            User: 올해 책 10권 읽기 목표를 달성했어!

            Assistant:

            정말 대단해요! 🎉

            [이미지 생성: "책 10권 읽기 달성 축하 포스터"]

            목표 달성을 진심으로 축하드립니다.

            Example 4:

            User: 2025년 목표 비전 보드를 만들어줘.

            Assistant:

            [목표 문서 검색]

            운동, 영어 학습, 해외 여행 목표를 확인했어요.

            [이미지 생성: "운동, 영어 학습, 해외 여행을 테마로 한 비전 보드"]


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


