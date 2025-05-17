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

# 메인 앱
def main():
    st.title("💼 IT 직무 이력서 생성 챗봇")
    show_progress()

    # Step 1: 기본 정보 입력 (폼 기반)
    if st.session_state.step == 1:
        with st.form("basic_info_form"):
            st.subheader("기본 정보를 입력해주세요")
            
            # 필수 입력 필드
            name = st.text_input("이름 *", help="한글 또는 영문으로 입력해주세요")
            email = st.text_input("이메일 *", help="이력서에 표시될 이메일 주소를 입력해주세요")
            
            # 선택 입력 필드
            phone = st.text_input("전화번호", help="선택사항입니다")
            portfolio = st.text_input("포트폴리오 링크", help="GitHub, 블로그 등")
            
            submitted = st.form_submit_button("다음으로")

        if submitted:
            if not name or not email:
                st.error("이름과 이메일은 필수 입력 항목입니다.")
            else:
                st.session_state.resume_data["basic_info"] = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "portfolio": portfolio
                }
                st.session_state.step = 2
                st.rerun()

    # Step 2 이후: 챗봇 기반 흐름
    else:
        # 챗봇 환영 메시지
        if not st.session_state.chat_history:
            intro = f"안녕하세요 {st.session_state.resume_data['basic_info']['name']}님!\n이제부터 IT 이력서를 작성해드릴게요. 먼저, 어떤 직무에 지원하실 예정인가요?"
            st.session_state.chat_history.append(("🤖", intro))

        # 대화 출력
        for sender, msg in st.session_state.chat_history:
            st.chat_message("user" if sender == "🧑" else "assistant").write(msg)

        # 입력창
        user_input = st.chat_input("답변을 입력해주세요...")

        if user_input:
            st.session_state.chat_history.append(("🧑", user_input))

            # GPT 프롬프트 구성
            full_prompt = f"""
            사용자의 기본 정보:
            이름: {st.session_state.resume_data['basic_info']['name']}
            이메일: {st.session_state.resume_data['basic_info']['email']}
            전화번호: {st.session_state.resume_data['basic_info']['phone']}
            포트폴리오: {st.session_state.resume_data['basic_info']['portfolio']}

            사용자의 현재 입력: "{user_input}"

            위 내용을 기반으로 이력서 작성을 위한 질문을 이어가거나, 경험을 이력서 문장으로 정리해주세요.
            - 자연스럽고 부드러운 말투로
            - IT 직무 중심
            - 필요 시 추가 질문 포함
            """

            bot_response = generate_gpt_response(full_prompt)
            st.session_state.chat_history.append(("🤖", bot_response))
            st.rerun()

if __name__ == "__main__":
    main()
