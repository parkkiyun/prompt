import streamlit as st
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import io
import tempfile

# Google 드라이브 연결 설정
def connect_to_google_drive():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    try:
        # Streamlit Secrets에서 서비스 계정 정보 가져오기
        if 'gcp_service_account' in st.secrets:
            # 서비스 계정 정보를 임시 파일로 저장
            service_account_info = st.secrets["gcp_service_account"]
            service_account_info_str = json.dumps(service_account_info)
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp:
                temp.write(service_account_info_str)
                temp_path = temp.name
            
            # 임시 파일로 인증
            creds = ServiceAccountCredentials.from_json_keyfile_name(temp_path, scope)
            
            # 임시 파일 삭제
            os.unlink(temp_path)
            
        # 로컬 파일에서 서비스 계정 정보 가져오기
        elif os.path.exists('service_account.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        else:
            st.error("서비스 계정 정보를 찾을 수 없습니다. Streamlit Secrets 또는 service_account.json 파일을 설정해주세요.")
            return None
            
        # 서비스 계정 인증
        client = gspread.authorize(creds)
        
        return client
    except Exception as e:
        st.error(f"Google 드라이브 연결 중 오류가 발생했습니다: {str(e)}")
        return None

def get_file_from_drive(file_id):
    """Google 드라이브에서 파일을 가져옵니다."""
    try:
        client = connect_to_google_drive()
        if client is None:
            return None
            
        # 드라이브 API를 통해 파일 가져오기
        file = client.drive.files().get(fileId=file_id, fields="name,mimeType").execute()
        
        # 파일 내용 다운로드
        file_content = client.drive.files().get_media(fileId=file_id).execute()
        
        return file_content
    except Exception as e:
        st.error(f"파일을 가져오는 중 오류가 발생했습니다: {str(e)}")
        return None

def update_file_in_drive(file_id, content):
    """Google 드라이브의 파일을 업데이트합니다."""
    try:
        client = connect_to_google_drive()
        if client is None:
            return False
            
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(content.encode('utf-8'))
            temp_path = temp.name
        
        # 파일 업데이트
        media_body = client.http.MediaFileUpload(
            temp_path,
            mimetype='application/json',
            resumable=True
        )
        
        client.drive.files().update(
            fileId=file_id,
            media_body=media_body
        ).execute()
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        return True
    except Exception as e:
        st.error(f"파일을 업데이트하는 중 오류가 발생했습니다: {str(e)}")
        return False

def load_prompts():
    """Google 드라이브 또는 로컬에서 prompts.json 파일을 로드합니다."""
    # Google 드라이브 파일 ID (Streamlit secrets에서 가져오기)
    file_id = st.secrets.get("PROMPTS_FILE_ID", None)
    
    if file_id:
        # Google 드라이브에서 파일 로드
        file_content = get_file_from_drive(file_id)
        if file_content:
            try:
                return json.loads(file_content.decode('utf-8'))
            except json.JSONDecodeError:
                st.error("JSON 파일 형식이 올바르지 않습니다.")
                return {}
        else:
            # 파일을 가져오지 못한 경우 로컬 파일 시도
            st.warning("Google 드라이브에서 파일을 가져오지 못했습니다. 로컬 파일을 시도합니다.")
    
    # 로컬 파일에서 로드
    try:
        with open('prompts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_prompts(prompts):
    """프롬프트를 Google 드라이브 또는 로컬 파일에 저장합니다."""
    # 프롬프트를 JSON 문자열로 변환
    prompts_json = json.dumps(prompts, ensure_ascii=False, indent=4)
    
    # Google 드라이브 파일 ID (Streamlit secrets에서 가져오기)
    file_id = st.secrets.get("PROMPTS_FILE_ID", None)
    
    if file_id:
        # Google 드라이브에 파일 업데이트
        success = update_file_in_drive(file_id, prompts_json)
        if success:
            return True
        else:
            st.warning("Google 드라이브 업데이트에 실패했습니다. 로컬 파일에 저장을 시도합니다.")
    
    # 로컬 파일에 저장
    try:
        with open('prompts.json', 'w', encoding='utf-8') as f:
            f.write(prompts_json)
        return True
    except Exception as e:
        st.error(f"로컬 파일 저장 중 오류가 발생했습니다: {str(e)}")
        return False

def main():
    st.title("📝 프롬프트 관리")
    
    # 프롬프트 로드
    prompts = load_prompts()
    
    # 파일 원본 소스 표시
    file_id = st.secrets.get("PROMPTS_FILE_ID", None)
    if file_id and 'gcp_service_account' in st.secrets:
        st.info(f"Google 드라이브에서 프롬프트 파일을 불러오는 중입니다.")
    else:
        st.info("로컬 파일에서 프롬프트를 불러오는 중입니다.")
    
    # 사이드바 메뉴
    menu = st.sidebar.selectbox(
        "메뉴 선택",
        ["프롬프트 목록", "새 프롬프트 추가", "프롬프트 수정", "프롬프트 삭제"]
    )
    
    if menu == "프롬프트 목록":
        st.header("📋 프롬프트 목록")
        
        for category, content in prompts.items():
            with st.expander(f"📌 {category}"):
                if isinstance(content, dict) and "system_prompt" in content:
                    # 일반 프롬프트 (진로, 자율, 행특, 동아리)
                    st.subheader("시스템 프롬프트")
                    st.text_area("시스템 프롬프트", content["system_prompt"], height=100, key=f"system_{category}")
                    
                    st.subheader("사용자 프롬프트 템플릿")
                    st.text_area("사용자 프롬프트 템플릿", content["user_prompt_template"], height=300, key=f"user_{category}")
                else:
                    # 교과 프롬프트
                    for subject, subject_content in content.items():
                        st.subheader(f"📚 {subject}")
                        st.text_area("시스템 프롬프트", subject_content["system_prompt"], height=100, key=f"system_{category}_{subject}")
                        st.text_area("사용자 프롬프트 템플릿", subject_content["user_prompt_template"], height=300, key=f"user_{category}_{subject}")
    
    elif menu == "새 프롬프트 추가":
        st.header("➕ 새 프롬프트 추가")
        
        # 프롬프트 유형 선택
        prompt_type = st.radio(
            "프롬프트 유형 선택",
            ["일반 프롬프트", "교과 프롬프트"]
        )
        
        if prompt_type == "일반 프롬프트":
            category = st.text_input("카테고리 (예: 진로, 자율, 행특, 동아리)")
            system_prompt = st.text_area("시스템 프롬프트", height=100)
            user_prompt = st.text_area("사용자 프롬프트 템플릿", height=300)
            
            if st.button("프롬프트 추가"):
                if category and system_prompt and user_prompt:
                    prompts[category] = {
                        "system_prompt": system_prompt,
                        "user_prompt_template": user_prompt
                    }
                    if save_prompts(prompts):
                        st.success("프롬프트가 성공적으로 추가되었습니다!")
                    else:
                        st.error("프롬프트 저장 중 오류가 발생했습니다.")
                else:
                    st.error("모든 필드를 입력해주세요.")
        
        else:  # 교과 프롬프트
            category = "교과"
            subject = st.text_input("교과목 (예: 국어, 수학)")
            system_prompt = st.text_area("시스템 프롬프트", height=100)
            user_prompt = st.text_area("사용자 프롬프트 템플릿", height=300)
            
            if st.button("프롬프트 추가"):
                if subject and system_prompt and user_prompt:
                    if category not in prompts:
                        prompts[category] = {}
                    prompts[category][subject] = {
                        "system_prompt": system_prompt,
                        "user_prompt_template": user_prompt
                    }
                    if save_prompts(prompts):
                        st.success("프롬프트가 성공적으로 추가되었습니다!")
                    else:
                        st.error("프롬프트 저장 중 오류가 발생했습니다.")
                else:
                    st.error("모든 필드를 입력해주세요.")
    
    elif menu == "프롬프트 수정":
        st.header("✏️ 프롬프트 수정")
        
        # 수정할 프롬프트 선택
        categories = list(prompts.keys())
        if not categories:
            st.warning("수정할 프롬프트가 없습니다.")
            return
            
        selected_category = st.selectbox("카테고리 선택", categories)
        
        if selected_category == "교과":
            subjects = list(prompts[selected_category].keys())
            if not subjects:
                st.warning("수정할 교과 프롬프트가 없습니다.")
                return
                
            selected_subject = st.selectbox("교과목 선택", subjects)
            
            st.subheader("시스템 프롬프트")
            system_prompt = st.text_area(
                "시스템 프롬프트",
                prompts[selected_category][selected_subject]["system_prompt"],
                height=100
            )
            
            st.subheader("사용자 프롬프트 템플릿")
            user_prompt = st.text_area(
                "사용자 프롬프트 템플릿",
                prompts[selected_category][selected_subject]["user_prompt_template"],
                height=300
            )
            
            if st.button("프롬프트 수정"):
                prompts[selected_category][selected_subject]["system_prompt"] = system_prompt
                prompts[selected_category][selected_subject]["user_prompt_template"] = user_prompt
                if save_prompts(prompts):
                    st.success("프롬프트가 성공적으로 수정되었습니다!")
                else:
                    st.error("프롬프트 저장 중 오류가 발생했습니다.")
        
        else:
            st.subheader("시스템 프롬프트")
            system_prompt = st.text_area(
                "시스템 프롬프트",
                prompts[selected_category]["system_prompt"],
                height=100
            )
            
            st.subheader("사용자 프롬프트 템플릿")
            user_prompt = st.text_area(
                "사용자 프롬프트 템플릿",
                prompts[selected_category]["user_prompt_template"],
                height=300
            )
            
            if st.button("프롬프트 수정"):
                prompts[selected_category]["system_prompt"] = system_prompt
                prompts[selected_category]["user_prompt_template"] = user_prompt
                if save_prompts(prompts):
                    st.success("프롬프트가 성공적으로 수정되었습니다!")
                else:
                    st.error("프롬프트 저장 중 오류가 발생했습니다.")
    
    elif menu == "프롬프트 삭제":
        st.header("🗑️ 프롬프트 삭제")
        
        # 삭제할 프롬프트 선택
        categories = list(prompts.keys())
        if not categories:
            st.warning("삭제할 프롬프트가 없습니다.")
            return
            
        selected_category = st.selectbox("카테고리 선택", categories)
        
        if selected_category == "교과":
            subjects = list(prompts[selected_category].keys())
            if not subjects:
                st.warning("삭제할 교과 프롬프트가 없습니다.")
                return
                
            selected_subject = st.selectbox("교과목 선택", subjects)
            
            if st.button("프롬프트 삭제", type="primary"):
                confirmation = st.checkbox("정말로 삭제하시겠습니까?")
                if confirmation:
                    del prompts[selected_category][selected_subject]
                    if not prompts[selected_category]:  # 교과 카테고리가 비어있으면
                        del prompts[selected_category]
                    if save_prompts(prompts):
                        st.success("프롬프트가 성공적으로 삭제되었습니다!")
                    else:
                        st.error("프롬프트 저장 중 오류가 발생했습니다.")
        
        else:
            if st.button("프롬프트 삭제", type="primary"):
                confirmation = st.checkbox("정말로 삭제하시겠습니까?")
                if confirmation:
                    del prompts[selected_category]
                    if save_prompts(prompts):
                        st.success("프롬프트가 성공적으로 삭제되었습니다!")
                    else:
                        st.error("프롬프트 저장 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main() 