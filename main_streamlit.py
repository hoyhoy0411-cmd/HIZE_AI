import streamlit as st
from dashboard_streamlit import create_dashboard # 파일명 변경 반영
from AI_streamlit import create_ai_simulator     # 파일명 변경 반영

# ==========================================
# 0. 페이지 기본 설정 (가장 먼저 선언되어야 함)
# ==========================================
st.set_page_config(
    page_title='하이즈항공 품질 시스템',
    page_icon='',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ==========================================
# 1. 세션 상태 초기화 및 페이지 이동 함수
# ==========================================
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = '홈 화면'

def navigate_to(page_name):
    """버튼 클릭 시 세션 상태를 변경하여 페이지를 전환하는 콜백 함수"""
    st.session_state['current_page'] = page_name

# ==========================================
# 2. 공통 사이드바 네비게이션
# ==========================================
def sidebar_navigation():
    with st.sidebar:
        st.title(' 하이즈항공 플랫폼')
        st.markdown('**AI 품질 통합 플랫폼**')
        st.divider() # 가로줄
        
        # 메뉴 버튼들
        st.button(' 홈 화면', on_click=navigate_to, args=('홈 화면',), use_container_width=True)
        st.button(' KPI 대시보드', on_click=navigate_to, args=('KPI 대시보드',), use_container_width=True)
        st.button(' AI 시뮬레이터', on_click=navigate_to, args=('AI 시뮬레이터',), use_container_width=True)

# ==========================================
# 3. 라우팅 (페이지 분기)
# ==========================================
def main():
    # 항상 좌측에 사이드바 렌더링
    sidebar_navigation()

    # ------------------------------------
    # 홈 화면
    # ------------------------------------
    if st.session_state['current_page'] == '홈 화면':
        # 중앙 정렬을 위해 HTML/CSS 적용
        st.markdown(
            """
            <div style='text-align: center; padding: 50px 0;'>
                <h1 style='font-size: 3rem; color: #1f2937;'>하이즈항공 품질관리 통합 시스템</h1>
                <p style='font-size: 1.2rem; color: #4b5563; margin-bottom: 50px;'>
                    무결점 품질 실현을 위한 데이터 분석 및 AI 예측 플랫폼입니다.
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # 버튼을 가운데로 몰기 위해 빈 컬럼 활용
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        with col2:
            st.button(' KPI 대시보드 바로가기', on_click=navigate_to, args=('KPI 대시보드',), type='primary', use_container_width=True)
        with col3:
            st.button(' AI 시뮬레이터 바로가기', on_click=navigate_to, args=('AI 시뮬레이터',), type='secondary', use_container_width=True)

    # ------------------------------------
    # 대시보드 화면
    # ------------------------------------
    elif st.session_state['current_page'] == 'KPI 대시보드':
        st.header(' KPI 대시보드')
        st.divider()
        create_dashboard()

    # ------------------------------------
    # AI 시뮬레이터 화면
    # ------------------------------------
    elif st.session_state['current_page'] == 'AI 시뮬레이터':
        st.header(' AI 예측 솔루션')
        st.divider()
        create_ai_simulator()

# ==========================================
# 통합 앱 실행
# ==========================================
if __name__ == '__main__':
    main()
