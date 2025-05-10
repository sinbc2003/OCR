# 수학 손글씨 LaTeX 변환기

손으로 작성한 수학 문제와 풀이를 업로드하면 LaTeX 코드로 변환하고 실시간으로 렌더링해주는 Streamlit 웹 애플리케이션입니다. 사용자가 제출한 이미지와 LaTeX 결과물은 관리자의 Google Drive에 자동으로 저장됩니다.

## 주요 기능

- 👤 **사용자 정보 입력**: 학번과 이름 기반으로 파일 관리
- 📸 **손글씨 이미지 업로드**: JPG, JPEG, PNG 형식의 이미지 파일 지원
- 🔄 **자동 LaTeX 변환**: OpenAI의 o4-mini 모델을 사용하여 손글씨를 LaTeX 코드로 변환
- ✏️ **실시간 편집**: 변환된 LaTeX 코드를 직접 편집 가능
- 👁️ **실시간 렌더링**: 편집한 LaTeX 코드가 즉시 수학 표현으로 렌더링
- 💾 **구글 드라이브 저장**: 이미지와 LaTeX 코드가 관리자의 드라이브에 자동 저장
- 📊 **제출 로그 관리**: 제출 기록이 CSV 파일로 관리되어 쉽게 확인 가능

## 설치 및 설정 방법

### 1. 저장소 복제

```bash
git clone https://github.com/your-username/math-handwriting-latex.git
cd math-handwriting-latex
```

### 2. 가상 환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 구글 클라우드 서비스 계정 설정

구글 드라이브에 파일을 자동으로 저장하기 위해 Google Cloud 서비스 계정이 필요합니다. 서비스 계정은 사용자 개입 없이 Google API에 접근할 수 있는 특별한 계정입니다.

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트를 생성하거나 기존 프로젝트 선택
3. API 및 서비스 > 라이브러리에서 "Google Drive API" 검색 및 활성화
4. API 및 서비스 > 사용자 인증 정보 > 사용자 인증 정보 만들기 > 서비스 계정
5. 서비스 계정 세부정보 입력 후 생성
6. 서비스 계정에 대한 키 생성 (JSON 형식) 및 다운로드
7. 다운로드한 JSON 파일의 내용을 `.streamlit/secrets.toml` 파일의 `[gcp_service_account]` 섹션에 추가

### 5. 구글 드라이브 폴더 공유 설정

1. 구글 드라이브에서 결과물을 저장할 폴더 생성
2. 폴더를 서비스 계정 이메일 주소(예: your-service-account@your-project-id.iam.gserviceaccount.com)와 공유
3. 폴더 URL에서 ID 부분 복사 (https://drive.google.com/drive/folders/**folder-id-here**)
4. 복사한 폴더 ID를 `.streamlit/secrets.toml` 파일의 `DRIVE_FOLDER_ID` 항목에 추가

### 6. OpenAI API 키 설정

1. [OpenAI API 키 관리 페이지](https://platform.openai.com/api-keys)에서 API 키 발급
2. 발급받은 API 키를 `.streamlit/secrets.toml` 파일의 `OPENAI_API_KEY` 항목에 추가

### 7. Streamlit 시크릿 설정 파일 생성

1. `.streamlit` 폴더 생성 (없는 경우)
2. `secrets.toml.example` 파일을 참고하여 `.streamlit/secrets.toml` 파일 생성 및 실제 값 입력

```toml
# OpenAI API 키 설정
OPENAI_API_KEY = "your-openai-api-key-here"

# 구글 드라이브 폴더 ID (결과물이 저장될 폴더)
DRIVE_FOLDER_ID = "your-google-drive-folder-id-here"

# Google Cloud 서비스 계정 정보
# 서비스 계정 JSON 키 내용을 여기에 입력
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----
"""
client_email = "your-service-account-email@your-project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email%40your-project-id.iam.gserviceaccount.com"
```

### 8. 로컬에서 앱 실행

```bash
streamlit run app.py
```

## Streamlit Cloud에 배포하기

1. GitHub에 코드 푸시 (주의: `secrets.toml` 파일이 `.gitignore`에 포함되어 있는지 확인)

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
   - 고급 설정에서 시크릿 추가:
     - `OPENAI_API_KEY`: OpenAI API 키
     - `DRIVE_FOLDER_ID`: Google Drive 폴더 ID
     - `gcp_service_account`: Google Cloud 서비스 계정 정보 (JSON 형식)
5. "Deploy!" 버튼 클릭

## 사용 방법

1. 웹 앱에 접속합니다.
2. 학번과 이름을 입력하고 "시작하기" 버튼을 클릭합니다.
3. 손으로 작성한 수학 문제 이미지를 업로드합니다.
4. "이미지 처리하기" 버튼을 클릭하면 OpenAI API가 이미지를 분석합니다.
5. 추출된 LaTeX 코드가 에디터에 표시되고, 오른쪽에 렌더링 결과가 나타납니다.
6. 필요한 경우 LaTeX 코드를 직접 수정하면 실시간으로 렌더링이 업데이트됩니다.
7. 결과가 만족스러우면 "최종 확인 완료 및 제출" 버튼을 클릭합니다.
8. 제출된 이미지와 LaTeX 코드는 관리자의 Google Drive에 자동으로 저장됩니다.

## 파일 저장 형식

- 이미지 파일: `{학번}_{이름}_{timestamp}.jpg`
- LaTeX 파일: `{학번}_{이름}_{timestamp}.tex`
- 제출 로그: `submission_log_{날짜}.csv`

## 주의사항

- 이 앱을 사용하려면 유효한 OpenAI API 키와 Google Cloud 서비스 계정이 필요합니다.
- OpenAI API 사용 시 비용이 발생할 수 있습니다.
- 복잡한 수학 표현의 경우 일부 변환이 정확하지 않을 수 있으므로 편집 기능을 활용하세요.
- 모든 중요한 인증 정보는 `.gitignore`에 포함시켜 GitHub에 업로드되지 않도록 주의하세요.

## 기술 스택

- [Streamlit](https://streamlit.io/): 웹 애플리케이션 프레임워크
- [OpenAI API](https://openai.com/): 이미지 인식 및 LaTeX 변환 (gpt-4o-mini 모델 사용)
- [Google Drive API](https://developers.google.com/drive): 결과물 저장 및 관리
- [Streamlit-Ace](https://github.com/okld/streamlit-ace): 코드 에디터 컴포넌트
- [MathJax](https://www.mathjax.org/): LaTeX 수학 표현식 렌더링

## 라이센스

MIT License
