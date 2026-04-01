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
    div.stButton > button:hover, div.stFormSubmitButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #f00a0a !important;
        color: #ffffff !important;
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
    .result-date {
        font-size: 38px;
        font-weight: bold;
        color: #000000 !important;
    }

    [data-testid="stElementToolbar"] { display: none !important; }
        /* 💡 บังคับตาราง HTML ให้เป็นสีขาว/ดำล้วน (แบบขั้นเด็ดขาด ล็อกทุกจุด!) */
    table.white-table, table.white-table tbody, table.white-table thead, table.white-table tr {
        background-color: white !important;
        color: black !important;
        border-collapse: collapse !important;
        width: 100% !important;
        margin-top: 10px !important;
    }
    
    table.white-table th, table.white-table td {
        background-color: white !important;
        color: black !important; /* ล็อกสีตัวหนังสือเป็นสีดำ */
        border: 1px solid #CCCCCC !important; /* ล็อกเส้นขอบตาราง */
        padding: 10px !important;
        text-align: center !important;
        font-size: 16px !important;
    }
    
    table.white-table th {
        background-color: #f2f2f2 !important; /* พื้นหลังหัวตารางสีเทาอ่อน */
        font-weight: bold !important;
    }

     
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
    conn = st.connection("gsheets", type=GSheetsConnection)
    def get_data(): return conn.read(worksheet="Kickless", ttl="1s")
    st.markdown('<div class="mus-header">MUS-W</div>', unsafe_allow_html=True)
    main_tab, tab_other1, tab_other2 = st.tabs(["Kickless", "Welding Transformer", "Other"])
    with main_tab:
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🔍 ค้นหาข้อมูล", "⚙️ จัดการข้อมูล/อัพเดท", "📊 ภาพรวม"])

        # -------- แท็บ 1: ค้นหา (ค้นหาด้วยชื่อ Machine) --------
        with sub_tab1:
            df = get_data()
            machine_list = df['Cable_Name'].unique().tolist() if not df.empty else []
            
            search_kw1 = st.text_input("🔍 พิมพ์ชื่อ Machine เพื่อค้นหา:", key="search1")
            filtered_list1 = [m for m in machine_list if str(search_kw1).lower().strip() in str(m).lower()] if search_kw1 else machine_list
            default_idx1 = 1 if (search_kw1 and len(filtered_list1) > 0) else 0
            
            selected_m = st.selectbox("เลือกชื่อ Machine จากรายการ", ["-- กรุณาเลือกเครื่อง --"] + filtered_list1, index=default_idx1)
            
            if st.button("ค้นหาข้อมูลล่าสุด", use_container_width=True):
                if selected_m == "-- กรุณาเลือกเครื่อง --":
                    st.warning("กรุณาเลือก Machine ก่อนครับ")
                else:
                    latest = df[df['Cable_Name'] == selected_m].iloc[-1]
                    spec_info = f" (สเปค: {latest['Cable_Spec']})" if 'Cable_Spec' in latest and pd.notna(latest['Cable_Spec']) else ""
                    st.markdown(f"""
                    <div class="result-box">
                        <div style="color:#333; font-weight:bold;">-- วันที่เปลี่ยนสายล่าสุด {spec_info} --</div>
                        <div class="result-date">{latest['Last_Changed_Date']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # -------- แท็บ 2: จัดการข้อมูล (Machine Input + Spec Dropdown) --------
        with sub_tab2:
            mode = st.radio("โหมด:", ["อัพเดทสายเดิม", "ลงข้อมูลสายใหม่"], horizontal=True, label_visibility="collapsed")
            
            spec_options = [
                "150 sq.mm * 2.4 m",
                "150 sq.mm * 3.0 m",
                "200 sq.mm * 2.4 m",
                "200 sq.mm * 3.0 m"
            ]

            if mode == "ลงข้อมูลสายใหม่":
                m_name = st.text_input("พิมพ์ชื่อ Machine ใหม่:")
            else:
                search_kw2 = st.text_input("🔍 พิมพ์ชื่อ Machine เดิมเพื่อค้นหา:", key="search2")
                filtered_list2 = [m for m in machine_list if str(search_kw2).lower().strip() in str(m).lower()] if search_kw2 else machine_list
                default_idx2 = 1 if (search_kw2 and len(filtered_list2) > 0) else 0
                m_name = st.selectbox("เลือกชื่อ Machine เดิม:", ["-- กรุณาเลือกเครื่อง --"] + filtered_list2 if filtered_list2 else ["ไม่มีข้อมูล"], index=default_idx2 if filtered_list2 else 0)
            
            # เพิ่ม Dropdown เลือกสเปคสาย
            c_spec = st.selectbox("เลือกสเปคสาย Kickless:", spec_options)

            with st.form("input_form", clear_on_submit=True):
                st.markdown("**📅 กำหนดวันที่และเวลา:**")
                d = st.date_input("เลือกวันที่")
                now = datetime.now()
                col_h, col_m = st.columns(2)
                with col_h:
                    h = st.selectbox("ชั่วโมง", [f"{i:02d}" for i in range(24)], index=now.hour)
                with col_m:
                    m = st.selectbox("นาที", [f"{i:02d}" for i in range(60)], index=now.minute)
                
                if st.form_submit_button("บันทึกข้อมูล", use_container_width=True):
                    if not m_name or m_name in ["ไม่มีข้อมูล", "-- กรุณาเลือกเครื่อง --"]:
                        st.error("กรุณาระบุชื่อ Machine!")
                    else:
                        with st.spinner('กำลังบันทึกข้อมูล...'):
                            dt_str = f"{d.strftime('%d-%m-%Y')} {h}.{m}"
                            new_row = {"Cable_Name": m_name, "Cable_Spec": c_spec, "Last_Changed_Date": dt_str}
                            updated_df = pd.concat([get_data(), pd.DataFrame([new_row])], ignore_index=True)
                            conn.update(worksheet="Kickless", data=updated_df)
                            time.sleep(1)
                        st.toast("บันทึกข้อมูล Machine: " + m_name + " เรียบร้อย! ✅")
                        st.cache_data.clear()

        # -------- แท็บ 3: ภาพรวม --------
        with sub_tab3:
            st.markdown("### 📊 สรุปการเปลี่ยนสายรายเดือน")
            df_chart = get_data().copy()
            if not df_chart.empty:
                df_chart['Date'] = pd.to_datetime(df_chart['Last_Changed_Date'], format='%d-%m-%Y %H.%M', errors='coerce')
                df_chart = df_chart.dropna(subset=['Date'])
                if not df_chart.empty:
                    df_chart['Month'] = df_chart['Date'].dt.strftime('%m-%Y') 
                    summary = df_chart.groupby(['Month', 'Cable_Name']).size().reset_index(name='Count')
                    
                    chart = alt.Chart(summary).mark_bar().encode(
                        x=alt.X('Month:N', title='เดือน-ปี'),
                        y=alt.Y('Count:Q', title='จำนวนครั้ง'),
                        color=alt.Color('Cable_Name:N', title='Machine'),
                        xOffset='Cable_Name:N'
                    ).properties(height=350, background='white').configure_view(strokeWidth=0).configure_legend(titleColor='black', labelColor='black')
                    
                    st.altair_chart(chart, use_container_width=True, theme=None)
                    
                    pivot = summary.pivot(index='Cable_Name', columns='Month', values='Count').fillna(0).astype(int)
                    st.markdown(pivot.to_html(classes='white-table'), unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    csv = pivot.to_csv().encode('utf-8-sig')
                    st.download_button("📥 ดาวน์โหลดข้อมูลสรุป (CSV)", data=csv, file_name="MUS-W_Summary.csv", mime="text/csv", use_container_width=True)
                else: st.info("ไม่พบข้อมูลวันที่ครับ")
            else: st.info("ยังไม่มีข้อมูลในระบบ")

    with tab_other1: st.info("Coming Soon")
    with tab_other2: st.info("Coming Soon")
