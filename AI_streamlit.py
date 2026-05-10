import streamlit as st
import pandas as pd
import os
import joblib
import plotly.graph_objects as go
import plotly.express as px

# ==========================================
# 1. 상수 및 기본 설정 데이터
# ==========================================
BEST_METRICS = {
    'scratch': {
        'reg': {'RMSE': '2.5123', 'R2': '0.4253', 'Model': 'RandomForest'},
        'class': {'Acc': '0.7769', 'F1': '0.4255', 'Model': 'XGBoost', 'CM': [[450, 15], [30, 123]]}
    },
    'cleaning': {
        'reg': {'RMSE': '3.2267', 'R2': '0.3125', 'Model': 'RandomForest'},
        'class': {'Acc': '0.6777', 'F1': '0.5517', 'Model': 'XGBoost', 'CM': [[352, 45], [55, 196]]}
    },
    'sealant': {
        'reg': {'RMSE': '2.4524', 'R2': '0.7287', 'Model': 'RandomForest'},
        'class': {'Acc': '0.7934', 'F1': '0.7748', 'Model': 'XGBoost', 'CM': [[312, 30], [25, 266]]}
    },
    'install': {
        'reg': {'RMSE': '1.0915', 'R2': '0.7514', 'Model': 'RandomForest'},
        'class': {'Acc': '0.9256', 'F1': '0.8831', 'Model': 'RandomForest', 'CM': [[451, 10], [5, 147]]}
    }
}

WORKER_MAP = {
    'M_FAJ': sorted(['이준호', '정현우']),
    'M_Install': sorted(['강동원', '송중기', '유재석']),
    'M_Sealant': sorted(['김태희', '송혜교', '전지현']),
    'M_Hole': sorted(['남주혁', '박보검']),
    'QI': sorted(['김철민', '박지용', '최윤석'])
}

REQUIRED_FEATURES = [
    'QI', 'M_FAJ', 'M_Install', 'M_Sealant', 'M_Hole', 
    'Temp_FAJ', 'Temp_Install', 'Temp_Sealant', 'Temp_Hole', 
    'RH_FAJ', 'RH_Install', 'RH_Silent', 'RH_Hole', 
    'Storage_RH', 'Storage_Temp', 'Storage_Pa', 'Weight', 
    'worktime_loading', 'worktime_setting', 'worktime_drilling', 
    'worktime_Unloading', 'worktime_sealing', 'waiting_sealing', 
    'Month', 'Hour'
]

# ==========================================
# 2. 데이터 로드 및 통계량 추출 (캐싱)
# ==========================================
@st.cache_data
def get_feature_stats(data_path):
    feature_stats = {}
    try:
        df = pd.read_excel(data_path)
        if 'final_Date' in df.columns:
            df['final_Date'] = pd.to_datetime(df['final_Date'])
            df['Month'] = df['final_Date'].dt.month
            df['Hour'] = df['final_Date'].dt.hour
            
        for col in REQUIRED_FEATURES:
            if col not in WORKER_MAP:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    feature_stats[col] = {'default': float(df[col].mean()), 'min': float(df[col].min()), 'max': float(df[col].max())}
                else:
                    feature_stats[col] = {'default': 0.0, 'min': 0.0, 'max': 100.0}
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        # 실패 시 기본값 세팅
        for col in REQUIRED_FEATURES:
            if col not in WORKER_MAP:
                feature_stats[col] = {'default': 0.0, 'min': 0.0, 'max': 100.0}
    return feature_stats

def get_filtered_models(directory, model_type):
    if not os.path.exists(directory): 
        return []
    files = [f for f in os.listdir(directory) if f.endswith('.pkl')]
    if model_type == 'class': 
        return [f for f in files if f != 'model_features.pkl']
    if model_type == 'reg': 
        return [f for f in files if 'CatBoost' not in f]
    return files

# ==========================================
# 3. 메인 UI 구성
# ==========================================
def create_ai_simulator():
    # [수정] 절대 경로(C:\...) 대신 현재 실행 경로('.')를 사용합니다.
    base_dir = '.' 
    data_path = os.path.join(base_dir, 'aircraft_parts_virtual_data_v3.xlsx')
    
    # 모델 폴더 경로도 현재 폴더 기준으로 설정
    class_model_dir = os.path.join(base_dir, 'saved_model_class')
    reg_model_dir = os.path.join(base_dir, 'saved_models_reg')
    
    feature_stats = get_feature_stats(data_path)

    # ------------------------------------------
    # 레이아웃 분할: 좌측(시뮬레이터 70%), 우측(평가지표 30%)
    # ------------------------------------------
    col_main, col_sidebar = st.columns([7, 3])

    # --- 우측: 성능 지표 사이드바 (평가지표 렌더링용 변수 미리 선언) ---
    m_type_key = None
    target_key = None
    m_file = None

    # --- 좌측 영역 ---
    with col_main:
        st.markdown("---")

        with st.container(border=True):
            st.markdown("#### 1. 시뮬레이션 모델 선택")
            c1, c2 = st.columns(2)
            with c1:
                model_type_select = st.selectbox('모델 종류', ['분류(Classification)', '회귀(Regression)'])
            
            # 모델 타입에 따라 파일 리스트 갱신
            m_type_key = 'class' if model_type_select == '분류(Classification)' else 'reg'
            model_dir = class_model_dir if m_type_key == 'class' else reg_model_dir
            model_files = get_filtered_models(model_dir, m_type_key)
            
            with c2:
                m_file = st.selectbox('모델 파일 선택', model_files if model_files else ["모델 없음"])

        with st.container(border=True):
            st.markdown("#### 2. 공정 파라미터 조정")
            
            # 4열 그리드 배치
            input_cols = st.columns(4)
            state_inputs = {}
            
            for i, col in enumerate(REQUIRED_FEATURES):
                with input_cols[i % 4]:
                    if col in WORKER_MAP:
                        state_inputs[col] = st.selectbox(f' {col}', options=WORKER_MAP[col])
                    elif col in ['Month', 'Hour']:
                        val = feature_stats.get(col, {'default': 0})['default']
                        state_inputs[col] = st.number_input(f' {col}', value=int(val), step=1)
                    else:
                        stat = feature_stats.get(col, {'default': 0.0})
                        state_inputs[col] = st.number_input(f'{col}', value=float(stat['default']), format="%.2f")

        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button(" 시뮬레이션 실행", type="primary", use_container_width=True)
        
        # --- 시뮬레이션 실행 로직 ---
        if run_btn:
            if m_file == "모델 없음" or not m_file:
                st.warning("선택된 모델 파일이 없습니다.")
            else:
                try:
                    model_path = os.path.join(model_dir, m_file)
                    model = joblib.load(model_path)
                    
                    # 입력 데이터 구성
                    input_row = {}
                    for col in REQUIRED_FEATURES:
                        raw_val = state_inputs[col]
                        input_row[col] = [WORKER_MAP[col].index(raw_val)] if col in WORKER_MAP else [raw_val]
                    
                    input_df = pd.DataFrame(input_row)
                    prediction = model.predict(input_df)[0]
                    
                    # 결과 출력
                    with st.container(border=True):
                        st.markdown("###  예측 결과")
                        if m_type_key == 'class':
                            if prediction == 0:
                                st.success(" 정상 (Normal)")
                            else:
                                st.error(" 불량 (Defect)")
                        else:
                            st.info(f" 예측 수치: **{prediction:.4f}**")
                    
                    # 영향 인자(Feature Importance) 분석 레이더 차트
                    if hasattr(model, 'feature_importances_'):
                        st.markdown("####  영향 인자 분석")
                        imp = model.feature_importances_
                        imp_df = pd.DataFrame({'Feature': REQUIRED_FEATURES, 'Importance': imp}).sort_values('Importance', ascending=False).head(10)
                        
                        fig = go.Figure(go.Scatterpolar(
                            r=imp_df['Importance'].tolist() + [imp_df['Importance'].iloc[0]], 
                            theta=imp_df['Feature'].tolist() + [imp_df['Feature'].iloc[0]], 
                            fill='toself'
                        ))
                        fig.update_layout(polar=dict(radialaxis=dict(visible=False)), margin=dict(l=40, r=40, t=40, b=40))
                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"시뮬레이션 실행 중 오류 발생: {e}")

    # --- 우측 영역 (평가 지표) ---
    with col_sidebar:
        st.markdown("###  모델 평가 지표")
        
        with st.container(border=True):
            if not m_file or m_file == "모델 없음":
                st.write("모델을 선택해주세요.")
            else:
                st.markdown(f"**{m_file}**")
                st.divider()
                
                # 파일명에서 타겟 키워드 추출
                m_file_lower = m_file.lower()
                for key in ['scratch', 'cleaning', 'sealant', 'install']:
                    if key in m_file_lower:
                        target_key = key
                        break
                
                if target_key and target_key in BEST_METRICS:
                    data = BEST_METRICS[target_key][m_type_key]
                    
                    if m_type_key == 'reg':
                        st.caption("회귀 성능 (Best)")
                        st.metric("RMSE", data['RMSE'])
                        st.metric("R² Score", data['R2'])
                        st.info(f"Model: {data['Model']}")
                    else:
                        st.caption("분류 성능 (Best)")
                        st.metric("정확도 (Accuracy)", data['Acc'])
                        st.metric("F1-Score", data['F1'])
                        st.success(f"Model: {data['Model']}")
                        
                        # 혼동 행렬 시각화
                        st.markdown("###### 혼동 행렬 (Confusion Matrix)")
                        fig_cm = px.imshow(
                            data['CM'],
                            labels=dict(x="예측 값", y="실제 값", color="건수"),
                            x=['정상(0)', '불량(1)'],
                            y=['정상(0)', '불량(1)'],
                            text_auto=True,
                            color_continuous_scale='Blues'
                        )
                        fig_cm.update_layout(width=300, height=300, margin=dict(l=20, r=20, t=20, b=20), coloraxis_showscale=False)
                        st.plotly_chart(fig_cm, use_container_width=True)
                else:
                    st.warning("지표 매칭 실패: 파일명에 키워드(scratch 등)가 포함되어 있는지 확인하세요.")
