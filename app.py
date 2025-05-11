import streamlit as st
import os
from PIL import Image
import base64
import io
import requests
import time
import json
import traceback
from streamlit_ace import st_ace
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
# 강제 라이트 테마용 CSS (다크 모드 무시 + 알림박스 등 텍스트 색상 강제)
st.markdown(
    """
    <style>
    /* 전체 바디와 스트림릿 앱 영역을 흰 배경/검정 텍스트로 통일 */
    body, .stApp, .block-container {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    /* streamlit의 info, warning, error 박스 배경/글자색 보정 */
    .stAlert p {
        color: #000000 !important;
    }
    /* Ace Editor 내부를 강제 흰 배경 + 검정글자로 */
    .ace_editor,
    .ace_scroller,
    .ace_content,
    .ace_gutter {
        background: #ffffff !important;
        color: #000000 !important;
    }
    .ace_print-margin {
        background-color: #ffffff !important;
    }
    .ace_gutter {
        background-color: #f7f7f7 !important;
        color: #666666 !important;
    }
    /* 버튼, 제목 등에 쓰일 기본 스타일 약간 보정 */
    .stButton>button {
        background-color: #2563EB !important;
        color: white !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover {
        background-color: #1E40AF !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# -------------------------------------------------------------------------------------

# 추가 CSS (앱 디자인 전반)
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1 {
        color: #1E3A8A;
        margin-bottom: 1.5rem;
    }
    .user-info-box {
        padding: 1rem;
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 0.375rem;
        margin-bottom: 1.5rem;
    }
    .upload-section {
        padding: 1.5rem;
        border: 1px dashed #D1D5DB;
        border-radius: 0.375rem;
        background-color: #F9FAFB;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .editor-section {
        border: 1px solid #E5E7EB;
        border-radius: 0.375rem;
        margin-bottom: 1.5rem;
        background-color: #FFFFFF;
    }
    .rendered-latex-container {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        overflow: auto;
        max-height: 400px;
    }
    footer {
        margin-top: 3rem;
        text-align: center;
        color: #6B7280;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 세션 상태 초기화
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'student_name' not in st.session_state:
    st.session_state.student_name = ""
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

# ----------------------------------------------------------------------------
# OpenAI API 키 & 구글 드라이브/시트 설정 (Streamlit secrets)
api_key = st.secrets.get("OPENAI_API_KEY", "")
drive_folder_id = st.secrets.get("DRIVE_FOLDER_ID", "")
spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")

# ----------------------------------------------------------------------------
# 구글 API 서비스 초기화
def get_google_service(api_name, api_version, scopes):
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        service = build(api_name, api_version, credentials=credentials)
        return service
    except Exception as e:
        st.error(f"[오류] 구글 서비스 인증에 실패했습니다: {str(e)}")
        return None

def get_drive_service():
    return get_google_service('drive', 'v3', ['https://www.googleapis.com/auth/drive'])

def get_sheets_service():
    return get_google_service('sheets', 'v4', ['https://www.googleapis.com/auth/spreadsheets'])

# ----------------------------------------------------------------------------
# 구글 드라이브에 이미지 업로드
def upload_to_drive(image, filename, folder_id, mime_type="image/jpeg"):
    try:
        service = get_drive_service()
        if service is None:
            return False, "드라이브 서비스가 None입니다."
        
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

# ----------------------------------------------------------------------------
# 구글 시트에 결과 append
def append_to_sheet(spreadsheet_id, student_id, student_name, latex_code, image_id):
    try:
        service = get_sheets_service()
        if service is None:
            return False, "시트트 서비스가 None입니다."
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        values = [[
            student_id,
            student_name,
            latex_code,
            timestamp,
            f"https://drive.google.com/file/d/{image_id}/view"
        ]]
        
        body = {'values': values}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:E',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return True, result
    except Exception as e:
        return False, f"시트 업데이트 중 오류: {str(e)}"

# ----------------------------------------------------------------------------
# OpenAI API로 이미지 → LaTeX 추출
def extract_latex_from_image(image_data, api_key):
    """OpenAI API 또는 OCR+LLM 등을 사용해 이미지 속 수학 식을 LaTeX로 변환."""
    status_box = st.empty()
    
    try:
        if not api_key or len(api_key) < 10:
            raise ValueError("유효한 OpenAI API 키가 없습니다. (secrets에서 OPENAI_API_KEY 설정 필요)")
        
        status_box.info("이미지 전처리 중...")
        # RGBA → RGB 변환
        if image_data.mode == 'RGBA':
            image_data = image_data.convert('RGB')
        
        # 크기 제한 (가로/세로 1500px 넘으면 축소)
        max_size = 1500
        if image_data.width > max_size or image_data.height > max_size:
            ratio = min(max_size / image_data.width, max_size / image_data.height)
            new_size = (int(image_data.width * ratio), int(image_data.height * ratio))
            image_data = image_data.resize(new_size, Image.LANCZOS)
        
        # Base64 인코딩
        status_box.info("이미지를 Base64로 인코딩 중...")
        buffered = io.BytesIO()
        image_data.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        # (예시) 모델 후보
        models_to_try = ["gpt-4o-mini", "o4-mini", "gpt-3.5-turbo"]
        model_to_use = models_to_try[0]
        
        # Prompt
        system_prompt = """당신은 손글씨로 된 수학 문제와 풀이를 정확한 LaTeX 코드로 변환하는 전문가입니다.
- 본문 전체를 LaTeX 형식으로 변환하되, 불필요한 설명은 배제합니다.
- 수식은 $$ ... $$ 로 감싸거나 \\begin{align*} ... \\end{align*} 형태를 허용합니다.
- 문단/수식별로 줄바꿈(\\n)을 적절히 넣어 가독성을 높입니다.
"""
        
        # OpenAI API 호출
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {
                        "type": "text",
                        "text": "이 손글씨 이미지를 LaTeX 코드로 변환해주세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]}
            ],
            "max_tokens": 1500,
            "temperature": 0.1
        }
        
        status_box.info(f"OpenAI API({model_to_use}) 호출 중...")
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        
        # 모델 변경 시도
        idx_model = 0
        while response.status_code != 200 and idx_model < len(models_to_try)-1:
            idx_model += 1
            model_to_use = models_to_try[idx_model]
            payload["model"] = model_to_use
            status_box.warning(f"{models_to_try[idx_model-1]} 모델 실패 → {model_to_use}로 재시도합니다.")
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        
        if response.status_code != 200:
            return f"[오류] OpenAI API 응답 실패: {response.status_code}, {response.text}"
        
        # 결과 파싱
        result_json = response.json()
        if "choices" not in result_json or len(result_json["choices"]) == 0:
            return "[오류] OpenAI API 응답에 choices가 없습니다."
        
        extracted_text = result_json["choices"][0]["message"]["content"]
        
        # 불필요한 마크다운 코드 블록(```latex ... ```) 제거
        if "```latex" in extracted_text:
            extracted_text = extracted_text.replace("```latex", "").replace("```", "")
        
        # 최종 LaTeX 코드
        status_box.success("LaTeX 추출 완료!")
        return extracted_text
    
    except Exception as e:
        status_box.error(f"[오류] 텍스트 추출 중 문제 발생: {e}")
        st.error(traceback.format_exc())
        return f"오류 발생: {str(e)}"

# ----------------------------------------------------------------------------
# 라텍스 렌더링 함수
def display_latex_with_rendering(latex_code):
    """
    Streamlit은 기본적으로 st.markdown() 호출 시
    $$...$$ 또는 $...$ 패턴을 수학 수식으로 렌더링한다.
    """
    # 그냥 st.markdown에 넣으면 자동 렌더링된다.
    # 여러 줄 환경(align 등)도 $$...$$로 감싸져 있으면 가능.
    st.markdown(latex_code)

# ----------------------------------------------------------------------------
# 1) 로그인 단계
if not st.session_state.is_logged_in:
    st.title("수학 손글씨 LaTeX 변환기")
    st.subheader("학생 정보 입력")
    
    with st.container():
        st.markdown('<div class="user-info-box">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.student_id = st.text_input("학번", placeholder="예) 20230123")
        with c2:
            st.session_state.student_name = st.text_input("이름", placeholder="예) 홍길동")
        
        if st.button("시작하기"):
            if st.session_state.student_id and st.session_state.student_name:
                st.session_state.is_logged_in = True
                st.experimental_rerun()
            else:
                st.error("학번과 이름을 모두 입력해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ----------------------------------------------------------------------------
# 2) 로그인 후 메인 화면
st.title("수학 손글씨 LaTeX 변환기")
st.markdown(f"""
<div class="user-info-box">
    <strong>학번:</strong> {st.session_state.student_id} &nbsp; | &nbsp; 
    <strong>이름:</strong> {st.session_state.student_name}
</div>
""", unsafe_allow_html=True)

# 레이아웃: 왼쪽 = 이미지 업로드/처리, 오른쪽 = LaTeX 에디터 & 미리보기
left_col, right_col = st.columns(2)

with left_col:
    st.header("1. 손글씨 이미지 업로드")
    
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("이미지 (JPG/PNG)", type=["jpg", "jpeg", "png"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.write(f"이미지 정보: {image.format}, {image.size}, {image.mode}")
            
            # 원본 이미지 세션에 저장
            st.session_state.original_image = image
            st.image(image, caption="업로드된 이미지", use_column_width=True)
            
            if st.button("이미지 → LaTeX 변환"):
                if not api_key:
                    st.error("OpenAI API 키가 설정되지 않았습니다. (secrets에 OPENAI_API_KEY 필요)")
                else:
                    # 모델 추출
                    with st.spinner("이미지 분석 및 LaTeX 변환 중..."):
                        latex_result = extract_latex_from_image(image, api_key)
                        
                    # 추출 결과 세션에 저장
                    st.session_state.latex_code = latex_result
                    st.session_state.processing_complete = True
                    st.success("추출된 LaTeX 코드는 우측 '2. LaTeX 코드 편집'에서 확인/수정하세요.")
                    
                    # 화면 다시 그리기
                    st.experimental_rerun()
        
        except Exception as ex:
            st.error(f"이미지 처리 중 오류: {ex}")
            st.error(traceback.format_exc())
    else:
        st.info("변환할 손글씨 이미지를 업로드하세요.")

with right_col:
    st.header("2. LaTeX 코드 편집")
    st.markdown('<div class="editor-section">', unsafe_allow_html=True)
    
    # Ace 에디터에 현재 세션의 latex_code 표시
    edited_code = st_ace(
        value=st.session_state.latex_code,
        language="latex",
        theme="chrome",
        placeholder="추출된 LaTeX 코드가 여기에 나타납니다.\n수정이 필요하면 직접 편집하세요.",
        height=300,
        key="latex_editor",
        wrap=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 에디터 결과를 세션에 바로 반영
    st.session_state.latex_code = edited_code
    
    st.header("3. 렌더링 결과")
    if st.session_state.latex_code:
        display_latex_with_rendering(st.session_state.latex_code)
        
        # 다운로드 버튼
        latex_bytes = st.session_state.latex_code.encode("utf-8")
        st.download_button(
            label="LaTeX 코드 다운로드",
            data=latex_bytes,
            file_name=f"{st.session_state.student_id}_{st.session_state.student_name}_latex.tex",
            mime="text/plain"
        )
    else:
        st.info("아직 변환된 LaTeX 코드가 없습니다.")

# ----------------------------------------------------------------------------
# 3) 최종 제출 섹션
if st.session_state.processing_complete and st.session_state.original_image:
    st.markdown("---")
    st.markdown("## 최종 제출")
    
    st.write("변환된 LaTeX 코드와 이미지를 제출하시겠습니까?")
    submit_area = st.empty()
    
    if st.session_state.upload_status is None:
        if submit_area.button("제출하기", type="primary"):
            with st.spinner("제출 중... 잠시만 기다려주세요."):
                # 1) 구글 드라이브 업로드
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{st.session_state.student_id}_{st.session_state.student_name}_{timestamp}.jpg"
                
                success_drive, drive_result = upload_to_drive(
                    st.session_state.original_image, filename, drive_folder_id
                )
                
                if success_drive:
                    # 2) 구글 시트 저장
                    success_sheet, sheet_result = append_to_sheet(
                        spreadsheet_id,
                        st.session_state.student_id,
                        st.session_state.student_name,
                        st.session_state.latex_code,
                        drive_result  # image_id
                    )
                    if success_sheet:
                        st.session_state.upload_status = "success"
                    else:
                        st.session_state.upload_status = "error"
                        st.session_state.error_message = f"시트 업데이트 실패: {sheet_result}"
                else:
                    st.session_state.upload_status = "error"
                    st.session_state.error_message = f"드라이브 업로드 실패: {drive_result}"
    
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
    <p>이 앱은 Streamlit + OpenAI API로 제작되었습니다.</p>
    <p>© 2025 수학 손글씨 LaTeX 변환기</p>
</footer>
""", unsafe_allow_html=True)
