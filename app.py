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
    /* พื้นหลังแอปสีเทาอ่อน */
    .stApp { background-color: #E5E5E5; }
    header { visibility: hidden; }
    
    /* บังคับตัวหนังสือทั่วไปให้เป็นสีดำ */
    .stApp, .stApp p, .stApp span, .stApp label, .stRadio label { color: #000000 !important; }

    /* หัวข้อ MUS-W */
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

    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #f00a0a !important;
        color: white !important;
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
    .result-date {
        font-size: 38px;
        font-weight: bold;
        color: #000000 !important;
    }

    /* 💡 บังคับตาราง HTML ให้เป็นสีขาว/ดำล้วน */
    .white-table {
        background-color: white !important;
        color: black !important;
        border-collapse: collapse;
        width: 100%;
        border-radius: 5px;
        overflow: hidden;
        margin-top: 10px;
    }
    .white-table th, .white-table td {
        border: 1px solid #ddd !important;
        padding: 8px !important;
        text-align: center !important;
    }
    .white-table th {
        background-color: #f2f2f2 !important;
        font-weight: bold;
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

# ================= 3. เชื่อมต่อฐานข้อมูลและเริ่มตัวแอป =================
if check_password():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    def get_data():
        return conn.read(worksheet="Kickless", ttl="1s")

    st.markdown('<div class="mus-header">MUS-W</div>', unsafe_allow_html=True)
    main_tab, tab_other1, tab_other2 = st.tabs(["Kickless", "Welding Transformer", "Other"])
    with main_tab:
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🔍 ค้นหาข้อมูล", "⚙️ จัดการข้อมูล/อัพเดท", "📊 ภาพรวม"])

        # -------- แท็บ 1: ค้นหา --------
        with sub_tab1:
            df = get_data()
            cable_list = df['Cable_Name'].unique().tolist() if not df.empty else []
            
            search_kw1 = st.text_input("🔍 พิมพ์รหัสสายเพื่อค้นหา:", key="search1")
            filtered_list1 = [c for c in cable_list if str(search_kw1).lower().strip() in str(c).lower()] if search_kw1 else cable_list
            default_idx1 = 1 if (search_kw1 and len(filtered_list1) > 0) else 0
            
            selected = st.selectbox("เลือกรหัสสาย Kickless จากรายการ", ["-- กรุณาเลือกสาย --"] + filtered_list1, index=default_idx1)
            
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

        # -------- แท็บ 2: จัดการข้อมูล --------
        with sub_tab2:
            mode = st.radio("โหมด:", ["อัพเดทสายเดิม", "ลงข้อมูลสายใหม่"], horizontal=True, label_visibility="collapsed")
            
            if mode == "ลงข้อมูลสายใหม่":
                c_name = st.text_input("ชื่อ/รหัส สาย Kickless เส้นใหม่:")
            else:
                search_kw2 = st.text_input("🔍 พิมพ์รหัสสายเดิมเพื่อค้นหา:", key="search2")
                filtered_list2 = [c for c in cable_list if str(search_kw2).lower().strip() in str(c).lower()] if search_kw2 else cable_list
                default_idx2 = 1 if (search_kw2 and len(filtered_list2) > 0) else 0
                c_name = st.selectbox("เลือกสายเดิมจากรายการ:", ["-- กรุณาเลือกสาย --"] + filtered_list2 if filtered_list2 else ["ไม่มีข้อมูล"], index=default_idx2 if filtered_list2 else 0)
            
            with st.form("input_form", clear_on_submit=True):
                st.markdown("**📅 กำหนดวันที่และเวลา:**")
                
                # ปฏิทินเลือกวันแบบเดิม
                d = st.date_input("เลือกวันที่")
                
                # วงล้อเลือกเวลาแบบเดิม
                now = datetime.now()
                col_h, col_m = st.columns(2)
                with col_h:
                    h = st.selectbox("ชั่วโมง", [f"{i:02d}" for i in range(24)], index=now.hour)
                with col_m:
                    m = st.selectbox("นาที", [f"{i:02d}" for i in range(60)], index=now.minute)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.form_submit_button("บันทึกข้อมูล", use_container_width=True):
                    if not c_name or c_name in ["ไม่มีข้อมูล", "-- กรุณาเลือกสาย --"]:
                        st.error("ข้อมูลไม่ครบ!")
                    else:
                        # 💡 ดึง Animation การโหลดกลับมา
                        with st.spinner('กำลังบันทึกข้อมูล... กรุณารอสักครู่ ⏳'):
                            dt_str = f"{d.strftime('%d-%m-%Y')} {h}.{m}"
                            new_data = pd.DataFrame([{"Cable_Name": c_name, "Last_Changed_Date": dt_str}])
                            updated_df = pd.concat([get_data(), new_data], ignore_index=True)
                            conn.update(worksheet="Kickless", data=updated_df)
                            time.sleep(1) # หน่วงเวลาให้เห็น animation นิดนึง
                            
                        st.toast("บันทึกข้อมูลลงระบบเรียบร้อย! ✅")
                        st.cache_data.clear()

        # -------- แท็บ 3: ภาพรวม --------
        with sub_tab3:
            st.markdown("### 📊 สรุปการเปลี่ยนสายรายเดือน (แยกรายเส้น)")
            df_chart = get_data().copy()
            
            if not df_chart.empty:
                df_chart['Date'] = pd.to_datetime(df_chart['Last_Changed_Date'], format='%d-%m-%Y %H.%M', errors='coerce')
                df_chart = df_chart.dropna(subset=['Date'])
                
                if not df_chart.empty:
                    df_chart['Month'] = df_chart['Date'].dt.strftime('%m-%Y') 
                    
                    summary_table = df_chart.groupby(['Month', 'Cable_Name']).size().reset_index(name='จำนวนที่เปลี่ยน')
                    
                    # กราฟแท่งสีขาว
                    bar_chart = alt.Chart(summary_table).mark_bar().encode(
                        x=alt.X('Month:N', title='เดือน-ปี', axis=alt.Axis(labelAngle=0, labelColor='black', titleColor='black')),
                        y=alt.Y('จำนวนที่เปลี่ยน:Q', title='จำนวนที่เปลี่ยน (ครั้ง)', axis=alt.Axis(tickMinStep=1, labelColor='black', titleColor='black')),
                        color=alt.Color('Cable_Name:N', title='รหัสสาย'),
                        xOffset='Cable_Name:N' 
                    ).properties(
                        height=350,
                        background='white'
                    ).configure_view(
                        strokeWidth=0
                    ).configure_legend(
                        titleColor='black',
                        labelColor='black'
                    )
                    
                    st.altair_chart(bar_chart, use_container_width=True, theme=None)
                    
                    # 💡 ตาราง HTML สีขาวสะอาดตา 
                    st.markdown("**📝 รายละเอียดจำนวนที่เปลี่ยน (เส้น):**")
                    pivot_summary = summary_table.pivot(index='Cable_Name', columns='Month', values='จำนวนที่เปลี่ยน').fillna(0).astype(int)
                    
                    # แปลง DataFrame เป็น HTML แล้วยัดใส่คลาส white-table ที่เราเขียนไว้ด้านบน
                    html_table = pivot_summary.to_html(classes='white-table')
                    st.markdown(html_table, unsafe_allow_html=True)

                else:
                    st.info("ไม่พบข้อมูลวันที่ครับ")
            else:
                st.info("ยังไม่มีข้อมูลในระบบ")

    with tab_other1: st.info("Coming Soon")
    with tab_other2: st.info("Coming Soon")
