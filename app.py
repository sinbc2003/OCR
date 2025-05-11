import streamlit as st
import os
from PIL import Image
import base64
import io
import requests
import time
import json
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

# 앱 스타일 적용
st.markdown("""
<style>
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
        color: #000000 !important;  /* 텍스트 색상을 검정색으로 강제 지정 */
    }
    .latex-preview p {
        color: #000000 !important;  /* p 태그의 텍스트 색상도 검정색으로 지정 */
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
</style>
""", unsafe_allow_html=True)

# 제목
st.title("수학 손글씨 LaTeX 변환기")
st.markdown("손으로 작성한 수학 문제를 업로드하여 LaTeX 코드로 변환하고 실시간으로 렌더링해보세요.")

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

# API 키 및 구글 드라이브 설정 가져오기
api_key = st.secrets.get("OPENAI_API_KEY", "")
drive_folder_id = st.secrets.get("DRIVE_FOLDER_ID", "")
spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")

# 구글 API 인증 및 서비스 설정
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

# 구글 드라이브 서비스 초기화
def get_drive_service():
    return get_google_service('drive', 'v3', ['https://www.googleapis.com/auth/drive'])

# 구글 시트 서비스 초기화
def get_sheets_service():
    return get_google_service('sheets', 'v4', ['https://www.googleapis.com/auth/spreadsheets'])

# 이미지를 구글 드라이브에 업로드하는 함수
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
        
        media = MediaIoBaseUpload(
            buffered, 
            mimetype=mime_type,
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return True, file.get('id')
    except Exception as e:
        return False, f"이미지 업로드 오류: {str(e)}"

# 구글 시트에 LaTeX 코드 추가하는 함수
def append_to_sheet(spreadsheet_id, student_id, student_name, latex_code, image_id):
    try:
        service = get_sheets_service()
        if service is None:
            return False, "시트 서비스 초기화 실패"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 시트에 추가할 데이터
        values = [
            [
                student_id,                  # A열: 학번
                student_name,                # B열: 이름
                latex_code,                  # C열: LaTeX 코드
                timestamp,                   # D열: 제출 시간
                f"https://drive.google.com/file/d/{image_id}/view"  # E열: 이미지 링크
            ]
        ]
        
        body = {
            'values': values
        }
        
        # 시트의 마지막 행에 데이터 추가
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:E',  # 시트 이름과 범위 지정
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return True, result
    except Exception as e:
        return False, f"시트 업데이트 오류: {str(e)}"

# 이미지를 OpenAI API로 전송하여 LaTeX 추출하는 함수
def extract_latex_from_image(image_data, api_key):
    """OpenAI API의 o4-mini 모델을 사용하여 이미지에서 LaTeX 코드를 추출합니다."""
    try:
        # 디버깅 메시지 표시
        debug_container = st.empty()
        debug_container.info("API 요청 준비 중...")
        
        # API 키 확인
        if not api_key or len(api_key) < 10:  # API 키는 일반적으로 길이가 깁니다
            raise ValueError("유효한 OpenAI API 키를 입력해주세요")
        
        # 이미지 전처리
        debug_container.info("이미지 전처리 중...")
        if image_data.mode == 'RGBA':
            image_data = image_data.convert('RGB')
            
        # 이미지 크기 제한 (너무 큰 이미지는 처리 속도가 느려짐)
        max_size = 1500  # 최대 크기 지정 (약간 줄임)
        if image_data.width > max_size or image_data.height > max_size:
            # 비율 유지하며 크기 조정
            ratio = min(max_size / image_data.width, max_size / image_data.height)
            new_size = (int(image_data.width * ratio), int(image_data.height * ratio))
            image_data = image_data.resize(new_size, Image.LANCZOS)
            
        # 이미지를 Base64로 인코딩
        debug_container.info("이미지를 Base64로 인코딩 중...")
        buffered = io.BytesIO()
        image_data.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        # 이미지 크기 확인 (너무 크면 OpenAI API 제한에 걸릴 수 있음)
        img_size_mb = len(img_bytes) / (1024 * 1024)
        if img_size_mb > 20:  # OpenAI는 일반적으로 20MB 미만 권장
            debug_container.warning(f"이미지 크기가 큽니다: {img_size_mb:.2f}MB. 처리 속도가 느릴 수 있습니다.")
        
        # OpenAI API 요청 설정
        debug_container.info("OpenAI API 요청 준비 중...")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 모델 선택 - gpt-4o-mini로 설정 (o4-mini가 실패하면 폴백)
        model_to_use = "gpt-4o-mini"
        
        debug_container.info(f"선택된 모델: {model_to_use}")
        
        # 요청 페이로드 구성 - Chat Completions API 사용
        payload = {
            "model": model_to_use,
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 손글씨 수학 문제와 풀이를 LaTeX 코드로 변환하는 전문가입니다. 이미지에서 보이는 수학 표현을 정확하게 LaTeX 코드로 변환해주세요. 설명 없이 LaTeX 코드만 제공해주세요."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 수학 손글씨를 LaTeX 코드로 변환해주세요. LaTeX 코드만 제공해주세요."
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
            "max_tokens": 1000,
            "temperature": 0.3
        }
        
        # API 호출
        debug_container.info("OpenAI API 호출 중...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        # 응답 확인
        if response.status_code == 200:
            result = response.json()
            debug_container.success("API 요청 성공!")
            
            if "choices" in result and len(result["choices"]) > 0:
                extracted_text = result["choices"][0]["message"]["content"]
                debug_container.empty()  # 디버그 메시지 숨기기
                return extracted_text
            else:
                debug_container.error("API 응답에 'choices' 필드가 없습니다.")
                return "LaTeX 추출에 실패했습니다. API 응답에서 결과를 찾을 수 없습니다."
        else:
            error_msg = f"API 오류 ({response.status_code}): {response.text}"
            debug_container.error(error_msg)
            st.error(f"API 응답: {response.text}")
            return f"OpenAI API 오류가 발생했습니다: {error_msg}"
    except Exception as e:
        st.error(f"텍스트 추출 오류: {str(e)}")
        import traceback
        st.error(f"상세 오류: {traceback.format_exc()}")
        return f"텍스트 추출 중 오류 발생: {str(e)}"

# 사용자 로그인 화면
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
    
    # 로그인 전에는 나머지 콘텐츠를 표시하지 않음
    st.stop()

# 로그인 후 화면
st.markdown(f"""
<div class="user-info-box">
    <p><strong>학번:</strong> {st.session_state.student_id} | <strong>이름:</strong> {st.session_state.student_name}</p>
</div>
""", unsafe_allow_html=True)

# 애플리케이션 레이아웃 - 2개 열로 나누기
col1, col2 = st.columns(2)

with col1:
    st.header("1. 손글씨 이미지 업로드")
    
    # 이미지 업로드 섹션
    upload_placeholder = st.empty()
    
    with upload_placeholder.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("수학 손글씨가 담긴 이미지를 업로드하세요", type=["jpg", "jpeg", "png"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 이미지 미리보기 및 처리 버튼
    if uploaded_file is not None:
        try:
            # 이미지 로드 및 전처리
            image = Image.open(uploaded_file)
            st.write(f"이미지 정보: 크기 {image.size}, 형식 {image.format}, 모드 {image.mode}")
            
            # RGBA 이미지를 RGB로 변환 (알파 채널 제거)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
                st.info("RGBA 이미지를 RGB로 변환했습니다.")
            
            # 이미지 크기 제한 (너무 큰 이미지는 처리 속도가 느려짐)
            max_size = 1500  # 최대 크기 지정
            if image.width > max_size or image.height > max_size:
                # 비율 유지하며 크기 조정
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.LANCZOS)
                st.info(f"이미지 크기가 너무 커서 {new_size}로 조정했습니다.")
            
            # 세션에 원본 이미지 저장
            st.session_state.original_image = image
            
            # 이미지 표시
            st.image(image, caption="업로드한 이미지", use_column_width=True)
            
            # 처리 버튼 및 상태 정보를 위한 컨테이너
            button_col, status_col = st.columns([1, 3])
            
            with button_col:
                process_button = st.button("이미지 처리하기")
            
            # 처리 버튼 클릭 시 
            if process_button:
                status_col.info("처리 시작...")
                
                # API 키 확인
                if not api_key:
                    st.error("OpenAI API 키가 설정되지 않았습니다.")
                    st.error("Streamlit Cloud의 시크릿 설정에서 'OPENAI_API_KEY'를 설정하세요.")
                else:
                    try:
                        st.info(f"OpenAI API 키 확인: {api_key[:5]}...{api_key[-4:]} (길이: {len(api_key)})")
                        
                        # 처리 진행 표시
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # 진행 상태 업데이트
                        status_text.text("이미지 분석 준비 중...")
                        progress_bar.progress(25)
                        
                        # API 키를 사용하여 이미지 처리
                        status_text.text("OpenAI API 호출 중...")
                        progress_bar.progress(50)
                        
                        latex_result = extract_latex_from_image(image, api_key)
                        
                        # 결과 업데이트
                        progress_bar.progress(75)
                        status_text.text("처리 결과 업데이트 중...")
                        
                        st.session_state.latex_code = latex_result
                        st.session_state.processing_complete = True
                        
                        # 완료
                        progress_bar.progress(100)
                        status_text.text("처리 완료!")
                        
                        # 3초 후 리프레시 (선택적)
                        time.sleep(2)
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"처리 중 오류 발생: {str(e)}")
                        import traceback
                        st.error(f"상세 오류: {traceback.format_exc()}")
            
            # 이전 처리 결과가 있으면 표시
            if st.session_state.latex_code and not process_button:
                st.success("이미지가 이미 처리되었습니다. LaTeX 코드를 편집할 수 있습니다.")
                
        except Exception as e:
            st.error(f"이미지 처리 중 오류가 발생했습니다: {str(e)}")
            st.info("다른 이미지 파일을 시도해보세요. JPEG 또는 PNG 형식이 가장 안정적입니다.")

with col2:
    st.header("2. LaTeX 코드 편집")
    
    # LaTeX 코드 에디터
    st.markdown('<div class="editor-section">', unsafe_allow_html=True)
    new_latex_code = st_ace(
        value=st.session_state.latex_code,
        language="latex",
        theme="github",
        placeholder="LaTeX 코드가 여기에 표시됩니다. 필요한 경우 직접 편집할 수 있습니다.",
        height=250,
        key="latex_editor"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 사용자가 코드를 변경했으면 세션 상태 업데이트
    if new_latex_code != st.session_state.latex_code:
        st.session_state.latex_code = new_latex_code
    
    st.header("3. 렌더링 결과")
    
    if st.session_state.latex_code:
        # MathJax로 렌더링 (LaTeX을 HTML에 삽입)
        st.markdown(f"""
        <div class="latex-preview">
            <p style="color: black; font-size: 16px;">$$
            {st.session_state.latex_code}
            $$</p>
        </div>
        """, unsafe_allow_html=True)
        
        # MathJax 스크립트 직접 포함
        st.components.v1.html(f"""
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <div id="latex-render" style="padding: 20px; background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; color: black;">
            $$
            {st.session_state.latex_code}
            $$
        </div>
        <script>
            window.onload = function() {{
                if (typeof MathJax !== 'undefined') {{
                    MathJax.typeset();
                }}
            }}
        </script>
        """, height=300)
        
        # 다운로드 버튼 - LaTeX 코드를 텍스트 파일로 저장
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
                이미지를 업로드하고 처리하면 여기에 렌더링 결과가 표시됩니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

# 최종 제출 섹션 (처리가 완료된 경우에만 표시)
if st.session_state.processing_complete and st.session_state.original_image is not None:
    st.markdown("---")
    st.markdown("## 최종 확인 및 제출")
    st.markdown("아래 버튼을 클릭하면 이미지와 LaTeX 코드가 시스템에 제출됩니다.")
    
    submit_button_placeholder = st.empty()
    status_placeholder = st.empty()
    
    if st.session_state.upload_status is None:
        if submit_button_placeholder.button("최종 확인 완료 및 제출", key="submit_button", type="primary"):
            with st.spinner("제출 중..."):
                # 현재 시간을 파일명에 포함
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{st.session_state.student_id}_{st.session_state.student_name}_{timestamp}.jpg"
                
                # 1. 이미지 업로드
                image_success, image_id = upload_to_drive(
                    st.session_state.original_image, 
                    image_filename, 
                    drive_folder_id
                )
                
                # 2. 구글 시트에 LaTeX 코드 추가
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
            # 세션 초기화
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

# 하단 정보
st.markdown("""
<footer>
    <p>이 앱은 Streamlit과 OpenAI API를 사용하여 제작되었습니다.</p>
    <p>© 2025 수학 손글씨 LaTeX 변환기</p>
</footer>
""", unsafe_allow_html=True)

# MathJax 스크립트 추가 (LaTeX 렌더링용)
st.markdown("""
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<script>
    window.MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true,
            processEnvironments: true
        },
        options: {
            ignoreHtmlClass: 'tex2jax_ignore',
            processHtmlClass: 'tex2jax_process'
        }
    };
    document.addEventListener("DOMContentLoaded", function() {
        if (typeof MathJax !== 'undefined') {
            MathJax.typeset();
        }
    });
</script>
""", unsafe_allow_html=True)
