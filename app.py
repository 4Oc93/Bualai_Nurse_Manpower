import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าเพจ (Page Configuration)
# ---------------------------------------------------------
st.set_page_config(
    page_title="อัตรากำลังกลุ่มการพยาบาล โรงพยาบาลบัวลาย",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. Custom CSS (ทำให้ Minimal, รองรับ Dark/Light Mode และมือถือ)
# ---------------------------------------------------------
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* ปรับแต่งปุ่มลิงก์ให้ดู minimal */
    .stLinkButton > a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. ฟังก์ชันโหลดข้อมูล (Data Loading)
# ---------------------------------------------------------
@st.cache_data(ttl=600) # รีเฟรชข้อมูลใหม่อัตโนมัติทุกๆ 10 นาที
def load_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # =========================================================
        # 🌟 วิธีที่ 1: ดึงจาก Google Sheet โดยตรง (Auto-Update) 🌟
        # =========================================================
        sheet_id = "11EpKxkld8MS5MIiuK5qAbEZxBwfon6PET9qu3Rq2m4c"
        
        url_trans = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1248730638"
        url_plan = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=716776140"
        url_cal = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1503879217"
        
        df_trans = pd.read_csv(url_trans)
        df_plan = pd.read_csv(url_plan)
        df_cal = pd.read_csv(url_cal)
        
        # แปลง Type วันที่ให้ตรงกันเพื่อใช้ Filter
        df_trans['Date'] = pd.to_datetime(df_trans['Date'], format='mixed').dt.date
        df_cal['Date'] = pd.to_datetime(df_cal['Date'], format='mixed').dt.date
        
        return df_trans, df_plan, df_cal
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        st.warning("โปรดตรวจสอบว่าไฟล์ Google Sheet เปิดแชร์เป็น 'ทุกคนที่มีลิงก์' แล้วหรือยัง")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_trans, df_plan, df_cal = load_data()

# ---------------------------------------------------------
# 4. แถบควบคุมด้านซ้าย (Sidebar & Authentication)
# ---------------------------------------------------------
with st.sidebar:
    st.header("เลือกวันที่") 
    
    if st.button("วันนี้ (Today)", use_container_width=True):
        st.session_state['selected_date'] = date.today()
        
    default_date = st.session_state.get('selected_date', date.today())
    selected_date = st.date_input("เลือกวันที่เพื่อดูข้อมูล:", value=default_date)
    
    st.markdown("---")
    
    st.subheader("ระบบแก้ไขข้อมูล")
    pin_input = st.text_input("กรอก PIN เพื่อเข้าถึงฐานข้อมูล", type="password")
    
    if pin_input:
        if pin_input == "27839":
            st.success("รหัสถูกต้อง")
            google_sheet_url = "https://docs.google.com/spreadsheets/d/11EpKxkld8MS5MIiuK5qAbEZxBwfon6PET9qu3Rq2m4c/edit?usp=sharing" 
            st.link_button("ไปหน้า Google Sheet", google_sheet_url, use_container_width=True)
        else:
            st.error("รหัส PIN ไม่ถูกต้อง")
            
    st.markdown("---")
    if st.button("โหลดข้อมูลล่าสุด (Refresh)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------------
# 5. ฟังก์ชันคำนวณและสร้างการ์ด (KPI Card Component)
# ---------------------------------------------------------

# 5.1 การ์ดแผนกหลักแบบปกติ
def create_kpi_card(dept, shift, staff_list, required_count):
    actual_count = len(staff_list)
    diff = actual_count - required_count
    
    if diff < 0:
        border_color = "#FF4B4B" # สีแดง
        status_text = f"<span style='color: {border_color};'>●</span> ขาดคน ({abs(diff)} คน)"
    elif diff == 0:
        border_color = "#21C354" # สีเขียว
        status_text = f"<span style='color: {border_color};'>●</span> อัตรากำลังพอดี"
    else:
        border_color = "#2B83FE" # สีฟ้า
        status_text = f"<span style='color: {border_color};'>●</span> กำลังเสริม ({diff} คน)"
        
    names_html = "".join([f"<div style='font-size: 0.85rem; padding: 2px 0; color: var(--text-color);'><span style='color: #888; margin-right: 6px;'>•</span>{n}</div>" for n in staff_list])
    if not names_html:
        names_html = "<div style='font-size: 0.85rem; color: gray; font-style: italic;'>ไม่มีผู้ปฏิบัติงาน</div>"
        
    # ซ่อนป้ายเวรเช้าถ้าส่งค่า shift เป็น string ว่าง
    shift_badge = f"""<span style="font-size: 0.8rem; background-color: var(--background-color); padding: 0.2rem 0.5rem; border-radius: 1rem; font-weight: 500; vertical-align: middle;">เวร{shift}</span>""" if shift else ""
    
    # ปรับ Layout ใหม่เป็น Flexbox (ย้ายตัวเลขไปขวา) และลด padding/margin ลงให้พอดีกับ ER/IPD
    card_html = f"""<div style="background-color: var(--secondary-background-color); padding: 1rem 1.2rem; border-radius: 0.6rem; border: 1px solid rgba(128,128,128,0.2); border-left: 5px solid {border_color}; box-shadow: 0 2px 5px rgba(0,0,0,0.02); margin-bottom: 0.8rem; transition: transform 0.2s;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
        <div>
            <p style="margin:0; font-size: 1.6rem; color: var(--text-color); font-weight: 700; line-height: 1.2;">{dept} {shift_badge}</p>
            <p style="margin:0; font-size: 0.85rem; font-weight: 600; margin-top: 4px;">{status_text}</p>
        </div>
        <div style="text-align: right;">
            <h2 style="margin:0; font-size: 2rem; line-height: 1; color: var(--text-color);">{actual_count} <span style="font-size: 1.1rem; opacity: 0.5; font-weight: 400;">/ {required_count}</span></h2>
        </div>
    </div>
    <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed rgba(128,128,128,0.3); max-height: 80px; overflow-y: auto;">
        {names_html}
    </div>
</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

# 5.2 การ์ดแผนกแบบรวม 3 เวร (สำหรับ ER และ IPD)
def create_combined_kpi_card(dept, shifts_info):
    cols_html = ""
    for i, s in enumerate(shifts_info):
        actual = len(s['staff'])
        req = s['req']
        diff = actual - req
        
        if diff < 0:
            b_color = "#FF4B4B"
            s_text = f"<span style='color: {b_color};'>●</span> ขาดคน ({abs(diff)})"
        elif diff == 0:
            b_color = "#21C354"
            s_text = f"<span style='color: {b_color};'>●</span> พอดี"
        else:
            b_color = "#2B83FE"
            s_text = f"<span style='color: {b_color};'>●</span> เสริม ({diff})"

        names = "".join([f"<div style='font-size: 0.85rem; padding: 2px 0; color: var(--text-color);'><span style='color: #888; margin-right: 6px;'>•</span>{n}</div>" for n in s['staff']])
        if not names: names = "<div style='font-size: 0.85rem; color: gray; font-style: italic;'>ไม่มีผู้ปฏิบัติงาน</div>"

        border_top = "border-top: 1px dashed rgba(128,128,128,0.2); padding-top: 12px; margin-top: 12px;" if i > 0 else ""

        cols_html += f"""<div style="{border_top}">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
        <div style="border-left: 4px solid {b_color}; padding-left: 10px;">
            <p style="margin:0; font-size: 1.1rem; font-weight: 700; color: var(--text-color);">เวร{s['shift']}</p>
            <p style="margin:0; font-size: 0.85rem; font-weight: 600;">{s_text}</p>
        </div>
        <div style="text-align: right;">
            <h2 style="margin:0; font-size: 1.8rem; line-height: 1; color: var(--text-color);">{actual} <span style="font-size: 1.1rem; opacity: 0.5; font-weight: 400;">/ {req}</span></h2>
        </div>
    </div>
    <div style="padding-left: 14px; max-height: 100px; overflow-y: auto;">
        {names}
    </div>
</div>"""

    card_html = f"""<div style="background-color: var(--secondary-background-color); padding: 1.2rem; border-radius: 0.6rem; border: 1px solid rgba(128,128,128,0.2); box-shadow: 0 2px 5px rgba(0,0,0,0.02); margin-bottom: 1rem;">
    <p style="margin:0 0 15px 0; font-size: 1.8rem; color: var(--text-color); font-weight: 700; line-height: 1.2;">{dept}</p>
    {cols_html}
</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

# 5.3 การ์ดขนาดเล็ก (คลินิกพิเศษ และ การลา)
def create_mini_card(title, staff_list, card_type=None):
    actual_count = len(staff_list)
    
    border_color = "#808495" # สีเทา (เริ่มต้น/ไม่มีคน)
    
    if actual_count > 0:
        if card_type == "clinic":
            border_color = "#21C354" # มีคนเข้าคลินิกพิเศษ = สีเขียว
        elif card_type == "leave":
            border_color = "#FF9800" # มีคนลา/อบรม = สีส้ม
            
    names_html = "".join([f"<div style='font-size: 0.85rem; padding: 2px 0; color: var(--text-color);'><span style='color: #888; margin-right: 6px;'>•</span>{n}</div>" for n in staff_list])
    if not names_html:
        names_html = "<div style='font-size: 0.85rem; color: gray; font-style: italic;'>ไม่มีข้อมูล</div>"
        
    card_html = f"""<div style="background-color: var(--secondary-background-color); padding: 1rem; border-radius: 0.6rem; border: 1px solid rgba(128,128,128,0.2); border-left: 4px solid {border_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 1rem;">
    <p style="margin:0; font-size: 1.5rem; color: var(--text-color); font-weight: 600;">{title}</p>
    <h3 style="margin:0; padding: 0.2rem 0; color: var(--text-color);">{actual_count} <span style="font-size: 1rem; font-weight: 400;">คน</span></h3>
    <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed rgba(128,128,128,0.3); max-height: 100px; overflow-y: auto;">
        {names_html}
    </div>
</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. ประมวลผลข้อมูลประจำวัน (Data Processing)
# ---------------------------------------------------------
day_type = "Normal"
if not df_cal.empty and 'Date' in df_cal.columns and 'DayType' in df_cal.columns:
    cal_today = df_cal[df_cal['Date'] == selected_date]
    if not cal_today.empty:
        day_type = cal_today.iloc[0]['DayType']

if not df_trans.empty and 'Date' in df_trans.columns:
    df_today = df_trans[df_trans['Date'] == selected_date]
else:
    df_today = pd.DataFrame()

def get_staff_list(dept, shift):
    if df_today.empty or 'Actual_Department' not in df_today.columns or 'Shift' not in df_today.columns or 'FullName' not in df_today.columns: 
        return []
    return df_today[(df_today['Actual_Department'] == dept) & (df_today['Shift'] == shift)]['FullName'].tolist()

def get_required(dept, shift_code):
    if df_plan.empty or 'DepartmentShiftKey' not in df_plan.columns: 
        return 0
    key = f"{dept}|{shift_code}"
    plan = df_plan[df_plan['DepartmentShiftKey'] == key]
    if not plan.empty:
        col = 'Required_Normal' if day_type == "Normal" else 'Required_Holiday'
        if col in plan.columns:
            return int(plan.iloc[0][col])
    return 0

# ---------------------------------------------------------
# 7. ส่วนหัว Dashboard (Top Section & Logo)
# ---------------------------------------------------------
col_logo, col_text = st.columns([1, 8])

with col_logo:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "logo.png") 
        st.image(logo_path, use_container_width=True)
    except Exception:
        pass 

with col_text:
    st.title("อัตรากำลังกลุ่มการพยาบาล โรงพยาบาลบัวลาย")
    day_th = "วันหยุดราชการ/นักขัตฤกษ์" if day_type == "Holiday" else "วันทำการปกติ"
    st.markdown(f"**ข้อมูลประจำวันที่:** {selected_date.strftime('%d / %m / %Y')} &nbsp;|&nbsp; **ประเภทวัน:** {day_th}")

st.divider()

# ---------------------------------------------------------
# 8. โซนที่ 1: แผนกหลัก (Main Departments)
# ---------------------------------------------------------
st.subheader("ส่วนที่ 1: แผนกหลัก")

c1, c2, c3 = st.columns(3)

with c1:
    create_kpi_card("OPD", "", get_staff_list("OPD", "เช้า"), get_required("OPD", "ช"))
    create_kpi_card("NCD", "", get_staff_list("NCD", "เช้า"), get_required("NCD", "ช"))
    create_kpi_card("ARI", "", get_staff_list("ARI", "เช้า"), get_required("ARI", "ช"))
    create_kpi_card("Triage", "", get_staff_list("Triage", "เช้า"), get_required("Triage", "ช"))

with c2:
    er_shifts = [
        {"shift": "เช้า", "staff": get_staff_list("ER", "เช้า"), "req": get_required("ER", "ช")},
        {"shift": "บ่าย", "staff": get_staff_list("ER", "บ่าย"), "req": get_required("ER", "บ")},
        {"shift": "ดึก", "staff": get_staff_list("ER", "ดึก"), "req": get_required("ER", "ด")}
    ]
    create_combined_kpi_card("ER", er_shifts)

with c3:
    ipd_shifts = [
        {"shift": "เช้า", "staff": get_staff_list("IPD", "เช้า"), "req": get_required("IPD", "ช")},
        {"shift": "บ่าย", "staff": get_staff_list("IPD", "บ่าย"), "req": get_required("IPD", "บ")},
        {"shift": "ดึก", "staff": get_staff_list("IPD", "ดึก"), "req": get_required("IPD", "ด")}
    ]
    create_combined_kpi_card("IPD", ipd_shifts)

st.divider()

# ---------------------------------------------------------
# 9. โซนที่ 2 & 3: แผนกย่อย และ ข้อมูลการลา
# ---------------------------------------------------------
col_sub, col_leave = st.columns([1.5, 1])

with col_sub:
    st.subheader("ส่วนที่ 2: คลินิกพิเศษ")
    s1, s2, s3 = st.columns(3)
    with s1: create_mini_card("Psychiatric", get_staff_list('Psychiatric', 'เช้า'), card_type="clinic")
    with s2: create_mini_card("TB", get_staff_list('TB', 'เช้า'), card_type="clinic")
    with s3: create_mini_card("IC", get_staff_list('IC', 'เช้า'), card_type="clinic")
    
    s4, s5, s6 = st.columns(3)
    with s4: create_mini_card("ARV", get_staff_list('ARV', 'เช้า'), card_type="clinic")
    with s5: create_mini_card("IMC", get_staff_list('IMC', 'เช้า'), card_type="clinic")
    with s6: create_mini_card("COPD", get_staff_list('COPD', 'เช้า'), card_type="clinic")

with col_leave:
    st.subheader("ส่วนที่ 3: สถานะการลา/อบรม")
    
    def get_leave_list(type_name): 
        if df_today.empty or 'Actual_Department' not in df_today.columns or 'FullName' not in df_today.columns:
            return []
        return df_today[df_today['Actual_Department'] == type_name]['FullName'].tolist()
    
    l1, l2 = st.columns(2)
    with l1: create_mini_card("ลาพักผ่อน (VA)", get_leave_list('VA'), card_type="leave")
    with l2: create_mini_card("ลากิจ", get_leave_list('ลากิจ'), card_type="leave")
    
    l3, l4 = st.columns(2)
    with l3: create_mini_card("ลาป่วย", get_leave_list('ลาป่วย'), card_type="leave")
    with l4: create_mini_card("ไปอบรม", get_leave_list('อบรม'), card_type="leave")