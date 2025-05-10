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

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트를 생성하거나 기존 프로젝트 선택
3. API 및 서비스 > 사용자 인증 정보 > 사용자 인증 정보 만들기 > 서비스 계정
4. 서비스 계정 세부정보 입력 후 생성
5. 서비스 계정에 대한 키 생성 (JSON 형식) 및 다운로드
6. 다운로드한 JSON 파일의 내용을 `.streamlit/secrets.toml` 파일의 `[gcp_service_account]` 섹션에 추가

### 5. Google Drive API 활성화

1. [Google Cloud Console](https://console.cloud.google.com/)에서 Google Drive API 활성화
2. 설정한 서비스 계정에 적절한 권한 부여

### 6. 설정 파일 생성

1. `.streamlit` 폴더
