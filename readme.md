# 수학 손글씨 LaTeX 변환기

손으로 작성한 수학 문제와 풀이를 업로드하면 LaTeX 코드로 변환하고 실시간으로 렌더링해주는 Streamlit 웹 애플리케이션입니다.

## 주요 기능

- 📸 **손글씨 이미지 업로드**: JPG, JPEG, PNG 형식의 이미지 파일 지원
- 🔄 **자동 LaTeX 변환**: OpenAI의 o4-mini 모델을 사용하여 손글씨를 LaTeX 코드로 변환
- ✏️ **실시간 편집**: 변환된 LaTeX 코드를 직접 편집 가능
- 👁️ **실시간 렌더링**: 편집한 LaTeX 코드가 즉시 수학 표현으로 렌더링
- 💾 **코드 다운로드**: 변환 및 편집된 LaTeX 코드를 파일로 다운로드 가능

## 설치 및 실행 방법

### 로컬에서 실행하기

1. 저장소 복제:
```bash
git clone https://github.com/your-username/math-handwriting-latex.git
cd math-handwriting-latex
```

2. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

4. OpenAI API 키 설정:
   - `.streamlit` 폴더를 만들고 그 안에 `secrets.toml` 파일 생성
   - 파일에 다음 내용 추가: `OPENAI_API_KEY = "your-api-key-here"`

5. Streamlit 앱 실행:
```bash
streamlit run app.py
```

### Streamlit Cloud에 배포하기

1. GitHub에 코드 푸시:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. [Streamlit Cloud](https://streamlit.io/cloud)에 접속하여 로그인

3. "New app" 버튼 클릭하고 저장소 연결

4. 앱 설정:
   - 저장소: `your-username/math-handwriting-latex`
   - 브랜치: `main`
   - 메인 파일 경로: `app.py`
   - 고급 설정에서 API 키 추가: `OPENAI_API_KEY`

5. "Deploy!" 버튼 클릭

## 사용 방법

1. 웹 앱에 접속합니다.
2. 손으로 작성한 수학 문제 이미지를 업로드합니다.
3. "이미지 처리하기" 버튼을 클릭하면 OpenAI API가 이미지를 분석합니다.
4. 추출된 LaTeX 코드가 에디터에 표시되고, 오른쪽에 렌더링 결과가 나타납니다.
5. 필요한 경우 LaTeX 코드를 직접 수정하면 실시간으로 렌더링이 업데이트됩니다.
6. "LaTeX 코드 다운로드" 버튼을 눌러 코드를 저장할 수 있습니다.

## 주의사항

- 이 앱을 사용하려면 유효한 OpenAI API 키가 필요합니다.
- 이미지 처리 시 OpenAI API 사용 비용이 발생할 수 있습니다.
- 복잡한 수학 표현의 경우 일부 변환이 정확하지 않을 수 있으므로 편집 기능을 활용하세요.

## 기술 스택

- [Streamlit](https://streamlit.io/): 웹 애플리케이션 프레임워크
- [OpenAI API](https://openai.com/): 이미지 인식 및 LaTeX 변환 (gpt-4o-mini 모델 사용)
- [Streamlit-Ace](https://github.com/okld/streamlit-ace): 코드 에디터 컴포넌트
- [MathJax](https://www.mathjax.org/): LaTeX 수학 표현식 렌더링

## 라이센스

MIT License
