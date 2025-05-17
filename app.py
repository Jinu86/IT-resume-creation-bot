import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 환경변수 로드 및 API 키 설정
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# GPT 모델 초기화
model = genai.GenerativeModel("gemini-1.5-pro")

# 페이지 설정
st.set_page_config(
    page_title="IT 이력서 생성 챗봇",
    page_icon="💼",
    layout="wide"
)

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.chat_history = []
    st.session_state.resume_data = {
        "basic_info": {},
        "job_info": {},
        "experience": [],
        "projects": [],
        "skills": [],
        "certificates": [],
        "summary": "",
        "style": ""
    }
    st.session_state.current_question = 0
    st.session_state.context = {
        "current_topic": None,
        "last_response": None,
        "next_action": "ask_job_title"
    }

# 진행 상태 표시
def show_progress():
    steps = ["기본 정보", "직무 확인", "경력 상세화", "프로젝트", "기술 스택", "자기소개", "스타일 선택"]
    current_step = st.session_state.step
    st.progress(current_step / len(steps))
    st.caption(f"Step {current_step}/{len(steps)}: {steps[current_step-1]}")

# GPT 응답 생성 함수
def generate_gpt_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 오류: {e}"

# 질문 목록
QUESTIONS = {
    "job_info": [
        "주로 사용하시는 백엔드 기술 스택은 무엇인가요? (예: Java, Spring, Python, Django, Node.js, Go, PHP, Ruby on Rails, 데이터베이스 등) 각 기술에 대한 숙련도를 어느 정도라고 생각하시는지도 함께 알려주시면 더 좋습니다.",
        "백엔드 개발 경험을 구체적인 프로젝트로 설명해주실 수 있나요? 프로젝트에서 맡았던 역할과 기여한 부분을 중심으로 설명해주세요.",
        "API 개발 경험이 있으신가요? 있다면 어떤 종류의 API를 개발해보셨는지 알려주세요.",
        "데이터베이스 관련 경험은 어떠신가요? 어떤 데이터베이스를 사용해보셨고, 데이터 모델링이나 쿼리 최적화 경험이 있으신지 궁금합니다.",
        "혹시 백엔드 개발과 관련된 자격증이나 수상 경력이 있으신가요?"
    ]
}

# ReAct 기반 프롬프트 생성
def create_react_prompt(user_input, context):
    # 기본 정보가 있는 경우에만 포함
    basic_info_section = ""
    if st.session_state.resume_data["basic_info"]:
        basic_info = st.session_state.resume_data["basic_info"]
        basic_info_section = f"""
        사용자의 기본 정보:
        이름: {basic_info.get('name', '')}
        이메일: {basic_info.get('email', '')}
        전화번호: {basic_info.get('phone', '')}
        포트폴리오: {basic_info.get('portfolio', '')}
        """

    return f"""
    당신은 IT 이력서 작성을 도와주는 친절한 챗봇입니다. 사용자의 경험과 역량을 자연스럽게 파악하고 이력서를 작성해주세요.

    {basic_info_section}

    현재 상황:
    - 단계: {st.session_state.step}
    - 현재 주제: {context['current_topic']}
    - 마지막 응답: {context['last_response']}
    - 다음 행동: {context['next_action']}

    사용자 입력: "{user_input}"

    대화 규칙:
    - 항상 친절하고 자연스러운 말투를 사용하세요.
    - 한 번에 하나의 질문만 하세요.
    - 사용자의 답변을 바탕으로 자연스럽게 다음 질문으로 이어가세요.
    - IT 직무에 관련된 전문적인 내용을 다루되, 이해하기 쉽게 설명하세요.
    - 사용자의 답변이 불충분하다면, 구체적인 예시를 들어 추가 질문을 하세요.

    이력서 작성 가이드라인:
    - STAR 방식(상황, 과제, 행동, 결과)을 따르세요.
    - 구체적인 수치와 성과를 포함하도록 유도하세요.
    - 기술 스택과 경험을 명확하게 파악하세요.
    - 프로젝트의 규모와 기간을 확인하세요.

    내부 처리 과정:
    1. 현재 상황을 분석하고 다음 단계를 결정하세요.
    2. 결정된 단계에 따라 자연스러운 대화를 이어가세요.
    3. 사용자의 응답을 관찰하고 다음 단계를 계획하세요.

    다음 응답을 생성해주세요:
    """

# 기본 정보 입력 폼
def show_basic_info_form():
    with st.form("basic_info_form"):
        st.subheader("기본 정보를 입력해주세요")
        
        # 필수 입력 필드
        name = st.text_input(
            "이름 *",
            help="한글 또는 영문으로 입력해주세요",
            placeholder="홍길동"
        )
        email = st.text_input(
            "이메일 *",
            help="이력서에 표시될 이메일 주소를 입력해주세요",
            placeholder="example@email.com"
        )
        
        # 선택 입력 필드
        phone = st.text_input(
            "전화번호",
            help="선택사항입니다",
            placeholder="010-0000-0000"
        )
        portfolio = st.text_input(
            "포트폴리오 링크",
            help="GitHub, 블로그 등",
            placeholder="https://github.com/username"
        )
        
        submitted = st.form_submit_button("다음으로")

        if submitted:
            if not name or not email:
                st.error("이름과 이메일은 필수 입력 항목입니다.")
                return False
            
            # 이메일 형식 검증
            if "@" not in email or "." not in email:
                st.error("올바른 이메일 형식이 아닙니다.")
                return False
            
            # 전화번호 형식 검증 (입력된 경우)
            if phone and not phone.replace("-", "").isdigit():
                st.error("올바른 전화번호 형식이 아닙니다.")
                return False
            
            st.session_state.resume_data["basic_info"] = {
                "name": name,
                "email": email,
                "phone": phone,
                "portfolio": portfolio
            }
            st.session_state.step = 2
            return True
    
    return False

# 메인 앱
def main():
    st.title("💼 IT 직무 이력서 생성 챗봇")
    show_progress()

    # Step 1: 기본 정보 입력 (폼 기반)
    if st.session_state.step == 1:
        if show_basic_info_form():
            st.rerun()

    # Step 2 이후: 챗봇 기반 흐름
    else:
        # 챗봇 환영 메시지
        if not st.session_state.chat_history:
            intro = f"""안녕하세요 {st.session_state.resume_data['basic_info']['name']}님! 이제부터 IT 이력서를 작성해드릴게요.

먼저, 어떤 직무에 지원하실 예정인가요?
예시) `백엔드 개발자, DevOps 엔지니어`

위 예시 중에서 선택하시거나, 다른 직무를 말씀해 주셔도 됩니다."""
            st.session_state.chat_history.append(("🤖", intro))
            st.session_state.context["next_action"] = "ask_job_title"

        # 대화 출력
        for sender, msg in st.session_state.chat_history:
            st.chat_message("user" if sender == "🧑" else "assistant").write(msg)

        # 입력창
        user_input = st.chat_input("답변을 입력해주세요...")

        if user_input:
            st.session_state.chat_history.append(("🧑", user_input))
            st.session_state.context["last_response"] = user_input

            # ReAct 기반 프롬프트 생성
            prompt = create_react_prompt(user_input, st.session_state.context)
            bot_response = generate_gpt_response(prompt)
            
            # 응답 저장 및 컨텍스트 업데이트
            st.session_state.chat_history.append(("🤖", bot_response))
            st.session_state.context["last_response"] = bot_response
            
            # 사용자 응답 저장
            if st.session_state.step == 2:
                if "job_info" not in st.session_state.resume_data:
                    st.session_state.resume_data["job_info"] = {"title": user_input}
                    st.session_state.context["current_topic"] = "job_title"
                    st.session_state.context["next_action"] = "ask_tech_stack"
                else:
                    current_q = st.session_state.current_question
                    st.session_state.resume_data["job_info"][f"answer_{current_q}"] = user_input
                    st.session_state.current_question += 1
                    
                    # 다음 행동 결정
                    if st.session_state.current_question < len(QUESTIONS["job_info"]):
                        st.session_state.context["next_action"] = f"ask_question_{st.session_state.current_question}"
                    else:
                        st.session_state.context["next_action"] = "summarize_and_confirm"
            
            st.rerun()

if __name__ == "__main__":
    main()
