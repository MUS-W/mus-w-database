import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# ================= 1. ตั้งค่าหน้าจอและดีไซน์ (CSS) =================
st.set_page_config(page_title="MUS-W Dashboard", layout="centered")

st.markdown("""
<style>
    /* พื้นหลังแอป */
    .stApp { background-color: #E5E5E5; }
    header { visibility: hidden; }

    /* บังคับตัวหนังสือทั่วไปให้เป็นสีดำ */
    .stApp, .stApp p, .stApp span, .stApp label, .stRadio label {
        color: #000000 !important;
    }

    /* หัวข้อ MUS-W */
    .mus-header {
        background-color: #C00000;
        color: white !important;
        text-align: center;
        padding: 10px;
        font-size: 48px;
        font-weight: bold;
        border-radius: 15px 15px 15px 15px;
        margin-top: -70px;
        margin-bottom: 20px;
    }

    /* แต่งปุ่มกดทั้งหมด (ปุ่มล็อกอิน, ค้นหา, บันทึกข้อมูล) ให้เป็นสีแดง MUS-W */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #f00a0a !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        height: 50px !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #f00a0a !important;
        color: white !important;
    }

    /* กล่อง Input และ Dropdown (บังคับพื้นสีเทาอ่อน ตัวอักษรสีดำ) */
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
    /* สีของรายการเวลาคลิก Dropdown ลงมา */
    ul[role="listbox"] li {
        color: #000000 !important;
        background-color: #F0F0F0 !important;
    }

    /* กล่องแสดงผลลัพธ์ */
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
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. ระบบรักษาความปลอดภัย (Login) =================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.authenticated:
        return True
    
    st.markdown('<div class="mus-header">LOGIN</div>', unsafe_allow_html=True)
    with st.container():
        st.write("---")
        pwd = st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน:", type="password")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("เข้าสู่ระบบ", use_container_width=True):
                if pwd == "musw1234":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("รหัสผ่านไม่ถูกต้อง!")
    return False

if check_password():
    # ================= 3. เชื่อมต่อ Google Sheets =================
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    def get_data():
        return conn.read(worksheet="Kickless", ttl="1s")

    # ส่วนหัวแอปหลังล็อกอิน
    st.markdown('<div class="mus-header">MUS-W</div>', unsafe_allow_html=True)

    main_tab, tab_other1, tab_other2 = st.tabs(["Kickless", "Welding Transformer", "Other"])

    with main_tab:
        sub_tab1, sub_tab2 = st.tabs(["ค้นหาข้อมูล", "จัดการข้อมูล/อัพเดท"])

        # -------- หน้าค้นหา --------
        with sub_tab1:
            df = get_data()
            cable_list = df['Cable_Name'].unique().tolist() if not df.empty else []
            
            # ช่องนี้สามารถเอานิ้วจิ้มแล้วพิมพ์บนคีย์บอร์ด iPad เพื่อค้นหาได้เลย!
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
                    # ช่องนี้ก็พิมพ์ค้นหาได้เช่นกันครับ
                    c_name = st.selectbox("เลือกสายเดิม (พิมพ์ค้นหาได้):", cable_list if cable_list else ["ไม่มีข้อมูล"])
                
                st.markdown("**กำหนดวันที่และเวลา:**")
                # แบ่งเป็น 3 ช่อง: วันที่ | ชั่วโมง | นาที (แก้ปัญหาบั๊กเวลาบน iPad)
                col_d, col_h, col_m = st.columns([2, 1, 1])
                
                with col_d:
                    d = st.date_input("วันที่")
                with col_h:
                    hours = [f"{i:02d}" for i in range(24)]
                    h = st.selectbox("ชั่วโมง", hours, index=12)
                with col_m:
                    mins = [f"{i:02d}" for i in range(60)]
                    m = st.selectbox("นาที", mins, index=0)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.form_submit_button("บันทึกข้อมูล", use_container_width=True):
                    if not c_name or c_name == "ไม่มีข้อมูล":
                        st.error("ข้อมูลไม่ครบ กรุณาตรวจสอบอีกครั้ง!")
                    else:
                        # นำชั่วโมงและนาทีมาประกอบกัน
                        dt_str = f"{d.strftime('%d-%m-%Y')} {h}.{m}"
                        new_data = pd.DataFrame([{"Cable_Name": c_name, "Last_Changed_Date": dt_str}])
                        
                        updated_df = pd.concat([get_data(), new_data], ignore_index=True)
                        conn.update(worksheet="Kickless", data=updated_df)
                        st.success("บันทึกข้อมูลลง Google Sheets เรียบร้อย!")
                        st.cache_data.clear()

    with tab_other1: st.info("Coming Soon")
    with tab_other2: st.info("Coming Soon")
