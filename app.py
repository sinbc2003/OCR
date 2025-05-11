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

# 페이지 설정
st.set_page_config(
    page_title="수학 손글씨 LaTeX 변환기",
    page_icon="✏️",
    layout="wide"
)

###############################################################################
# (1) 알림 상자 시각적 문제 해결용 CSS
# 다크 모드 환경에서도 st.success(), st.warning(), st.error() 등의 텍스트가 보이도록
###############################################################################
st.markdown("""
<style>
/* 알림 상자 (st.success, st.warning, st.error 등)의 배경과 텍스트 색상 강제 지정 */
.stAlert {
  background-color: #DFF0D8 !important; /* 라이트그린 계열 */
  color: #000000 !important;           /* 텍스트는 검정색 */
}
.stAlert svg {
  fill: #000000 !important; /* 아이콘(체크/경고 등)도 검정으로 */
}

/* 다크 모드 환경에서도 동일하게 보이도록 강제 */
@media (prefers-color-scheme: dark) {
  .stAlert {
    background-color: #DFF0D8 !important;
    color: #000000 !important;
  }
  .stAlert svg {
    fill: #000000 !important;
  }
}
</style>
""", unsafe_allow_html=True)

###############################################################################
# (2) 기존 CSS 스타일 (앱 전반 디자인, 에디터, 라이트 모드 강제 등)
# 필요에 맞춰 수정/추가
###############################################################################
st.markdown("""
<style>
    /* 전체/배경을 라이트 모드로 강제(추가 적용) */
    @media (prefers-color-scheme: dark) {
      body, .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
      }
    }
    body, .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    .main {
        padding: 2rem;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1 {
        color: #1E3A8A;
        margin-bottom: 1.5rem;
    }
    h2 {
        color: #2563EB;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .css-18e3th9 {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
    }
    .submit-button>button {
        background-color: #10B981;
        color: white;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1.1rem;
    }
    .submit-button>button:hover {
        background-color: #059669;
    }
    .latex-preview {
        padding: 1rem;
        border: 1px solid #E5E7EB;
        border-radius: 0.375rem;
        background-color: #F9FAFB;
        min-height: 200px;
        margin-bottom: 1rem;
        color: #000000 !important;  /* 텍스트 색상을 검정색으로 */
    }
    .latex-preview p {
        color: #000000 !important;
    }
    .rendered-latex-container {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        overflow: auto;
        max-height: 400px;
    }
    .latex-line {
        margin: 5px 0;
    }
    .latex-line p {
        color: #000000 !important;
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
    .css-1fcdlhc {
        padding-top: 0.5rem !important;
    }
    .stImage {
        max-height: 300px;
        margin: 0 auto;
        display: block;
    }
    .user-info-box {
        padding: 1rem;
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 0.375rem;
        margin-bottom: 1.5rem;
    }
    footer {
        margin-top: 3rem;
        text-align: center;
        color: #6B7280;
        font-size: 0.875rem;
    }
    .render-box {
        margin-top: 1.5rem;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    .render-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .editor-active {
        border: 2px solid #3B82F6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }

    /* Ace Editor 관련, 강제 라이트 배경 */
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
</style>
""", unsafe_allow_html=True)

###############################################################################
# 제목/소개
###############################################################################
st.title("수학 손글씨 LaTeX 변환기")
st.markdown("손으로 작성한 수학 문제를 업로드하여 LaTeX 코드로 변환하고 실시간으로 렌더링해보세요.")

###############################################################################
# (3) LaTeX 렌더링 함수 : \[...\] 제거 후 $$...$$로 통일
###############################################################################
def display_latex_with_rendering(latex_code):
    """
    모델에서 \[...\] 형태로 반환된 수식을 
    $$ ... $$ 형태로만 렌더링하도록 전처리.
    """
    # 불필요한 ```latex 제거
    if "```latex" in latex_code:
        latex_code = latex_code.replace("```latex", "").replace("```", "")
    
    # 라인 단위로 분할
    lines = latex_code.strip().split('\n')
    processed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # \[...\] -> 제거
        line = line.replace("\\[", "").replace("\\]", "")
        # (필요 시, $$ 중복제거도 가능)

        processed_lines.append(line)
    
    # 컨테이너 시작
    st.markdown(
        '<div class="rendered-latex-container" style="background-color: #ffffff; color: #000000;">',
        unsafe_allow_html=True
    )
    
    # 각 줄을 $$ ... $$로 감싸서 렌더링
    for line in processed_lines:
        st.markdown(
            f"<div class='latex-line'><p>$$ { line } $$</p></div>",
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

###############################################################################
# (4) 세션 상태 초기화
###############################################################################
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

###############################################################################
# (5) API 키 및 Google Drive/Sheet 설정
###############################################################################
api_key = st.secrets.get("OPENAI_API_KEY", "")
drive_folder_id = st.secrets.get("DRIVE_FOLDER_ID", "")
spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")

###############################################################################
# (6) 구글 API 인증 및 서비스
###############################################################################
def get_google_service(api_name, api_version, scopes):
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        service = build(api_name, api_version, credentials=credentials)
        return service
    except Exception as e:
        st.error(f"구글 서비스 인증 오류: {str(e)}")
        return None

def get_drive_service():
    return get_google_service('drive', 'v3', ['https://www.googleapis.com/auth/drive'])

def get_sheets_service():
    return get_google_service('sheets', 'v4', ['https://www.googleapis.com/auth/spreadsheets'])

###############################################################################
# (7) 구글 드라이브 업로드 함수
###############################################################################
def upload_to_drive(image, filename, folder_id, mime_type="image/jpeg"):
    try:
        service = get_drive_service()
        if service is None:
            return False, "드라이브 서비스 초기화 실패"
        
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
        return False, f"이미지 업로드 오류: {str(e)}"

###############################################################################
# (8) 구글 시트에 LaTeX 코드 추가
###############################################################################
def append_to_sheet(spreadsheet_id, student_id, student_name, latex_code, image_id):
    try:
        service = get_sheets_service()
        if service is None:
            return False, "시트 서비스 초기화 실패"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        values = [
            [
                student_id,
                student_name,
                latex_code,
                timestamp,
                f"https://drive.google.com/file/d/{image_id}/view"
            ]
        ]
        
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:E',  
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return True, result
    except Exception as e:
        return False, f"시트 업데이트 오류: {str(e)}"

###############################################################################
# (9) OpenAI API: 이미지 → LaTeX 추출
###############################################################################
def extract_latex_from_image(image_data, api_key):
    try:
        debug_container = st.empty()
        debug_container.info("API 요청 준비 중...")
        
        if not api_key or len(api_key) < 10:
            raise ValueError("유효한 OpenAI API 키를 입력해주세요")
        
        debug_container.info("이미지 전처리 중...")
        if image_data.mode == 'RGBA':
            image_data = image_data.convert('RGB')
            
        max_size = 1500
        if image_data.width > max_size or image_data.height > max_size:
            ratio = min(max_size / image_data.width, max_size / image_data.height)
            new_size = (int(image_data.width * ratio), int(image_data.height * ratio))
            image_data = image_data.resize(new_size, Image.LANCZOS)
            
        # Base64
        debug_container.info("이미지를 Base64로 인코딩 중...")
        buffered = io.BytesIO()
        image_data.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        img_size_mb = len(img_bytes) / (1024 * 1024)
        if img_size_mb > 20:
            debug_container.warning(f"이미지 크기가 큽니다: {img_size_mb:.2f}MB.")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 모델 후보
        models_to_try = ["gpt-4o-mini", "o4-mini", "gpt-3.5-turbo"]
        model_to_use = models_to_try[0]
        
        debug_container.info(f"선택된 모델: {model_to_use}")
        
        system_prompt = """당신은 손글씨 수학 문제를 정확히 LaTeX 수식으로 변환하는 전문가입니다.
        - 수식이나 문단마다 줄바꿈(\\n) 잘 넣어 가독성 높게.
        - 불필요한 마크다운(```latex 등) 넣지 말 것.
        - LaTeX 코드만 출력.
        """
        
        payload = {
            "model": model_to_use,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
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
                    ]
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.2
        }
        
        # 첫 호출
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        # 실패 시 다른 모델 시도
        if response.status_code != 200 and len(models_to_try) > 1:
            debug_container.warning(f"{model_to_use} 모델 실패. {models_to_try[1]} 모델로 재시도.")
            model_to_use = models_to_try[1]
            payload["model"] = model_to_use
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200 and len(models_to_try) > 2:
                debug_container.warning(f"{model_to_use} 모델도 실패. {models_to_try[2]} 모델로 재시도.")
                model_to_use = models_to_try[2]
                payload["model"] = model_to_use
                
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
        
        if response.status_code == 200:
            result = response.json()
            debug_container.success("API 요청 성공!")
            
            if "choices" in result and len(result["choices"]) > 0:
                extracted_text = result["choices"][0]["message"]["content"]
                
                if "```latex" in extracted_text:
                    extracted_text = extracted_text.replace("```latex", "").replace("```", "")
                
                debug_container.empty()
                return extracted_text
            else:
                debug_container.error("API 응답에 'choices'가 없습니다.")
                return "LaTeX 추출 실패: 결과 없음."
        else:
            error_msg = f"API 오류 ({response.status_code}): {response.text}"
            debug_container.error(error_msg)
            return f"OpenAI API 오류: {error_msg}"
    except Exception as e:
        st.error(f"텍스트 추출 오류: {str(e)}")
        st.error(f"상세 오류: {traceback.format_exc()}")
        return f"추출 중 오류: {str(e)}"

###############################################################################
# (10) 로그인 로직
###############################################################################
if not st.session_state.is_logged_in:
    st.markdown("## 학생 정보 입력")
    st.markdown('<div class="user-info-box">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input("학번을 입력하세요:", placeholder="예: 20230123")
    with col2:
        student_name = st.text_input("이름을 입력하세요:", placeholder="예: 홍길동")
    
    if st.button("시작하기"):
        if student_id and student_name:
            st.session_state.student_id = student_id
            st.session_state.student_name = student_name
            st.session_state.is_logged_in = True
            st.experimental_rerun()
        else:
            st.error("학번과 이름을 모두 입력해주세요.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

###############################################################################
# (11) 로그인 후 화면
###############################################################################
st.markdown(f"""
<div class="user-info-box">
    <p><strong>학번:</strong> {st.session_state.student_id} | <strong>이름:</strong> {st.session_state.student_name}</p>
</div>
""", unsafe_allow_html=True)

# 2개 열로 나누기
col1, col2 = st.columns(2)

###############################################################################
# (12) 왼쪽 컬럼: 이미지 업로드 + OpenAI 처리
###############################################################################
with col1:
    st.header("1. 손글씨 이미지 업로드")
    upload_placeholder = st.empty()
    
    with upload_placeholder.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("수학 손글씨 이미지를 업로드", type=["jpg", "jpeg", "png"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.write(f"이미지 정보: 크기 {image.size}, 형식 {image.format}, 모드 {image.mode}")
            
            if image.mode == 'RGBA':
                image = image.convert('RGB')
                st.info("RGBA 이미지를 RGB로 변환했습니다.")
            
            # 크기가 너무 크면 리사이즈
            max_size = 1500
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.LANCZOS)
                st.info(f"이미지가 커서 {new_size}로 리사이즈했습니다.")
            
            # 세션에 저장
            st.session_state.original_image = image
            st.image(image, caption="업로드한 이미지", use_column_width=True)
            
            process_button = st.button("이미지 처리하기", key="process_button")
            status_container = st.empty()
            
            if process_button:
                status_container.info("처리 시작...")
                if not api_key:
                    st.error("OpenAI API 키가 없습니다. 시크릿에 'OPENAI_API_KEY'를 설정하세요.")
                else:
                    try:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("이미지 분석 준비 중...")
                        progress_bar.progress(25)
                        
                        status_text.text("OpenAI API 호출 중...")
                        progress_bar.progress(50)
                        
                        # OpenAI로 LaTeX 추출
                        latex_result = extract_latex_from_image(image, api_key)
                        
                        progress_bar.progress(75)
                        status_text.text("결과 반영 중...")
                        
                        # 세션에 저장 → 오른쪽 에디터에서 확인
                        st.session_state.latex_code = latex_result
                        st.session_state.processing_complete = True
                        
                        progress_bar.progress(100)
                        status_text.text("완료!")
                        status_container.success("이미지 처리가 완료되었습니다! 오른쪽에서 LaTeX 코드를 확인하세요.")
                        
                        time.sleep(1)
                        st.experimental_rerun()
                        
                    except Exception as e:
                        status_container.error(f"처리 중 오류: {str(e)}")
                        st.error(traceback.format_exc())
            
            elif st.session_state.latex_code:
                status_container.success("이미지를 이미 처리했습니다. 오른쪽에서 편집 가능.")
                
        except Exception as e:
            st.error(f"이미지 처리 오류: {str(e)}")
            st.info("이미지 형식을 확인하거나 다른 파일로 시도해보세요.")
    else:
        st.info("이미지를 업로드해주세요.")

###############################################################################
# (13) 오른쪽 컬럼: LaTeX 코드 에디터 + 렌더링
###############################################################################
with col2:
    st.header("2. LaTeX 코드 편집")
    
    st.markdown('<div class="editor-section">', unsafe_allow_html=True)
    
    # Ace 에디터 초기값
    editor_value = st.session_state.latex_code if st.session_state.latex_code else ""
    
    new_latex_code = st_ace(
        value=editor_value,
        language="latex",
        theme="chrome",  # 라이트 테마 강제
        placeholder="LaTeX 코드가 여기에 표시됩니다. 필요한 경우 수정하세요.",
        height=300,
        key="latex_editor",
        wrap=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # LaTeX 도움말
    with st.expander("LaTeX 편집 도움말", expanded=False):
        st.markdown("""
        ### LaTeX 편집 가이드
        
        - 분수: `\\frac{a}{b}`
        - 제곱/아래첨자: `x^2`, `x_1`
        - 루트: `\\sqrt{x}`, n제곱근: `\\sqrt[n]{x}`
        - 괄호: `\\left( ... \\right)`
        - 텍스트: `\\text{내용}`
        
        새 줄 시작: `\\\\`  
        특수문자 `$, %, _, {, }` 등은 `\\` 붙여야 합니다.
        """)
    
    # 에디터 내용이 바뀌었다면 세션에 반영
    if new_latex_code != st.session_state.latex_code:
        st.session_state.latex_code = new_latex_code
    
    if st.button("렌더링 적용"):
        st.success("LaTeX 코드가 업데이트되었습니다. 아래에서 결과를 확인하세요.")
    
    st.header("3. 렌더링 결과")
    if st.session_state.latex_code:
        display_latex_with_rendering(st.session_state.latex_code)
        
        latex_bytes = st.session_state.latex_code.encode()
        st.download_button(
            label="LaTeX 코드 다운로드",
            data=latex_bytes,
            file_name=f"{st.session_state.student_id}_{st.session_state.student_name}_latex.tex",
            mime="text/plain"
        )
    else:
        st.markdown("""
        <div class="latex-preview">
            <p style="color:#000000; text-align:center; padding-top:70px;">
                변환된 LaTeX 코드가 아직 없습니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

###############################################################################
# (14) 최종 제출 섹션
###############################################################################
if st.session_state.processing_complete and st.session_state.original_image is not None:
    st.markdown("---")
    st.markdown("## 최종 확인 및 제출")
    st.markdown("아래 버튼을 클릭하면 이미지와 LaTeX 코드가 시스템에 제출됩니다.")
    
    submit_button_placeholder = st.empty()
    status_placeholder = st.empty()
    
    if st.session_state.upload_status is None:
        if submit_button_placeholder.button("최종 제출", key="submit_button", type="primary"):
            with st.spinner("제출 중..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{st.session_state.student_id}_{st.session_state.student_name}_{timestamp}.jpg"
                
                # 1) 이미지 업로드
                image_success, image_id = upload_to_drive(
                    st.session_state.original_image, 
                    image_filename, 
                    drive_folder_id
                )
                
                # 2) 구글 시트에 LaTeX 코드 기록
                if image_success:
                    sheet_success, sheet_result = append_to_sheet(
                        spreadsheet_id,
                        st.session_state.student_id,
                        st.session_state.student_name,
                        st.session_state.latex_code,
                        image_id
                    )
                    
                    if sheet_success:
                        st.session_state.upload_status = "success"
                    else:
                        st.session_state.upload_status = "error"
                        st.session_state.error_message = f"구글 시트 업데이트 오류: {sheet_result}"
                else:
                    st.session_state.upload_status = "error"
                    st.session_state.error_message = f"이미지 업로드 오류: {image_id}"
    
    if st.session_state.upload_status == "success":
        submit_button_placeholder.empty()
        status_placeholder.success("제출이 완료되었습니다! 제출해 주셔서 감사합니다.")
        
        if st.button("다시 시작하기", key="restart"):
            st.session_state.latex_code = ""
            st.session_state.original_image = None
            st.session_state.upload_status = None
            st.session_state.processing_complete = False
            st.experimental_rerun()
            
    elif st.session_state.upload_status == "error":
        submit_button_placeholder.empty()
        status_placeholder.error(f"제출 중 오류가 발생했습니다. {st.session_state.error_message}")
        
        if st.button("다시 시도하기", key="retry"):
            st.session_state.upload_status = None
            st.experimental_rerun()

###############################################################################
# (15) 하단 정보(푸터)
###############################################################################
st.markdown("""
<footer>
    <p>이 앱은 Streamlit과 OpenAI API를 사용하여 제작되었습니다.</p>
    <p>© 2025 수학 손글씨 LaTeX 변환기</p>
</footer>
""", unsafe_allow_html=True)
