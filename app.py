import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import altair as alt
from datetime import datetime

# ================= 1. ตั้งค่าหน้าจอและดีไซน์ (CSS) =================
st.set_page_config(
    page_title="MUS-W Dashboard", 
    layout="centered",
    page_icon="https://drive.google.com/uc?id=1X1y3I9VpW6-oE6p1K9rVv0lT_4-Nf6p-&v=3"
)

st.markdown("""
<style>
    /* พื้นหลังแอปสีเทาอ่อนเหมือนเดิม เพื่อให้ตัดกับกราฟสีขาว */
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

    .stTextInput input {
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

        # -------- แท็บ 2: จัดการข้อมูล (แก้บั๊กแป้นพิมพ์เด้งตอนใส่วันที่) --------
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
                
                # 💡 ใช้กล่องเลือกแบบ Dropdown แทน Date Input เพื่อกันแป้นพิมพ์เด้งบน iOS
                now = datetime.now()
                col_d, col_mo, col_y = st.columns(3)
                with col_d:
                    d_day = st.selectbox("วันที่", [f"{i:02d}" for i in range(1, 32)], index=now.day-1)
                with col_mo:
                    d_month = st.selectbox("เดือน", [f"{i:02d}" for i in range(1, 13)], index=now.month-1)
                with col_y:
                    years_list = [str(i) for i in range(2024, 2035)]
                    d_year = st.selectbox("ปี (ค.ศ.)", years_list, index=years_list.index(str(now.year)))

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
                        # นำค่าที่เลือกมาต่อกันเป็นข้อความ
                        dt_str = f"{d_day}-{d_month}-{d_year} {h}.{m}"
                        new_data = pd.DataFrame([{"Cable_Name": c_name, "Last_Changed_Date": dt_str}])
                        updated_df = pd.concat([get_data(), new_data], ignore_index=True)
                        conn.update(worksheet="Kickless", data=updated_df)
                        st.toast("บันทึกข้อมูลเรียบร้อย! ✅")
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
                    
                    # 💡 สร้างกราฟแท่งแบบแยกอิสระ (Clustered Bar Chart)
                    bar_chart = alt.Chart(summary_table).mark_bar().encode(
                        x=alt.X('Month:N', title='เดือน-ปี', axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('จำนวนที่เปลี่ยน:Q', title='จำนวนที่เปลี่ยน (ครั้ง)', axis=alt.Axis(tickMinStep=1)),
                        color=alt.Color('Cable_Name:N', title='รหัสสาย'),
                        xOffset='Cable_Name:N' # 💡 คำสั่งนี้ทำให้แท่งกราฟแยกกันในแต่ละเดือน
                    ).properties(
                        height=350
                    ).configure_view(
                        strokeWidth=0
                    )
                    
                    # 💡 พระเอกของงาน: theme=None คือการสั่งให้เฉพาะกราฟเป็นสีขาวสว่างๆ 
                    st.altair_chart(bar_chart, use_container_width=True, theme=None)
                    
                    # 2. ตารางสรุป 
                    st.markdown("**📝 รายละเอียดจำนวนที่เปลี่ยน (เส้น):**")
                    pivot_summary = summary_table.pivot(index='Cable_Name', columns='Month', values='จำนวนที่เปลี่ยน').fillna(0).astype(int)
                    st.dataframe(pivot_summary, use_container_width=True)
                else:
                    st.info("ไม่พบข้อมูลวันที่ครับ")
            else:
                st.info("ยังไม่มีข้อมูลในระบบ")

    with tab_other1: st.info("Coming Soon")
    with tab_other2: st.info("Coming Soon")
