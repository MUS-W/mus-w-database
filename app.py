import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import altair as alt
from datetime import datetime
import time

# ================= 1. ตั้งค่าหน้าจอและดีไซน์ (CSS) =================
st.set_page_config(
    page_title="MUS-W Dashboard", 
    layout="centered",
    page_icon="https://drive.google.com/uc?id=1X1y3I9VpW6-oE6p1K9rVv0lT_4-Nf6p-&v=3"
)

st.markdown("""
<style>
    .stApp { background-color: #E5E5E5; }
    header { visibility: hidden; }
    .stApp, .stApp p, .stApp span, .stApp label, .stRadio label { color: #000000 !important; }

    .mus-header {
        background-color: #f00a0a;
        color: white !important;
        text-align: center;
        padding: 10px;
        font-size: 48px;
        font-weight: bold;
        border-radius: 15px 15px 15px 15px;
        margin-top: -70px;
        margin-bottom: 20px;
    }

    div.stButton > button, div.stFormSubmitButton > button, div.stDownloadButton > button {
        background-color: #f00a0a !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        height: 50px !important;
        font-size: 18px !important;
    }

    .stTextInput input, .stDateInput input {
        background-color: #F0F0F0 !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #F0F0F0 !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }

    .result-box {
        background-color: #D9D9D9;
        text-align: center;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #CCCCCC;
        margin-top: 15px;
    }

    [data-testid="stElementToolbar"] { display: none !important; }
    
    /* 💡 ไม้ตายล็อกสีตัวอักษรในตารางให้เป็นสีดำ 100% */
    .white-table {
        background-color: white !important;
        border-collapse: collapse !important;
        width: 100% !important;
    }
    .white-table, .white-table th, .white-table td, .white-table tr, .white-table * {
        color: #000000 !important; 
    }
    .white-table th, .white-table td {
        border: 1px solid #CCCCCC !important;
        padding: 10px !important;
        text-align: center !important;
    }
    .white-table th { background-color: #f2f2f2 !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.authenticated: return True
    st.markdown('<div class="mus-header">LOGIN</div>', unsafe_allow_html=True)
    with st.container():
        st.write("---")
        pwd = st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน:", type="password")
        if st.button("เข้าสู่ระบบ", use_container_width=True):
            if pwd == "musw1234":
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("รหัสผ่านไม่ถูกต้อง!")
    return False

if check_password():
    conn = st.connection("gsheets", type=GSheetsConnection)
    def get_data(): return conn.read(worksheet="Kickless", ttl="1s")
    st.markdown('<div class="mus-header">MUS-W</div>', unsafe_allow_html=True)
    main_tab, tab_other1, tab_other2 = st.tabs(["Kickless", "Welding Transformer", "Other"])
    with main_tab:
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🔍 ค้นหาข้อมูล", "⚙️ จัดการข้อมูล/อัพเดท", "📊 ภาพรวม"])

        # -------- แท็บ 1: ค้นหา (ค้นหาด้วยชื่อ Machine เต็มเหมือนเดิม) --------
        with sub_tab1:
            df = get_data()
            machine_list = df['Cable_Name'].unique().tolist() if not df.empty else []
            search_kw = st.text_input("🔍 พิมพ์ชื่อ Machine (เช่น M1G1) เพื่อค้นหา:", key="search1")
            filtered = [m for m in machine_list if str(search_kw).lower().strip() in str(m).lower()] if search_kw else machine_list
            selected_m = st.selectbox("เลือก Machine จากรายการ", ["-- กรุณาเลือกเครื่อง --"] + filtered, index=1 if (search_kw and filtered) else 0)
            
            if st.button("ค้นหาข้อมูลล่าสุด", use_container_width=True):
                if selected_m != "-- กรุณาเลือกเครื่อง --":
                    latest = df[df['Cable_Name'] == selected_m].iloc[-1]
                    spec = f" (สเปค: {latest['Cable_Spec']})" if 'Cable_Spec' in latest else ""
                    st.markdown(f'<div class="result-box"><div style="color:#333;">-- วันที่เปลี่ยนสายล่าสุด {spec} --</div><div class="result-date" style="font-size:38px; font-weight:bold; color:black;">{latest["Last_Changed_Date"]}</div></div>', unsafe_allow_html=True)

        # -------- แท็บ 2: จัดการข้อมูล (กล่องเลือก 3 ส่วน) --------
        with sub_tab2:
            mode = st.radio("โหมด:", ["อัพเดทสายเดิม", "ลงข้อมูลสายใหม่"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("**⚙️ ระบุชื่อ Machine:**")
            col_m1, col_m2, col_m3 = st.columns([1, 2, 1])
            with col_m1: m_prefix = st.selectbox("Tranformer", ["M", "U", "D", "A", "Z"])
            with col_m2: m_number = st.text_input("Number", placeholder="เช่น 1, 2, 10")
            with col_m3: m_group = st.selectbox("Gun", ["G1", "G2"])
            
            # รวมร่างชื่อ Machine
            m_full_name = f"{m_prefix}{m_number}{m_group}"

            c_spec = st.selectbox("เลือกสเปคสาย:", ["150 sq.mm * 2.4 m", "150 sq.mm * 3.0 m", "200 sq.mm * 2.4 m", "200 sq.mm * 3.0 m", "N/A"])

            with st.form("input_form", clear_on_submit=True):
                st.markdown("**📅 กำหนดวันที่และเวลา (ใส่ N/A ได้):**")
                d = st.date_input("เลือกวันที่")
                now = datetime.now()
                col_h, col_m = st.columns(2)
                with col_h: h = st.selectbox("ชั่วโมง", ["N/A"] + [f"{i:02d}" for i in range(24)], index=now.hour + 1)
                with col_m: m = st.selectbox("นาที", ["N/A"] + [f"{i:02d}" for i in range(60)], index=now.minute + 1)
                
                if st.form_submit_button("บันทึกข้อมูล", use_container_width=True):
                    if not m_number:
                        st.error("กรุณาใส่ตัวเลขชื่อ Machine!")
                    else:
                        with st.spinner('กำลังบันทึก...'):
                            dt_str = f"{d.strftime('%d-%m-%Y')} N/A" if (h=="N/A" or m=="N/A") else f"{d.strftime('%d-%m-%Y')} {h}.{m}"
                            new_row = pd.DataFrame([{"Cable_Name": m_full_name, "Cable_Spec": c_spec, "Last_Changed_Date": dt_str}])
                            conn.update(worksheet="Kickless", data=pd.concat([get_data(), new_row], ignore_index=True))
                            time.sleep(1)
                        st.toast(f"บันทึกเครื่อง {m_full_name} เรียบร้อย! ✅")
                        st.cache_data.clear()

        # -------- แท็บ 3: ภาพรวม (ล็อกสีดำทุกจุด) --------
        with sub_tab3:
            st.markdown("### 📊 สรุปการเปลี่ยนสายรายเดือน")
            df_chart = get_data().copy()
            if not df_chart.empty:
                df_chart['Date'] = pd.to_datetime(df_chart['Last_Changed_Date'].astype(str).str[:10], format='%d-%m-%Y', errors='coerce')
                df_chart = df_chart.dropna(subset=['Date'])
                if not df_chart.empty:
                    df_chart['Month'] = df_chart['Date'].dt.strftime('%m-%Y') 
                    summary = df_chart.groupby(['Month', 'Cable_Name']).size().reset_index(name='Count')
                    chart = alt.Chart(summary).mark_bar().encode(
                        x=alt.X('Month:N', title='เดือน-ปี'), y=alt.Y('Count:Q', title='ครั้ง', axis=alt.Axis(tickMinStep=1)),
                        color=alt.Color('Cable_Name:N', title='Machine'), xOffset='Cable_Name:N'
                    ).properties(height=350, background='white').configure_axis(labelColor='black', titleColor='black', domainColor='black', tickColor='black', gridColor='#f0f0f0'
                    ).configure_legend(titleColor='black', labelColor='black').configure_view(strokeWidth=0)
                    
                    st.altair_chart(chart, use_container_width=True, theme=None)
                    pivot = summary.pivot(index='Cable_Name', columns='Month', values='Count').fillna(0).astype(int)
                    st.markdown(pivot.to_html(classes='white-table'), unsafe_allow_html=True)
                    csv = pivot.to_csv().encode('utf-8-sig')
                    st.download_button("📥 ดาวน์โหลดข้อมูลสรุป (CSV)", data=csv, file_name="Summary.csv", mime="text/csv", use_container_width=True)
                else: st.info("ไม่พบข้อมูลวันที่ครับ")
            else: st.info("ยังไม่มีข้อมูลในระบบ")

    with tab_other1: st.info("Coming Soon")
    with tab_other2: st.info("Coming Soon")
