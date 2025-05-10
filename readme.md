# 수학 손글씨 LaTeX 변환기

손으로 작성한 수학 문제와 풀이를 업로드하면 LaTeX 코드로 변환하고 실시간으로 렌더링해주는 Streamlit 웹 애플리케이션입니다. 사용자가 제출한 이미지는 Google Drive에, LaTeX 결과물은 Google Sheets에 자동으로 저장됩니다.

## 주요 기능

- 👤 **사용자 정보 입력**: 학번과 이름 기반으로 파일 관리
- 📸 **손글씨 이미지 업로드**: JPG, JPEG, PNG 형식의 이미지 파일 지원
- 🔄 **자동 LaTeX 변환**: OpenAI의 o4-mini 모델을 사용하여 손글씨를 LaTeX 코드로 변환
- ✏️ **실시간 편집**: 변환된 LaTeX 코드를 직접 편집 가능
- 👁️ **실시간 렌더링**: 편집한 LaTeX 코드가 즉시 수학 표현으로 렌더링
- 💾 **구글 드라이브/시트 저장**: 
  - 이미지는 지정된 Google Drive 폴더에 저장
  - LaTeX 코드는 Google Sheets에 학생 정보와 함께 저장
- 📊 **자동화된 데이터 관리**: 모든 제출물이 중앙에서 체계적으로 관리됨

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

구글 드라이브와 시트에 접근하기 위해 Google Cloud 서비스 계정이 필요합니다.

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트를 생성하거나 기존 프로젝트 선택
3. API 및 서비스 > 라이브러리에서 다음 API 활성화:
   - Google Drive API
   - Google Sheets API
4. API 및 서비스 > 사용자 인증 정보 > 사용자 인증 정보 만들기 > 서비스 계정
5. 서비스 계정 세부정보 입력 후 생성
6. 서비스 계정에 대한 키 생성 (JSON 형식) 및 다운로드
7. 다운로드한 JSON 파일의 내용을 `.streamlit/secrets.toml` 파일의 `[gcp_service_account]` 섹션에 추가

### 5. 구글 드라이브 폴더 설정

1. 구글 드라이브에서 이미지 파일을 저장할 폴더 생성
2. 폴더를 서비스 계정 이메일 주소와 공유 (편집자 권한 부여)
3. 폴더 URL에서 ID 부분 복사 (https://drive.google.com/drive/folders/**folder-id-here**)
4. 복사한 폴더 ID를 `.streamlit/secrets.toml` 파일의 `DRIVE_FOLDER_ID` 항목에 추가

### 6. 구글 스프레드시트 설정

1. 구글 드라이브에서 새 스프레드시트 생성
2. 첫 번째 행에 다음 헤더 추가:
   - A1: "학번"
   - B1: "이름"
   - C1: "LaTeX 코드"
   - D1: "제출 시간"
   - E1: "이미지 링크"
3. 스프레드시트를 서비스 계정 이메일 주소와 공유 (편집자 권한 부여)
4. 스프레드시트 URL에서 ID 부분 복사 (https://docs.google.com/spreadsheets/d/**spreadsheet-id-here**/edit)
5. 복사한 스프레드시트 ID를 `.streamlit/secrets.toml` 파일의 `SPREADSHEET_ID` 항목에 추가

### 7. OpenAI API 키 설정

1. [OpenAI API 키 관리 페이지](https://platform.openai.com/api-keys)에서 API 키 발급
2. 발급받은 API 키를 `.streamlit/secrets.toml` 파일의 `OPENAI_API_KEY` 항목에 추가

### 8. Streamlit 시크릿 설정 파일 생성

1. `.streamlit` 폴더 생성 (없는 경우)
2. `secrets.toml.example` 파일을 참고하여 `.streamlit/secrets.toml` 파일 생성 및 실제 값 입력

```toml
# OpenAI API 키 설정
OPENAI_API_KEY = "your-openai-api-key-here"

# 구글 드라이브 폴더 ID (이미지가 저장될 폴더)
DRIVE_FOLDER_ID = "your-google-drive-folder-id-here"

# 구글 스프레드시트 ID (LaTeX 코드가 저장될 시트)
SPREADSHEET_ID = "your-google-spreadsheet-id-here"

# Google Cloud 서비스 계정 정보
[gcp_service_account]
type = "service_account"
project_id =
# 수학 손글씨 LaTeX 변환기 설정 가이드

이 가이드는 제공된 Google Drive 폴더와 Google Sheets 스프레드시트를 사용하여 애플리케이션을 설정하는 방법을 설명합니다.

## 1. 필요한 계정 및 API 키

### OpenAI API 키
- [OpenAI 웹사이트](https://platform.openai.com/api-keys)에서 API 키를 발급받습니다.
- 이 키는 손글씨 이미지에서 LaTeX 코드를 추출하기 위한 o4-mini 모델 접근에 사용됩니다.

### Google Cloud 서비스 계정
- [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트와 서비스 계정을 생성합니다.
- Drive API와 Sheets API를 활성화합니다.
- 서비스 계정 키(JSON)를 다운로드합니다.

## 2. 설정 파일 구성

다음 내용으로 `.streamlit/secrets.toml` 파일을 생성합니다:

```toml
# OpenAI API 키 설정
OPENAI_API_KEY = "your-openai-api-key-here"

# 구글 드라이브 폴더 ID (이미지가 저장될 폴더)
DRIVE_FOLDER_ID = "1RbNytjT2LMeZQiFRBZQgJKbnro2xqLdB"

# 구글 스프레드시트 ID (LaTeX 코드가 저장될 시트)
SPREADSHEET_ID = "1pOLX2N2ShTkafQcid-EPmnQ9gMxoTLzMmkqfoHvYUFE"

# Google Cloud 서비스 계정 정보
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

`gcp_service_account` 섹션은 다운로드한 서비스 계정 JSON 파일의 내용으로 대체해야 합니다.

## 3. Google 리소스 공유 설정

### 구글 드라이브 폴더 공유
1. [이 링크](https://drive.google.com/drive/folders/1RbNytjT2LMeZQiFRBZQgJKbnro2xqLdB)로 드라이브 폴더에 접속합니다.
2. 폴더를 우클릭하고 "공유"를 선택합니다.
3. 서비스 계정 이메일(예: your-service-account@your-project-id.iam.gserviceaccount.com)을 추가합니다.
4. 편집자 권한을 부여하고 저장합니다.

### 구글 스프레드시트 공유
1. [이 링크](https://docs.google.com/spreadsheets/d/1pOLX2N2ShTkafQcid-EPmnQ9gMxoTLzMmkqfoHvYUFE/edit)로 스프레드시트에 접속합니다.
2. "공유" 버튼을 클릭합니다.
3. 서비스 계정 이메일을 추가합니다.
4. 편집자 권한을 부여하고 저장합니다.

## 4. Streamlit Cloud 배포

1. GitHub에 코드를 푸시합니다:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. [Streamlit Cloud](https://streamlit.io/cloud)에 접속하여 GitHub 계정으로 로그인합니다.

3. "New app" 버튼을 클릭하고 앱 설정:
   - 저장소: `your-username/math-handwriting-latex`
   - 브랜치: `main`
   - 메인 파일 경로: `app.py`

4. "Advanced settings"를 클릭하고 다음 시크릿을 추가:
   - `OPENAI_API_KEY`: OpenAI API 키
   - `DRIVE_FOLDER_ID`: 1RbNytjT2LMeZQiFRBZQgJKbnro2xqLdB
   - `SPREADSHEET_ID`: 1pOLX2N2ShTkafQcid-EPmnQ9gMxoTLzMmkqfoHvYUFE
   - `gcp_service_account`: 서비스 계정 JSON 내용 (전체 JSON을 그대로 붙여넣기)

5. "Deploy!" 버튼을 클릭합니다.

## 5. 앱 사용 방법

1. 앱 URL에 접속합니다.
2. 학번과 이름을 입력하고 "시작하기" 버튼을 클릭합니다.
3. 수학 손글씨 이미지를 업로드합니다.
4. "이미지 처리하기" 버튼을 클릭하여 LaTeX 코드를 추출합니다.
5. 필요한 경우 추출된 LaTeX 코드를 편집합니다.
6. "최종 확인 완료 및 제출" 버튼을 클릭하여 결과를 저장합니다:
   - 이미지는 지정된 Google Drive 폴더에 저장됩니다.
   - LaTeX 코드는 Google Sheets 스프레드시트에 저장됩니다.

## 6. 확인 방법

- 제출된 이미지는 [Google Drive 폴더](https://drive.google.com/drive/folders/1RbNytjT2LMeZQiFRBZQgJKbnro2xqLdB)에서 확인할 수 있습니다.
- 제출된 LaTeX 코드와 학생 정보는 [Google Sheets 스프레드시트](https://docs.google.com/spreadsheets/d/1pOLX2N2ShTkafQcid-EPmnQ9gMxoTLzMmkqfoHvYUFE/edit)에서 확인할 수 있습니다.

## 7. 문제 해결

### 구글 API 접근 오류
- 서비스 계정에 Drive API와 Sheets API가 활성화되어 있는지 확인합니다.
- 드라이브 폴더와 스프레드시트가 서비스 계정 이메일과 올바르게 공유되었는지 확인합니다.

### Streamlit Cloud 배포 오류
- 시크릿이 올바르게 설정되었는지 확인합니다.
- 서비스 계정 JSON이 올바른 형식으로 추가되었는지 확인합니다.
- # Google Cloud 서비스 계정 설정 상세 가이드

이 가이드는 수학 손글씨 LaTeX 변환기 애플리케이션을 위한 Google Cloud 서비스 계정을 설정하는 방법을 단계별로 설명합니다.

## 1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
2. 상단 메뉴바에서 프로젝트 선택 드롭다운을 클릭합니다.
3. "새 프로젝트" 버튼을 클릭합니다.
4. 프로젝트 이름(예: "Math-LaTeX-Converter")을 입력하고 "만들기" 버튼을 클릭합니다.
5. 프로젝트가 생성될 때까지 잠시 기다립니다.

## 2. API 활성화

새로 생성한 프로젝트에서 다음 API를 활성화해야 합니다:

1. 왼쪽 메뉴에서 "API 및 서비스" > "라이브러리"를 선택합니다.
2. 검색창에 "Google Drive API"를 입력하고 검색 결과에서 선택합니다.
3. "사용 설정" 버튼을 클릭합니다.
4. 같은 과정을 반복하여 "Google Sheets API"도 활성화합니다.

## 3. 서비스 계정 생성

1. 왼쪽 메뉴에서 "API 및 서비스" > "사용자 인증 정보"를 선택합니다.
2. 상단의 "사용자 인증 정보 만들기" 버튼을 클릭하고 드롭다운 메뉴에서 "서비스 계정"을 선택합니다.
3. 서비스 계정 세부정보를 입력합니다:
   - 서비스 계정 이름: "math-latex-converter"
   - 서비스 계정 ID: 자동 생성됨 (변경 가능)
   - 서비스 계정 설명: "수학 손글씨 LaTeX 변환기를 위한 서비스 계정"
4. "만들고 계속하기" 버튼을 클릭합니다.
5. 역할 부여 단계에서 다음 역할을 추가합니다:
   - "기본" 카테고리 > "편집자"
6. "계속" 버튼을 클릭합니다.
7. (선택 사항) 추가 사용자에게 이 서비스 계정에 대한 접근 권한을 부여할 수 있습니다.
8. "완료" 버튼을 클릭합니다.

## 4. 서비스 계정 키 생성

1. 서비스 계정 목록에서 방금 생성한 서비스 계정을 찾습니다.
2. 서비스 계정의 이메일 주소를 메모해둡니다 (예: math-latex-converter@project-id.iam.gserviceaccount.com).
3. 해당 서비스 계정 행의 오른쪽에 있는 "작업" 메뉴(세로 점 세 개)를 클릭합니다.
4. "키 관리"를 선택합니다.
5. "키 추가" > "새 키 만들기"를 클릭합니다.
6. 키 유형으로 "JSON"을 선택하고 "만들기" 버튼을 클릭합니다.
7. 서비스 계정 키 파일이 자동으로 다운로드됩니다. 이 파일은 안전한 곳에 보관하세요.

## 5. 다운로드한 JSON 키 파일 사용

다운로드한 서비스 계정 키 JSON 파일의 내용을 `.streamlit/secrets.toml` 파일의 `[gcp_service_account]` 섹션에 추가해야 합니다.

1. 다운로드한 JSON 파일을 텍스트 편집기로 엽니다.
2. 파일 내용을 복사합니다.
3. `.streamlit/secrets.toml` 파일을 생성하고 다음 형식으로 내용을 작성합니다:

```toml
# OpenAI API 키 설정
OPENAI_API_KEY = "your-openai-api-key-here"

# 구글 드라이브 폴더 ID (이미지가 저장될 폴더)
DRIVE_FOLDER_ID = "1RbNytjT2LMeZQiFRBZQgJKbnro2xqLdB"

# 구글 스프레드시트 ID (LaTeX 코드가 저장될 시트)
SPREADSHEET_ID = "1pOLX2N2ShTkafQcid-EPmnQ9gMxoTLzMmkqfoHvYUFE"

# Google Cloud 서비스 계정 정보
[gcp_service_account]
```

4. `[gcp_service_account]` 아래에 JSON 파일의 내용을 구조에 맞게 추가합니다:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"  # JSON에서 복사
private_key_id = "abc123..."    # JSON에서 복사
private_key = """-----BEGIN PRIVATE KEY-----
복사한 private_key 내용
-----END PRIVATE KEY-----
"""
client_email = "math-latex-converter@project-id.iam.gserviceaccount.com"  # JSON에서 복사
client_id = "123456789"         # JSON에서 복사
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/math-latex-converter%40project-id.iam.gserviceaccount.com"  # JSON에서 복사
```

참고: `private_key` 값은 여러 줄로 구성되어 있으므로, 위 예시처럼 삼중 따옴표(`"""`)로 감싸야 합니다.

## 6. Google 리소스 공유 설정

마지막으로, 생성한 서비스 계정에 Google Drive 폴더와 Google Sheets 스프레드시트에 대한 접근 권한을 부여해야 합니다.

### 드라이브 폴더 공유
1. [Google Drive](https://drive.google.com/)에 접속합니다.
2. 지정된 폴더(ID: 1RbNytjT2LMeZQiFRBZQgJKbnro2xqLdB)를 찾습니다.
3. 폴더를 우클릭하고 "공유"를 선택합니다.
4. "사용자 및 그룹 추가" 필드에 서비스 계정 이메일 주소를 입력합니다.
5. 권한을 "편집자"로 설정합니다.
6. (선택 사항) "알림 보내기" 체크박스의 선택을 해제합니다.
7. "공유" 버튼을 클릭합니다.

### 스프레드시트 공유
1. [Google Sheets](https://docs.google.com/spreadsheets/)에 접속합니다.
2. 지정된 스프레드시트(ID: 1pOLX2N2ShTkafQcid-EPmnQ9gMxoTLzMmkqfoHvYUFE)를 엽니다.
3. 오른쪽 상단의 "공유" 버튼을 클릭합니다.
4. "사용자 및 그룹 추가" 필드에 서비스 계정 이메일 주소를 입력합니다.
5. 권한을 "편집자"로 설정합니다.
6. (선택 사항) "알림 보내기" 체크박스의 선택을 해제합니다.
7. "공유" 버튼을 클릭합니다.

## 7. 로컬 테스트

설정이 완료되면 로컬에서 앱을 테스트해볼 수 있습니다:

1. 필요한 패키지를 설치합니다: `pip install -r requirements.txt`
2. Streamlit 앱을 실행합니다: `streamlit run app.py`
3. 웹 브라우저에서 `http://localhost:8501`로 접속하여 앱이 정상적으로 작동하는지 확인합니다.

## 주의사항

- 서비스 계정 키는 매우 중요한 보안 정보입니다. 절대 GitHub와 같은 공개 저장소에 업로드하지 마세요.
- `.gitignore` 파일에 `.streamlit/secrets.toml`이 포함되어 있는지 확인하세요.
- Streamlit Cloud에 배포할 때는 웹 인터페이스의 "Secrets" 섹션에 같은 정보를 추가해야 합니다.
