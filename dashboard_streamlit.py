import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 데이터 로드 및 전처리 (캐싱 적용)
# ==========================================
@st.cache_data
def load_data():
    file_path = 'aircraft_parts_virtual_data_v3.xlsx'
    try:
        df = pd.read_excel(file_path)
        # 날짜 데이터에서 '년-월' 컬럼 추출
        df['YearMonth'] = df['final_Date'].dt.to_period('M').astype(str)
        
        # 각 row별 총 불량 건수 합산 (새로운 컬럼 생성)
        df['Total_Defects'] = df['scratch'] + df['cleaning'] + df['sealant'] + df['Install_error']
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# ==========================================
# 2. 대시보드 UI 구성
# ==========================================
def create_dashboard():
    df = load_data()
    
    st.markdown("##  품질관리 KPI 대시보드")
    st.markdown("---")

    # ------------------------------------------
    # Row 1: 월별 생산량 & 타겟 컬럼(결함) 추이
    # ------------------------------------------
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#####  월별 부품 출하(생산)량")
        with st.container(border=True):
            if not df.empty:
                prod_df = df.groupby('YearMonth')['LN'].nunique().reset_index()
                prod_df.rename(columns={'LN': '생산량(LN 기준)'}, inplace=True)
                
                fig_prod = px.bar(prod_df, x='YearMonth', y='생산량(LN 기준)', text_auto=True, color_discrete_sequence=['#3b82f6'])
                fig_prod.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="출하 월", yaxis_title="출하량 (개)")
                st.plotly_chart(fig_prod, use_container_width=True)

    with col2:
        st.markdown("#####  월별 주요 결함 평균 발생 추이")
        with st.container(border=True):
            if not df.empty:
                target_cols = ['scratch', 'cleaning', 'sealant', 'Install_error']
                trend_df = df.groupby('YearMonth')[target_cols].mean().reset_index()
                
                fig_trend = go.Figure()
                for col in target_cols:
                    fig_trend.add_trace(go.Scatter(x=trend_df['YearMonth'], y=trend_df[col], mode='lines+markers', name=col))
                
                fig_trend.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="출하 월", yaxis_title="평균 결함 수", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True) # 여백

    # ------------------------------------------
    # Row 2: 각 공정별 온도 및 습도 그래프
    # ------------------------------------------
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#####  공정별 월별 평균 온도 추이")
        with st.container(border=True):
            if not df.empty:
                temp_cols = ['Temp_FAJ', 'Temp_Install', 'Temp_Sealant', 'Temp_Hole']
                temp_df = df.groupby('YearMonth')[temp_cols].mean().reset_index()
                
                fig_temp = px.line(temp_df, x='YearMonth', y=temp_cols, markers=True)
                fig_temp.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="출하 월", yaxis_title="온도 (°C)", legend_title="작업 공정")
                st.plotly_chart(fig_temp, use_container_width=True)

    with col4:
        st.markdown("#####  공정별 월별 평균 습도 추이")
        with st.container(border=True):
            if not df.empty:
                rh_cols = ['RH_FAJ', 'RH_Install', 'RH_Silent', 'RH_Hole']
                rh_df = df.groupby('YearMonth')[rh_cols].mean().reset_index()
                
                fig_rh = px.line(rh_df, x='YearMonth', y=rh_cols, markers=True)
                fig_rh.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title="출하 월", yaxis_title="상대습도 (%)", legend_title="작업 공정")
                st.plotly_chart(fig_rh, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True) # 여백

    # ------------------------------------------
    # Row 3: 월별 공정별 작업자 작업 건수
    # ------------------------------------------
    st.markdown("###  월별 공정별 작업자 작업 건수")
    
    worker_cols = ['M_FAJ', 'M_Install', 'M_Sealant', 'M_Hole', 'QI']
    process_names = {'M_FAJ': 'FAJ 공정', 'M_Install': 'Install 공정', 'M_Sealant': 'Sealant 공정', 'M_Hole': 'Hole 공정', 'QI': '최종 품질검사(QI)'}
    
    # 3열 형태로 배치 (총 5개이므로 3개 / 2개 나뉘어 출력됨)
    worker_columns = st.columns(3)
    
    for i, col in enumerate(worker_cols):
        with worker_columns[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{process_names[col]}**")
                if not df.empty:
                    worker_df = df.groupby(['YearMonth', col]).size().reset_index(name='작업 건수')
                    worker_df.rename(columns={col: '작업자명'}, inplace=True)
                    
                    fig_worker = px.bar(worker_df, x='YearMonth', y='작업 건수', color='작업자명', text_auto=True)
                    fig_worker.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="출하 월", yaxis_title="작업 건수", legend_title="작업자명")
                    st.plotly_chart(fig_worker, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True) # 여백

    # ------------------------------------------
    # Row 4: 작업자별 평균 작업 1개당 불량 발생 건수
    # ------------------------------------------
    st.markdown("###  작업자별 평균 작업 1개당 불량 발생 건수")
    
    with st.container(border=True):
        if not df.empty:
            target_worker_cols = ['M_FAJ', 'M_Install', 'M_Sealant', 'M_Hole']
            melted_df = df.melt(id_vars=['Total_Defects'], value_vars=target_worker_cols, var_name='공정', value_name='작업자명')
            
            defect_df = melted_df.groupby(['공정', '작업자명'])['Total_Defects'].agg(
                총불량건수='sum',
                작업건수='count'
            ).reset_index()
            
            defect_df['건당_불량건수'] = (defect_df['총불량건수'] / defect_df['작업건수']).round(3)
            defect_df = defect_df.sort_values(by='건당_불량건수', ascending=False)
            
            fig_defect = px.bar(defect_df, x='작업자명', y='건당_불량건수', color='공정', text_auto='.3f')
            fig_defect.update_layout(
                margin=dict(l=20, r=20, t=20, b=20), 
                xaxis_title="작업자 이름", 
                yaxis_title="평균 작업 1개당 불량 건수",
                legend_title="담당 공정",
                height=500
            )
            
            st.plotly_chart(fig_defect, use_container_width=True)
