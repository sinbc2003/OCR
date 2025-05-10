import streamlit as st
import os
from PIL import Image
import base64
import io
import requests
import time
import json
from streamlit_ace import st_ace

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
    .latex-preview {
        padding: 1rem;
        border: 1px solid #E5E7EB;
        border-radius: 0.375rem;
        background-color: #F9FAFB;
        min-height: 200px;
        margin-bottom: 1rem;
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

# OpenAI API 키 설정
if 'OPENAI_API_KEY' in st.secrets:
    api_key = st.secrets['OPENAI_API_KEY']
else:
    api_key = st.text_input("OpenAI API 키를 입력하세요:", type="password")
    if not api_key:
        st.warning("API 키를 입력하셔야 서비스를 이용할 수 있습니다.")
        st.stop()

# 이미지를 OpenAI API로 전송하여 LaTeX 추출하는 함수
def extract_latex_from_image(image_data, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    
    # 이미지를 base64로 인코딩
    buffered = io.BytesIO()
    image_data.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "당신은 손글씨 수학 문제와 풀이를 LaTeX 코드로 변환하는 전문가입니다. 이미지에서 보이는 수학 표현을 정확하게 LaTeX 코드로 변환해주세요. 설명 없이 LaTeX 코드만 제공해주세요."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_str}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "이 수학 손글씨를 LaTeX 코드로 변환해주세요. LaTeX 코드만 제공해주세요."
                    }
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.3,
        "seed": 123
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "LaTeX 추출에 실패했습니다. API 응답에서 결과를 찾을 수 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"

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
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드한 이미지", use_column_width=True)
        
        if st.button("이미지 처리하기"):
            with st.spinner("이미지 분석 중... 잠시만 기다려주세요."):
                # 세션 상태에 저장된 API 키를 사용하여 이미지 처리
                latex_result = extract_latex_from_image(image, api_key)
                st.session_state.latex_code = latex_result

with col2:
    st.header("2. LaTeX 코드 편집")
    
    # 초기 LaTeX 코드 설정
    if 'latex_code' not in st.session_state:
        st.session_state.latex_code = ""
    
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
            <p>$$
            {st.session_state.latex_code}
            $$</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 다운로드 버튼 - LaTeX 코드를 텍스트 파일로 저장
        latex_bytes = st.session_state.latex_code.encode()
        st.download_button(
            label="LaTeX 코드 다운로드",
            data=latex_bytes,
            file_name="math_latex_code.tex",
            mime="text/plain"
        )
    else:
        st.markdown("""
        <div class="latex-preview">
            <p style="color:#6B7280; text-align:center; padding-top:70px;">
                이미지를 업로드하고 처리하면 여기에 렌더링 결과가 표시됩니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

# 하단 정보
st.markdown("""
<footer>
    <p>이 앱은 Streamlit과 OpenAI API를 사용하여 제작되었습니다.</p>
    <p>© 2025 수학 손글씨 LaTeX 변환기</p>
</footer>
""", unsafe_allow_html=True)

# MathJax 스크립트 추가 (LaTeX 렌더링용)
st.markdown("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js"></script>
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
</script>
""", unsafe_allow_html=True)
