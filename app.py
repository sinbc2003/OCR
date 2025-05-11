import streamlit as st
import os
from PIL import Image
import base64
import io
import requests
import time
import json
import traceback
from datetime import datetime
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

# 페이지 기본 설정
st.set_page_config(
    page_title="수학 손글씨 LaTeX 변환기",
    page_icon="✏️",
    layout="wide"
)

# -------------------------------------------------------------------------------------
# CSS: 배경 = 흰색, 텍스트 기본 검정. 단, selectbox 내용(#9CA3AF)로 지정
st.markdown(
    """
    <style>
    /* 전체 배경 흰색 */
    body, .stApp, .block-container {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    /* 기본 텍스트: 검정 */
    h1, h2, h3, h4, h5, h6, strong, p, div, label {
        color: #000000 !important;
    }
    .stAlert p {
        color: #000000 !important;
    }
    /* 버튼: 파란색 배경 + 흰 텍스트 */
    .stButton>button {
        background-color: #2563EB !important;
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover {
        background-color: #1E40AF !important;
        color: #ffffff !important;
    }
    /* 앱 레이아웃 */
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    footer {
        margin-top: 3rem;
        text-align: center;
        color: #000000;
        font-size: 0.875rem;
    }

    /* selectbox(드롭다운) 글자색 = 회색(#9CA3AF). */
    /* 1) 기본 필드에 보여지는 텍스트 색상 */
    .stSelectbox div[data-baseweb="select"] * {
        color: #9CA3AF !important;
    }
    /* 2) 드롭다운 열렸을 때 옵션 항목 색상 */
    /*   (스트림릿 버전에 따라 class명이 다를 수 있으므로, -option 등 다양한 경우에 대응) */
    .stSelectbox [class*="option"] {
        color: #9CA3AF !important;
    }
    .stSelectbox [class*="-menu-item"] {
        color: #9CA3AF !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# -------------------------------------------------------------------------------------

# -------------------- 세션 상태 초기화 --------------------
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'student_name' not in st.session_state:
    st.session_state.student_name = ""
if 'doc_type' not in st.session_state:
    st.session_state.doc_type = ""  # 문제 / 해설
if 'latex_code' not in st.session_state:
    st.session_state.latex_code = ""
if 'original_image' not in st.session_state:
    st.session_state.original_image = None
if 'upload_status' not in st.session_state:
    st.session_state.upload_status = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""

# -------------------- API 키 & 구글 설정 --------------------
api_key = st.secrets.get("OPENAI_API_KEY", "")
drive_folder_id = st.secrets.get("DRIVE_FOLDER_ID", "")
spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")

# -------------------- 구글 API 초기화 --------------------
from google.oauth2 import service_account
def get_google_service(api_name, api_version, scopes):
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        service = build(api_name, api_version, credentials=credentials)
        return service
    except Exception as e:
        st.error(f"[오류] 구글 서비스 인증 실패: {str(e)}")
        return None

def get_drive_service():
    return get_google_service('drive', 'v3', ['https://www.googleapis.com/auth/drive'])

def get_sheets_service():
    return get_google_service('sheets', 'v4', ['https://www.googleapis.com/auth/spreadsheets'])

# -------------------- 구글 드라이브 업로드 --------------------
def upload_to_drive(image, filename, folder_id, mime_type="image/jpeg"):
    try:
        service = get_drive_service()
        if service is None:
            return False, "드라이브 서비스가 None임."
        
        # RGBA -> RGB 변환(방어적)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(buffered, mimetype=mime_type, resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return True, file.get('id')
    except Exception as e:
        return False, f"이미지 업로드 중 오류: {str(e)}"

# -------------------- 구글 시트 업데이트 --------------------
def append_to_sheet(spreadsheet_id, student_id, student_name, doc_type, latex_code, image_id):
    """
    시트 컬럼 구성:
    A: 학번, B: 이름, C: 종류(문제/해설), D: LaTeX, E: 제출시간, F: 이미지 링크
    """
    try:
        service = get_sheets_service()
        if service is None:
            return False, "시트 서비스가 None임."
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        values = [[
            student_id,
            student_name,
            doc_type,
            latex_code,
            timestamp,
            f"https://drive.google.com/file/d/{image_id}/view"
        ]]
        
        body = {'values': values}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:F',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return True, result
    except Exception as e:
        return False, f"시트 업데이트 중 오류: {str(e)}"

# -------------------- OpenAI (o4-mini) --------------------
def extract_latex_from_image(image_data, api_key):
    """
    이미지 속 손글씨 수식을 'o4-mini' 모델로 변환.
    불필요한 파라미터(max_tokens 등)는 제거.
    """
    status_box = st.empty()
    
    try:
        if not api_key or len(api_key) < 10:
            raise ValueError("유효한 OpenAI API 키가 없습니다. (secrets에 OPENAI_API_KEY 필요)")
        
        # 이미지 전처리
        if image_data.mode == 'RGBA':
            image_data = image_data.convert('RGB')
        
        max_size = 1500
        if image_data.width > max_size or image_data.height > max_size:
            ratio = min(max_size / image_data.width, max_size / image_data.height)
            new_size = (int(image_data.width * ratio), int(image_data.height * ratio))
            image_data = image_data.resize(new_size, Image.LANCZOS)
        
        status_box.info("이미지를 Base64로 인코딩 중...")
        buffered = io.BytesIO()
        image_data.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        model_to_use = "o4-mini"
        system_prompt = """당신은 수학 손글씨 이미지를 정확한 LaTeX 코드로 변환해주는 전문가입니다.
- 불필요한 설명 없이, 오직 LaTeX 코드만 출력하세요.
- mathjax로 렌더링이 되도록 수식은 $$로 감싸서 표현하세요. 텍스트는 그대로 출력하고, 수식은 달러 구분자 방식을 사용한 Math Mode를 사용하세요. 즉, 디스플레이 모드로 출력하시오.
"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 손글씨 이미지를 LaTeX 코드로 변환해줘."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
        }
        
        status_box.info("o4-mini 모델 호출 중...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            return f"[오류] OpenAI API 응답 실패: {response.status_code}, {response.text}"
        
        result_json = response.json()
        if "choices" not in result_json or len(result_json["choices"]) == 0:
            return "[오류] OpenAI API 응답에 choices가 없습니다."
        
        extracted_text = result_json["choices"][0]["message"]["content"]
        
        # 불필요한 코드 블록 제거
        if "```latex" in extracted_text:
            extracted_text = extracted_text.replace("```latex", "").replace("```", "")
        
        status_box.success("LaTeX 추출 완료!")
        return extracted_text
    
    except Exception as e:
        status_box.error(f"[오류] 텍스트 추출 중 문제 발생: {e}")
        st.error(traceback.format_exc())
        return f"오류 발생: {str(e)}"

# -------------------- 렌더링 함수 --------------------
def display_latex_with_rendering(latex_code: str):
    """$$...$$ 구문을 st.markdown()에 넣으면 MathJax로 자동 렌더링됨."""
    st.markdown(latex_code)

# ----------------------------------------------------------------------------
# 1) 로그인 단계
if not st.session_state.is_logged_in:
    st.title("수학 손글씨 LaTeX 변환기")
    st.subheader("학생 정보 입력")
    
    st.session_state.student_id = st.text_input("학번", placeholder="예) 20230123")
    st.session_state.student_name = st.text_input("이름", placeholder="예) 홍길동")
    st.session_state.doc_type = st.selectbox("종류 선택", ["문제", "해설"])
    
    if st.button("시작하기"):
        if st.session_state.student_id and st.session_state.student_name:
            st.session_state.is_logged_in = True
            st.experimental_rerun()
        else:
            st.error("학번과 이름을 모두 입력해주세요.")
    
    st.stop()

# ----------------------------------------------------------------------------
# 2) 로그인 후 메인 화면
st.title("수학 손글씨 LaTeX 변환기")
st.markdown(f"""
**학번:** {st.session_state.student_id}  
**이름:** {st.session_state.student_name}  
**종류:** {st.session_state.doc_type}
""")

# 레이아웃: 왼쪽(이미지 업로드), 오른쪽(코드 편집 + 렌더링)
left_col, right_col = st.columns(2)

with left_col:
    st.header("1. 손글씨 이미지 업로드")
    uploaded_file = st.file_uploader("이미지 (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.write(f"이미지 정보: {image.format}, {image.size}, {image.mode}")
            
            # RGBA -> RGB 변환
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            st.session_state.original_image = image
            st.image(image, caption="업로드된 이미지", use_column_width=True)
            
            if st.button("이미지 → LaTeX 변환"):
                if not api_key:
                    st.error("OpenAI API 키가 없습니다. (secrets에 OPENAI_API_KEY 필요)")
                else:
                    with st.spinner("이미지 분석 및 LaTeX 변환 중..."):
                        latex_result = extract_latex_from_image(image, api_key)
                    
                    st.session_state.latex_code = latex_result
                    st.session_state.processing_complete = True
                    st.success("추출된 LaTeX 코드는 우측에서 확인/수정하세요.")
                    st.experimental_rerun()
        
        except Exception as ex:
            st.error(f"이미지 처리 중 오류: {ex}")
            st.error(traceback.format_exc())
    else:
        st.info("변환할 손글씨 이미지를 업로드하세요.")

with right_col:
    st.header("2. LaTeX 코드 편집")
    
    temp_latex = st.text_area(
        "LaTeX 코드 (수정 가능)",
        value=st.session_state.latex_code,
        height=300
    )
    
    if st.button("렌더링 적용"):
        st.session_state.latex_code = temp_latex
    
    st.header("3. 렌더링 결과")
    if st.session_state.latex_code.strip():
        display_latex_with_rendering(st.session_state.latex_code)
    else:
        st.info("아직 변환된 LaTeX 코드가 없습니다.")

# ----------------------------------------------------------------------------
# 3) 최종 제출 섹션
if st.session_state.processing_complete and st.session_state.original_image:
    st.markdown("---")
    st.markdown("## 최종 제출")
    
    st.write("현재 LaTeX 코드 및 이미지를 제출하시겠습니까?")
    submit_area = st.empty()
    
    if st.session_state.upload_status is None:
        if submit_area.button("제출하기"):
            with st.spinner("제출 중... 잠시만 기다려주세요."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{st.session_state.student_id}_{st.session_state.student_name}_{timestamp}.jpg"
                
                # 1) 이미지 업로드
                success_drive, drive_result = upload_to_drive(
                    st.session_state.original_image, filename, drive_folder_id
                )
                
                if success_drive:
                    # 2) 구글 시트 기록
                    success_sheet, sheet_result = append_to_sheet(
                        spreadsheet_id,
                        st.session_state.student_id,
                        st.session_state.student_name,
                        st.session_state.doc_type,
                        st.session_state.latex_code,
                        drive_result
                    )
                    if success_sheet:
                        st.session_state.upload_status = "success"
                    else:
                        st.session_state.upload_status = "error"
                        st.session_state.error_message = f"시트 업데이트 오류: {sheet_result}"
                else:
                    st.session_state.upload_status = "error"
                    st.session_state.error_message = f"드라이브 업로드 오류: {drive_result}"
    
    if st.session_state.upload_status == "success":
        submit_area.empty()
        st.success("제출이 완료되었습니다! 감사합니다.")
        
        if st.button("다시 시작하기"):
            st.session_state.latex_code = ""
            st.session_state.original_image = None
            st.session_state.upload_status = None
            st.session_state.processing_complete = False
            st.experimental_rerun()
    
    elif st.session_state.upload_status == "error":
        submit_area.empty()
        st.error(f"제출 중 오류가 발생했습니다. {st.session_state.error_message}")
        
        if st.button("재시도"):
            st.session_state.upload_status = None
            st.session_state.error_message = ""
            st.experimental_rerun()

# ----------------------------------------------------------------------------
# 하단 정보
st.markdown("""
<footer>
    <p>제작 : 교사 신병철</p>
    <p>© 2025 수학 손글씨 LaTeX 변환기</p>
</footer>
""", unsafe_allow_html=True)
