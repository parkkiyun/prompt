# 프롬프트 관리 시스템

한올고등학교를 위한 프롬프트 관리 시스템입니다. 교과, 진로, 자율, 행특, 동아리 등 다양한 카테고리의 프롬프트를 관리할 수 있습니다.

## 기능

- 프롬프트 목록 조회
- 새 프롬프트 추가
- 프롬프트 수정
- 프롬프트 삭제
- Google Drive 연동을 통한 클라우드 저장

## 설치 방법

1. 저장소 클론
   ```
   git clone https://github.com/사용자명/hanol_database_prompt.git
   cd hanol_database_prompt
   ```

2. 필요한 패키지 설치
   ```
   pip install -r requirements.txt
   ```

3. 서비스 계정 설정
   - Google Cloud Platform에서 서비스 계정 생성
   - 서비스 계정 키(JSON) 다운로드 후 프로젝트 루트에 `service_account.json` 이름으로 저장
   - Google Drive API와 Google Sheets API 활성화

4. Streamlit 비밀 설정
   - `.streamlit/secrets.toml` 파일 생성
   - 다음 내용 추가:
     ```
     PROMPTS_FILE_ID = "Google_드라이브_파일_ID"
     ```

## 실행 방법

```
streamlit run prompt_manager.py
```

## 배포

Streamlit Sharing, Heroku 등에 배포 가능합니다. 배포 시 서비스 계정 정보와 비밀 설정을 환경에 맞게 구성해주세요. 