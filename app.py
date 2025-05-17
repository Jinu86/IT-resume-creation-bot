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
        "summary": ""
    }
    st.session_state.current_question = 0
    st.session_state.context = {
        "current_topic": None,
        "last_response": None,
        "next_action": "ask_job_title"
    }
    st.session_state.new_step = False  # 새로운 단계로 전환 상태 초기화
    if "collected_info" not in st.session_state:
        st.session_state.collected_info = {
            "job_info": {
                "지원 직무": False,
                "관심 기술 분야": False,
                "주로 다룬 기술": False
            },
            "experience": {
                "회사명": False,
                "직무": False,
                "근무 기간": False,
                "사용 기술": False,
                "주요 업무": False,
                "성과/결과": False
            },
            "projects": {
                "프로젝트명": False,
                "기간": False,
                "역할": False,
                "사용 기술": False,
                "성과/결과": False
            },
            "skills": {
                "언어": False,
                "프레임워크": False,
                "DB/인프라": False,
                "기타 도구": False
            },
            "summary": {
                "간단한 자기소개": False,
                "일하는 스타일": False,
                "커리어 방향 or 포부": False
            }
        }

# 진행 상태 표시
def show_progress():
    steps = ["기본 정보", "직무 확인", "경력 상세화", "프로젝트", "기술 스택", "자기소개", "이력서 확인"]
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
    ],
    "experience": [
        "가장 최근에 수행하신 프로젝트나 업무에 대해 설명해주세요. 어떤 역할을 맡으셨고, 어떤 성과를 이루셨나요?",
        "이전 프로젝트에서 가장 어려웠던 기술적 도전과 그것을 어떻게 해결하셨는지 설명해주세요.",
        "팀 프로젝트에서 협업 경험에 대해 말씀해주세요. 특히 기술적 의사결정이나 문제 해결 과정에서의 경험을 중심으로 설명해주시면 좋겠습니다."
    ],
    "projects": [
        "가장 자신 있는 프로젝트 하나를 선정해서, 프로젝트의 목적, 사용한 기술 스택, 본인의 역할, 그리고 달성한 성과를 구체적으로 설명해주세요.",
        "프로젝트 진행 중 발생했던 주요 문제점과 그 해결 과정을 설명해주세요.",
        "프로젝트에서 개선한 성능이나 품질 관련 사례가 있다면 말씀해주세요."
    ],
    "skills": [
        "주요 기술 스택과 각 기술에 대한 숙련도를 설명해주세요.",
        "최근에 새롭게 학습하거나 향상시킨 기술이 있다면 말씀해주세요.",
        "향후 발전시키고 싶은 기술 영역은 무엇인가요?"
    ],
    "summary": [
        "자신의 강점과 특기를 중심으로 간단한 자기소개를 해주세요.",
        "지원하시는 직무에서 본인이 가진 차별화된 경험이나 역량은 무엇인가요?",
        "앞으로의 커리어 목표는 무엇인가요?"
    ]
}

# 필드 정의
FIELD_DEFINITIONS = {
    "job_info": [
        ("지원 직무", "지원하시는 직무를 명확하게 파악"),
        ("관심 기술 분야", "관심 있는 기술 분야 파악"),
        ("주로 다룬 기술", "주요 기술 스택 파악")
    ],
    "experience": [
        ("회사명", "회사명 파악"),
        ("직무", "담당 직무 파악"),
        ("근무 기간", "근무 기간 파악"),
        ("사용 기술", "사용한 기술 스택 파악"),
        ("주요 업무", "주요 업무 내용 파악"),
        ("성과/결과", "주요 성과나 결과 파악")
    ],
    "projects": [
        ("프로젝트명", "프로젝트명 파악"),
        ("기간", "프로젝트 기간 파악"),
        ("역할", "프로젝트에서의 역할 파악"),
        ("사용 기술", "사용한 기술 스택 파악"),
        ("성과/결과", "프로젝트 성과나 결과 파악")
    ],
    "skills": [
        ("언어", "프로그래밍 언어 숙련도 파악"),
        ("프레임워크", "프레임워크 숙련도 파악"),
        ("DB/인프라", "데이터베이스/인프라 숙련도 파악"),
        ("기타 도구", "기타 개발 도구 숙련도 파악")
    ],
    "summary": [
        ("간단한 자기소개", "자기소개 내용 파악"),
        ("일하는 스타일", "업무 스타일 파악"),
        ("커리어 방향 or 포부", "커리어 목표 파악")
    ]
}

# 이력서 생성 관련 함수들
def validate_resume_data(data):
    required_fields = {
        "basic_info": ["name", "email"],
        "job_info": ["title"],
        "summary": [],
        "experience": [],
        "projects": [],
        "skills": []
    }
    
    missing_fields = []
    for section, fields in required_fields.items():
        if not data.get(section):
            missing_fields.append(section)
        elif fields:
            for field in fields:
                if not data[section].get(field):
                    missing_fields.append(f"{section}.{field}")
    
    return missing_fields

def build_resume_text(data):
    try:
        basic_info = data.get("basic_info", {})
        job_info = data.get("job_info", {})
        
        resume_text = f"""
[인적사항]
이름: {basic_info.get('name', '미입력')}
이메일: {basic_info.get('email', '미입력')}
전화번호: {basic_info.get('phone', '미입력')}
포트폴리오: {basic_info.get('portfolio', '없음')}

[지원 직무]
직무: {job_info.get('title', '미입력')}
주요 기술: {job_info.get('answer_0', '미입력')}
주요 경험: {job_info.get('answer_1', '미입력')}

[자기소개]
{chr(10).join(data.get('summary', ['자기소개가 아직 작성되지 않았습니다.']))}

[경력 및 프로젝트 경험]
"""
        # 경력 정보 추가
        for i, exp in enumerate(data.get("experience", []), 1):
            resume_text += f"{i}. {exp}\n"

        resume_text += "\n[프로젝트 경험]\n"
        # 프로젝트 정보 추가
        for i, proj in enumerate(data.get("projects", []), 1):
            resume_text += f"{i}. {proj}\n"

        resume_text += "\n[기술 스택]\n"
        # 기술 스택 추가
        for skill in data.get("skills", []):
            resume_text += f"- {skill}\n"

        return resume_text
    except Exception as e:
        st.error(f"이력서 생성 중 오류가 발생했습니다: {str(e)}")
        return None

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

    # 직무 정보가 있는 경우 포함
    job_info_section = ""
    if st.session_state.resume_data.get("job_info"):
        job_info = st.session_state.resume_data["job_info"]
        job_info_section = f"""
        지원 직무 정보:
        직무: {job_info.get('title', '')}
        기술 스택: {job_info.get('answer_0', '')}
        주요 경험: {job_info.get('answer_1', '')}
        API 경험: {job_info.get('answer_2', '')}
        DB 경험: {job_info.get('answer_3', '')}
        자격증/수상: {job_info.get('answer_4', '')}
        """

    # 현재 단계에 따른 추가 컨텍스트와 완료 조건
    step_context = ""
    completion_criteria = ""
    if st.session_state.step == 2:  # 직무 확인 단계
        step_context = "지금은 직무에 대해 알아보는 중이에요. 어떤 일을 하고 싶으신지, 어떤 경험이 있으신지 차근차근 이야기해주세요."
        completion_criteria = """
        다음 내용들이 잘 파악되면 'STEP_COMPLETE'를 포함해서 답변해주세요:
        1. 어떤 직무를 원하시는지
        2. 어떤 기술을 잘 다루시는지
        3. 어떤 경험이 있으신지
        4. API나 DB 관련 경험은 어떤지
        5. 자격증이나 수상 경력이 있으신지
        """
    elif st.session_state.step == 3:  # 경력 상세화
        step_context = "이제 경력에 대해 자세히 알아볼게요. 어떤 일을 하셨고, 어떤 성과를 이루셨는지 이야기해주세요."
        completion_criteria = """
        다음 내용들이 잘 파악되면 'STEP_COMPLETE'를 포함해서 답변해주세요:
        1. 최근에 어떤 일을 하셨는지
        2. 어떤 어려움을 겪으셨고 어떻게 해결하셨는지
        3. 팀에서 어떻게 일하셨는지
        """
    elif st.session_state.step == 4:  # 프로젝트
        step_context = "프로젝트 경험에 대해 이야기해주세요. 어떤 프로젝트를 진행하셨고, 어떤 역할을 맡으셨나요?"
        completion_criteria = """
        다음 내용들이 잘 파악되면 'STEP_COMPLETE'를 포함해서 답변해주세요:
        1. 어떤 프로젝트를 했는지
        2. 프로젝트에서 어떤 문제를 해결하셨는지
        3. 어떤 성과를 이루셨는지
        """
    elif st.session_state.step == 5:  # 기술 스택
        step_context = "이제 기술 스택에 대해 이야기해주세요. 어떤 기술을 잘 다루시고, 어떤 기술을 더 배우고 싶으신가요?"
        completion_criteria = """
        다음 내용들이 잘 파악되면 'STEP_COMPLETE'를 포함해서 답변해주세요:
        1. 어떤 기술을 잘 다루시는지
        2. 각 기술의 숙련도는 어느 정도인지
        3. 최근에 새로 배운 기술이 있다면 어떤 것인지
        4. 앞으로 어떤 기술을 더 배우고 싶으신지
        """
    elif st.session_state.step == 6:  # 자기소개
        step_context = "마지막으로 자기소개를 작성해볼게요. 어떤 강점이 있으시고, 어떤 목표를 가지고 계신가요?"
        completion_criteria = """
        다음 내용들이 잘 파악되면 'STEP_COMPLETE'를 포함해서 답변해주세요:
        1. 어떤 강점과 특기가 있는지
        2. 다른 사람과 차별화되는 점은 무엇인지
        3. 앞으로 어떤 목표를 가지고 계신지
        """

    # 추가 정보 요청 시 컨텍스트
    if context.get("next_action") == "ask_more_info":
        current_step = st.session_state.step
        last_response = context.get("last_response", "")
        
        # 이전 대화 내용 분석
        chat_history = st.session_state.chat_history
        recent_responses = [msg for sender, msg in chat_history[-4:] if sender == "🧑"]  # 최근 사용자 응답 2개
        
        if current_step == 2:  # 직무 확인
            if "백엔드" in last_response.lower():
                step_context = "백엔드 개발자에 대해 더 자세히 이야기해주세요. 주로 어떤 백엔드 기술을 사용해보셨나요? (예: Spring, Django, Node.js 등)"
            elif "프론트엔드" in last_response.lower():
                step_context = "프론트엔드 개발자에 대해 더 자세히 이야기해주세요. 주로 어떤 프레임워크를 사용해보셨나요? (예: React, Vue, Angular 등)"
            elif "데브옵스" in last_response.lower():
                step_context = "DevOps 엔지니어에 대해 더 자세히 이야기해주세요. 어떤 클라우드 플랫폼을 사용해보셨나요? (예: AWS, Azure, GCP 등)"
            else:
                step_context = "해당 직무에 대해 더 자세히 이야기해주세요. 어떤 기술이나 도구를 주로 사용하시나요?"

        elif current_step == 3:  # 경력 상세화
            # 이전 응답에서 언급된 기술이나 프로젝트를 반영
            mentioned_tech = [tech for tech in ["Java", "Python", "JavaScript", "Spring", "Django", "React"] if tech.lower() in last_response.lower()]
            if mentioned_tech:
                tech_str = ", ".join(mentioned_tech)
                step_context = f"{tech_str}를 사용하신 경험이 있으시군요! 이 기술을 활용한 프로젝트에서 어떤 문제를 해결하기 위해 선택하셨나요?"
            else:
                step_context = "경력에 대해 더 자세히 이야기해주세요. 가장 기억에 남는 프로젝트나 업무는 무엇인가요?"

        elif current_step == 4:  # 프로젝트
            # 이전 응답에서 언급된 프로젝트 유형이나 기술을 반영
            if "웹" in last_response.lower():
                step_context = "웹 프로젝트에 대해 더 자세히 이야기해주세요. 어떤 기술 스택을 사용하셨나요?"
            elif "모바일" in last_response.lower():
                step_context = "모바일 앱 프로젝트에 대해 더 자세히 이야기해주세요. 어떤 플랫폼을 타겟으로 하셨나요? (iOS/Android)"
            else:
                step_context = "프로젝트에 대해 더 자세히 이야기해주세요. 프로젝트의 규모나 기간은 어땠나요?"

        elif current_step == 5:  # 기술 스택
            # 이전 응답에서 언급된 기술을 반영
            mentioned_tech = [tech for tech in ["Java", "Python", "JavaScript", "Spring", "Django", "React"] if tech.lower() in last_response.lower()]
            if mentioned_tech:
                tech_str = ", ".join(mentioned_tech)
                step_context = f"{tech_str}에 대해 더 자세히 이야기해주세요. 이 기술을 얼마나 오래 사용해보셨나요?"
            else:
                step_context = "기술 스택에 대해 더 자세히 이야기해주세요. 각 기술을 얼마나 오래 사용해보셨나요?"

        elif current_step == 6:  # 자기소개
            # 이전 응답에서 언급된 강점이나 목표를 반영
            if "강점" in last_response.lower() or "특기" in last_response.lower():
                step_context = "강점에 대해 더 자세히 이야기해주세요. 이 강점이 실제 프로젝트에서 어떻게 발휘되었나요?"
            elif "목표" in last_response.lower() or "계획" in last_response.lower():
                step_context = "커리어 목표에 대해 더 자세히 이야기해주세요. 이 목표를 이루기 위해 어떤 계획을 세우고 계신가요?"
            else:
                step_context = "자기소개에 대해 더 자세히 이야기해주세요. 어떤 강점이 지원하는 직무에 도움이 될 것 같으신가요?"

    return f"""
    당신은 IT 이력서 작성을 도와주는 친근한 챗봇입니다. 사용자와 자연스럽게 대화하면서 경험과 역량을 파악해주세요.

    {basic_info_section}
    {job_info_section}

    현재 상황:
    - 단계: {st.session_state.step}
    - 현재 주제: {context['current_topic']}
    - 마지막 응답: {context['last_response']}
    - 다음 행동: {context['next_action']}
    {step_context}
    {completion_criteria}

    사용자 입력: "{user_input}"

    대화 규칙:
    - 친근하고 자연스러운 말투를 사용하세요. 예를 들어 '~해주세요' 대신 '~해볼까요?', '~하시나요?' 등을 사용하세요.
    - 반드시 한 번에 하나의 질문만 하세요. 여러 질문을 한꺼번에 하지 마세요.
    - 사용자의 답변을 잘 듣고 공감하는 태도로 대화를 이어가세요.
    - IT 관련 내용을 다룰 때도 쉽고 친근하게 설명해주세요.
    - 사용자의 답변이 짧다면, 구체적인 예시를 들어 더 자세히 이야기해볼 수 있도록 유도하세요.
    - 추가 정보를 요청할 때는 이전 대화 내용을 반영하여 자연스럽게 이어가세요.
    - 사용자가 언급한 기술이나 경험을 기억하고, 그것을 바탕으로 다음 질문을 이어가세요.
    - 각 단계에서 필요한 정보를 하나씩 순차적으로 수집하세요.

    이력서 작성 가이드라인:
    - STAR 방식(상황, 과제, 행동, 결과)을 자연스럽게 대화에 녹여주세요.
    - 구체적인 수치나 성과를 이야기할 수 있도록 도와주세요.
    - 기술 스택과 경험을 명확하게 파악하되, 대화가 딱딱하지 않도록 해주세요.
    - 프로젝트의 규모나 기간을 자연스럽게 물어보세요.

    내부 처리 과정:
    1. 현재 상황을 파악하고 다음 질문을 준비하세요.
    2. 대화가 자연스럽게 이어지도록 해주세요.
    3. 사용자의 응답을 잘 듣고 이해한 후 다음 단계를 계획하세요.
    4. 필요한 정보가 모두 수집되었다고 판단되면 'STEP_COMPLETE'를 포함해서 답변하세요.

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
            intro = f"""안녕하세요 {st.session_state.resume_data['basic_info']['name']}님! 😊
이력서 작성을 도와드릴게요. 차근차근 이야기 나누면서 좋은 이력서를 만들어보아요!
아니 
먼저, 어떤 직무에 지원하실 예정인가요?
예시) `백엔드 개발자, DevOps 엔지니어`

위 예시 중에서 선택하시거나, 다른 직무를 말씀해 주셔도 좋아요!"""
            st.session_state.chat_history.append(("🤖", intro))
            st.session_state.context["next_action"] = "ask_job_title"

        # 디버깅 메시지 표시
        if "debug_message" in st.session_state:
            st.info(f"디버깅: {st.session_state.debug_message}")
            
        # 단계 변경 시 안내 메시지 추가
        if "new_step" in st.session_state and st.session_state.new_step:
            st.info(f"새 단계 시작: {st.session_state.step}")
            
            # 현재 주제 확인
            current_topic = st.session_state.context.get("current_topic")
            st.info(f"현재 주제: {current_topic}")
            
            if st.session_state.step == 3:
                step_intro = f"""이제 {st.session_state.resume_data['basic_info']['name']}님의 직장 경력에 대해 자세히 알아볼게요! 🌟

지금까지 어떤 회사에서 근무하셨는지 말씀해 주실 수 있을까요?
회사명, 담당 직무, 근무 기간, 주요 업무와 성과 등을 중심으로 설명해 주시면 좋겠어요."""

            elif st.session_state.step == 4:
                step_intro = f"""이번에는 주요 프로젝트 경험에 대해 이야기 나눠볼까요? 🚀

진행했던 프로젝트 중에서 기술적으로 가장 도전적이었거나 의미 있었던 프로젝트를 소개해 주세요.
프로젝트명, 목적, 사용한 기술 스택, 본인의 역할, 그리고 달성한 성과를 간단히 소개해 주시면 좋겠어요."""

            elif st.session_state.step == 5:
                step_intro = f"""이제 {st.session_state.resume_data['basic_info']['name']}님의 기술 스택에 대해 알아볼게요! 💻

주로 사용하시는 기술 스택은 무엇인가요? 각 기술에 대한 숙련도도 함께 말씀해 주시면 도움이 될 것 같아요."""

            elif st.session_state.step == 6:
                step_intro = f"""마지막으로 자기소개를 작성해볼까요? ✨

{st.session_state.resume_data['basic_info']['name']}님의 강점과 특기를 중심으로 간단히 자기소개를 해주시겠어요?
지원하시는 직무에서 본인이 가진 차별화된 역량이 있다면 함께 말씀해 주세요."""

            # 메시지를 하나만 추가하기 위해 이전 체크 제거
            st.session_state.chat_history.append(("🤖", step_intro))
            st.info(f"질문 추가됨: {st.session_state.step}, 메시지 내용: {step_intro[:20]}...")
            st.session_state.new_step = False

        # 대화 출력
        for sender, msg in st.session_state.chat_history:
            st.chat_message("user" if sender == "🧑" else "assistant").write(msg)

        # 단계 완료 확인 상태 초기화
        if "step_complete_confirmed" not in st.session_state:
            st.session_state.step_complete_confirmed = False

        # 입력창
        user_input = st.chat_input("답변을 입력해주세요...")

        if user_input:
            st.session_state.chat_history.append(("🧑", user_input))
            st.session_state.context["last_response"] = user_input
            
            # 응답 분석 및 상태 업데이트
            current_topic = st.session_state.context.get("current_topic")
            if not current_topic and st.session_state.step == 2:
                current_topic = "job_info"
                st.session_state.context["current_topic"] = current_topic
                
            st.info(f"analyze_response 호출 - 현재 주제: {current_topic}")
            
            # 주제가 있을 경우에만 분석 수행
            if current_topic:
                is_complete, followup = analyze_response(user_input, current_topic)
                
                if is_complete:
                    st.session_state.step_complete_confirmed = True
                    st.rerun()
                else:
                    # 부족한 정보에 대한 후속 질문
                    bot_response = followup
                    st.session_state.chat_history.append(("🤖", bot_response))
                    st.session_state.context["last_response"] = bot_response
            else:
                # 주제가 없는 경우 기본 응답
                st.info("주제가 설정되지 않았습니다.")
                st.session_state.step_complete_confirmed = True
                st.rerun()

        # 단계 완료 확인 UI
        if st.session_state.step_complete_confirmed:
            current_step = st.session_state.step
            step_names = {
                2: "직무 확인",
                3: "경력 상세화",
                4: "프로젝트",
                5: "기술 스택",
                6: "자기소개"
            }
            
            st.divider()
            st.subheader(f"📝 {step_names.get(current_step, '')} 단계 완료")
            st.write("지금까지 이야기해주신 내용이 충분해 보여요. 다음 단계로 넘어갈까요?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("네, 다음 단계로 넘어갈게요"):
                    if current_step == 2:  # 직무 확인 완료
                        st.session_state.step = 3
                        st.session_state.current_question = 0
                        st.session_state.context["current_topic"] = "experience"
                        st.session_state.context["next_action"] = "ask_experience"
                        
                        # 단계 3 경력 상세화 첫 질문 메시지 직접 추가
                        intro_message = f"""이제 {st.session_state.resume_data['basic_info']['name']}님의 직장 경력에 대해 자세히 알아볼게요! 🌟

지금까지 어떤 회사에서 근무하셨는지 말씀해 주실 수 있을까요?
회사명, 담당 직무, 근무 기간, 주요 업무와 성과 등을 중심으로 설명해 주시면 좋겠어요."""
                        st.session_state.chat_history.append(("🤖", intro_message))
                        
                    elif current_step == 3:  # 경력 상세화 완료
                        st.session_state.step = 4
                        st.session_state.current_question = 0
                        st.session_state.context["current_topic"] = "projects"
                        st.session_state.context["next_action"] = "ask_projects"
                        
                        # 단계 4 프로젝트 첫 질문 메시지 직접 추가
                        intro_message = f"""이번에는 주요 프로젝트 경험에 대해 이야기 나눠볼까요? 🚀

진행했던 프로젝트 중에서 기술적으로 가장 도전적이었거나 의미 있었던 프로젝트를 소개해 주세요.
프로젝트명, 목적, 사용한 기술 스택, 본인의 역할, 그리고 달성한 성과를 간단히 소개해 주시면 좋겠어요."""
                        st.session_state.chat_history.append(("🤖", intro_message))
                        
                    elif current_step == 4:  # 프로젝트 완료
                        st.session_state.step = 5
                        st.session_state.current_question = 0
                        st.session_state.context["current_topic"] = "skills"
                        st.session_state.context["next_action"] = "ask_skills"
                        
                        # 단계 5 기술 스택 첫 질문 메시지 직접 추가
                        intro_message = f"""이제 {st.session_state.resume_data['basic_info']['name']}님의 기술 스택에 대해 알아볼게요! 💻

주로 사용하시는 기술 스택은 무엇인가요? 각 기술에 대한 숙련도도 함께 말씀해 주시면 도움이 될 것 같아요."""
                        st.session_state.chat_history.append(("🤖", intro_message))
                        
                    elif current_step == 5:  # 기술 스택 완료
                        st.session_state.step = 6
                        st.session_state.current_question = 0
                        st.session_state.context["current_topic"] = "summary"
                        st.session_state.context["next_action"] = "ask_summary"
                        
                        # 단계 6 자기소개 첫 질문 메시지 직접 추가
                        intro_message = f"""마지막으로 자기소개를 작성해볼까요? ✨

{st.session_state.resume_data['basic_info']['name']}님의 강점과 특기를 중심으로 간단히 자기소개를 해주시겠어요?
지원하시는 직무에서 본인이 가진 차별화된 역량이 있다면 함께 말씀해 주세요."""
                        st.session_state.chat_history.append(("🤖", intro_message))
                    elif current_step == 6:  # 자기소개 완료
                        st.session_state.step = 7
                        st.session_state.context["next_action"] = "show_resume"
                    
                    st.session_state.step_complete_confirmed = False
                    # 디버깅용 메시지 추가
                    st.session_state.debug_message = f"단계 전환: {current_step} → {st.session_state.step}, new_step: {st.session_state.new_step}"
                    st.rerun()
            
            with col2:
                if st.button("아니요, 더 이야기할게 남았어요"):
                    st.session_state.step_complete_confirmed = False
                    st.session_state.context["next_action"] = "ask_more_info"
                    st.rerun()

    # Step 7: 이력서 구성 요소별 출력
    if st.session_state.step == 7:
        st.title("📄 이력서 항목별 정리")
        st.progress(1.0)
        st.caption("Step 7/7: 이력서 최종 확인")

        data = st.session_state.resume_data
        basic_info = data.get("basic_info", {})
        job_info = data.get("job_info", {})

        # 데이터 검증
        missing_fields = validate_resume_data(data)
        if missing_fields:
            st.warning(f"다음 항목이 누락되었습니다: {', '.join(missing_fields)}")
            if st.button("누락된 항목 입력하기"):
                st.session_state.step = 1
                st.rerun()

        # 1. 인적사항
        with st.expander("1. 인적사항", expanded=True):
            st.markdown(f"""
            **이름**: {basic_info.get('name', '미입력')}  
            **이메일**: {basic_info.get('email', '미입력')}  
            **전화번호**: {basic_info.get('phone', '미입력')}  
            **포트폴리오**: {basic_info.get('portfolio', '없음')}
            """)
            if st.button("인적사항 수정"):
                st.session_state.step = 1
                st.rerun()

        # 2. 지원 직무
        with st.expander("2. 지원 직무", expanded=True):
            st.markdown(f"""
            **직무**: {job_info.get('title', '미입력')}  
            **주요 기술**: {job_info.get('answer_0', '미입력')}  
            **주요 경험**: {job_info.get('answer_1', '미입력')}
            """)
            if st.button("직무 정보 수정"):
                st.session_state.step = 2
                st.rerun()

        # 3. 자기소개
        with st.expander("3. 자기소개", expanded=True):
            summary = data.get("summary", [])
            if summary:
                st.markdown("\n".join(summary))
            else:
                st.info("자기소개가 아직 작성되지 않았습니다.")
            if st.button("자기소개 수정"):
                st.session_state.step = 6
                st.rerun()

        # 4. 경력 요약
        with st.expander("4. 경력 및 프로젝트 경험", expanded=True):
            experiences = data.get("experience", [])
            if experiences:
                for i, exp in enumerate(experiences, 1):
                    st.markdown(f"**{i}.** {exp}")
            else:
                st.info("아직 입력된 경력 정보가 없습니다.")
            if st.button("경력 정보 수정"):
                st.session_state.step = 3
                st.rerun()

        # 5. 프로젝트 요약
        with st.expander("5. 프로젝트 경험", expanded=True):
            projects = data.get("projects", [])
            if projects:
                for i, proj in enumerate(projects, 1):
                    st.markdown(f"**{i}.** {proj}")
            else:
                st.info("아직 입력된 프로젝트 정보가 없습니다.")
            if st.button("프로젝트 정보 수정"):
                st.session_state.step = 4
                st.rerun()

        # 6. 기술 스택
        with st.expander("6. 기술 스택", expanded=True):
            skills = data.get("skills", [])
            if skills:
                st.markdown("\n".join(skills))
            else:
                st.info("기술 스택이 아직 입력되지 않았습니다.")
            if st.button("기술 스택 수정"):
                st.session_state.step = 5
                st.rerun()

        st.divider()

        # 이력서 다운로드 옵션
        col1, col2 = st.columns(2)
        with col1:
            if st.button("이력서 다운로드"):
                resume_text = build_resume_text(data)
                if resume_text:
                    st.success("이력서가 생성되었습니다!")
                    st.download_button(
                        "📥 이력서 다운로드",
                        resume_text,
                        file_name=f"{basic_info.get('name', 'resume')}.txt",
                        mime="text/plain"
                    )

        with col2:
            if st.button("처음으로 돌아가기"):
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()

def analyze_response(user_input: str, topic: str) -> tuple[bool, str]:
    """사용자 응답을 분석하고 수집된 정보 상태를 업데이트"""
    current_fields = FIELD_DEFINITIONS.get(topic, [])
    all_fields_complete = True
    
    for field_name, field_description in current_fields:
        # 각 필드별 분석
        prompt = f"""
        사용자 응답: "{user_input}"
        
        다음 필드에 대한 정보가 충분한지 분석해주세요:
        필드명: {field_name}
        설명: {field_description}
        
        응답 형식:
        - 충분한 정보가 있다면: [YES][ENOUGH]
        - 일부 정보가 있지만 더 필요하다면: [YES][NEED_MORE]
        - 정보가 없다면: [NO]
        """
        response = model.generate_content(prompt)
        analysis = response.text.strip()
        
        # 분석 결과에 따른 상태 업데이트
        if "[YES][ENOUGH]" in analysis:
            st.session_state.collected_info[topic][field_name] = True
        elif "[YES][NEED_MORE]" in analysis or "[NO]" in analysis:
            all_fields_complete = False
            # 부족한 필드에 대한 후속 질문 생성
            followup_prompt = f"""
            이전 응답: "{user_input}"
            
            다음 필드에 대한 추가 정보를 요청하는 질문을 생성해주세요:
            필드명: {field_name}
            설명: {field_description}
            
            질문은 자연스럽고 친근한 말투로 작성해주세요.
            """
            followup_response = model.generate_content(followup_prompt)
            return False, followup_response.text.strip()
    
    return all_fields_complete, ""

def generate_followup_question(previous_answer, topic):
    # 현재 단계의 수집 상태 확인
    current_info = st.session_state.collected_info.get(topic, {})
    incomplete_fields = [field for field, collected in current_info.items() if not collected]
    
    if not incomplete_fields:
        return "STEP_COMPLETE"
    
    # 부족한 필드에 대한 질문 생성
    field_name = incomplete_fields[0]
    field_description = next((desc for name, desc in FIELD_DEFINITIONS[topic] if name == field_name), "")
    
    # 첫 질문인 경우
    if not previous_answer:
        prompt = f"""
        다음 필드에 대한 질문을 생성해주세요:
        필드명: {field_name}
        설명: {field_description}
        
        질문은 자연스럽고 친근한 말투로 작성해주세요.
        """
    else:
        prompt = f"""
        이전 응답: "{previous_answer}"
        
        다음 필드에 대한 추가 정보를 요청하는 질문을 생성해주세요:
        필드명: {field_name}
        설명: {field_description}
        
        질문은 자연스럽고 친근한 말투로 작성해주세요.
        """
    
    response = model.generate_content(prompt)
    return response.text.strip()

if __name__ == "__main__":
    main()
