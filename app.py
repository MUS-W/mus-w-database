import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ================= 1. ตั้งค่าหน้าจอและดีไซน์ (CSS) =================
st.set_page_config(page_title="MUS-W Dashboard", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #E5E5E5; }
    header { visibility: hidden; }
    .mus-header {
        background-color: #C00000;
        color: white;
        text-align: center;
        padding: 15px;
        font-size: 28px;
        font-weight: bold;
        border-radius: 0 0 15px 15px;
        margin-top: -70px;
        margin-bottom: 20px;
    }
    div.stButton > button:first-child {
        background-color: #C00000;
        color: white;
        border-radius: 8px;
        border: none;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
    }
    .result-box {
        background-color: #D9D9D9;
        text-align: center;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #CCCCCC;
        margin-top: 15px;
    }
    .result-date {
        font-size: 38px;
        font-weight: bold;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. ระบบรักษาความปลอดภัย (Login) =================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.authenticated:
        return True
    
    st.markdown('<div class="mus-header">MUS-W LOGIN</div>', unsafe_allow_html=True)
    with st.container():
        st.write("---")
        pwd = st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน:", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == "musw1234":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("รหัสผ่านไม่ถูกต้อง!")
    return False

if check_password():
    # ================= 3. เชื่อมต่อ Google Sheets =================
    # หมายเหตุ: URL จะไปใส่ใน Streamlit Secrets ตอน Deploy
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    def get_data():
        return conn.read(worksheet="Kickless", ttl="1s")

    # ส่วนหัวแอปหลังล็อกอิน
    st.markdown('<div class="mus-header">MUS-W</div>', unsafe_allow_html=True)

    main_tab, tab_other1, tab_other2 = st.tabs(["🗲 Kickless", "Welding Transformer", "Other"])

    with main_tab:
        sub_tab1, sub_tab2 = st.tabs(["🔍 ค้นหาข้อมูล", "⚙️ จัดการข้อมูล/อัพเดท"])

        # -------- หน้าค้นหา --------
        with sub_tab1:
            df = get_data()
            cable_list = df['Cable_Name'].unique().tolist() if not df.empty else []
            
            selected = st.selectbox("เลือกรหัสสาย Kickless (พิมพ์ค้นหาได้)", ["-- กรุณาเลือกสาย --"] + cable_list)
            
            if st.button("ค้นหาข้อมูลล่าสุด", use_container_width=True):
                if selected == "-- กรุณาเลือกสาย --":
                    st.warning("กรุณาเลือกสายก่อนครับ")
                else:
                    latest = df[df['Cable_Name'] == selected].iloc[-1]
                    st.markdown(f"""
                    <div class="result-box">
                        <div style="color:#333; font-weight:bold;">-- วันที่เปลี่ยนสายล่าสุด --</div>
                        <div class="result-date">{latest['Last_Changed_Date']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # -------- หน้าจัดการข้อมูล --------
        with sub_tab2:
            mode = st.radio("โหมด:", ["อัพเดทสายเดิม", "ลงข้อมูลสายใหม่"], horizontal=True, label_visibility="collapsed")
            
            with st.form("input_form", clear_on_submit=True):
                if mode == "ลงข้อมูลสายใหม่":
                    c_name = st.text_input("ชื่อ/รหัส สาย Kickless เส้นใหม่:")
                else:
                    c_name = st.selectbox("เลือกสายเดิม:", cable_list if cable_list else ["ไม่มีข้อมูล"])
                
                col1, col2 = st.columns(2)
                d = col1.date_input("วันที่")
                t = col2.time_input("เวลา")
                
                if st.form_submit_button("บันทึกข้อมูล", use_container_width=True):
                    if not c_name or c_name == "ไม่มีข้อมูล":
                        st.error("ข้อมูลไม่ครบ!")
                    else:
                        dt_str = f"{d.strftime('%d-%m-%Y')} {t.strftime('%H.%M')}"
                        new_data = pd.DataFrame([{"Cable_Name": c_name, "Last_Changed_Date": dt_str}])
                        
                        # อัปเดตข้อมูลลง Google Sheets
                        updated_df = pd.concat([get_data(), new_data], ignore_index=True)
                        conn.update(worksheet="Kickless", data=updated_df)
                        st.success("บันทึกข้อมูลลง Google Sheets เรียบร้อย!")
                        st.cache_data.clear()

    with tab_other1: st.info("Coming Soon")
    with tab_other2: st.info("Coming Soon")