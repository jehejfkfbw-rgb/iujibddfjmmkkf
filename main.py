import streamlit as st
import sqlite3
import os
import hashlib
import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التصميم والإخفاء الجذري للأشرطة العلوية
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="📚", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* إخفاء تام لكل الأشرطة العلوية والقوائم العائمة وشريط الحروف */
    #MainMenu, footer, header, .stDeployButton, 
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], 
    div[data-testid="stStatusWidget"], #stDecoration, 
    header[data-testid="stHeader"], div[data-testid="baseToolbar"],
    .viewerBadge_container__1QSob, .styles_viewerBadge__1yG5_ {
        display: none !important;
        visibility: hidden !important;
    }
    
    .block-container {
        max-width: 750px !important;
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: Arial, sans-serif !important;
    }
    
    h1, h2, h3, h4 {
        color: #1f2937 !important;
        font-weight: bold !important;
    }
    
    .classic-box {
        background-color: #f9fafb !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
    }
    
    .stTextInput input, .stNumberInput input, .stPasswordInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #9ca3af !important;
        border-radius: 4px !important;
        padding: 10px !important;
        width: 100% !important;
    }
    
    .stButton>button {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
        border: 1px solid #9ca3af !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        padding: 10px 16px !important;
        width: 100% !important;
        margin-top: 10px !important;
    }
    
    .stButton>button:hover {
        background-color: #e5e7eb !important;
        border-color: #4b5563 !important;
    }
    
    .cash-banner {
        background-color: #fffbeb !important;
        color: #92400e !important;
        padding: 12px !important;
        border-radius: 4px !important;
        text-align: center !important;
        border: 1px solid #f59e0b !important;
        margin: 10px 0 !important;
    }
    
    .success-badge {
        background-color: #ecfdf5 !important;
        color: #065f46 !important;
        padding: 12px !important;
        border-radius: 4px !important;
        border: 1px solid #10b981 !important;
        text-align: center !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد قاعدة البيانات والملفات
# ==========================================
MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

DB_NAME = 'nova_modern_system_pro.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            phone TEXT UNIQUE, 
            email TEXT UNIQUE,
            password TEXT, 
            name TEXT, 
            age TEXT, 
            grade TEXT, 
            role TEXT, 
            points INTEGER DEFAULT 0,
            wallet_balance REAL DEFAULT 0.0,
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            phone TEXT UNIQUE, 
            password TEXT, 
            name TEXT, 
            subject TEXT,
            grade_level TEXT, 
            age INTEGER, 
            price REAL, 
            image_url TEXT, 
            room_id TEXT, 
            rating REAL DEFAULT 5.0,
            is_blocked INTEGER DEFAULT 0)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS allowed_teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            phone TEXT UNIQUE)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            student_phone TEXT, 
            teacher_phone TEXT,
            status TEXT DEFAULT 'pending', 
            orange_cash_sender TEXT, 
            requested_at TEXT, 
            expires_at TEXT, 
            is_permanently_accepted INTEGER DEFAULT 1,
            UNIQUE(student_phone, teacher_phone))''')

        c.execute('''CREATE TABLE IF NOT EXISTS live_broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_phone TEXT UNIQUE,
            title TEXT,
            is_active INTEGER DEFAULT 0,
            visibility TEXT DEFAULT 'subscriber',
            countdown_hours INTEGER DEFAULT 0,
            started_at TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS call_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_phone TEXT,
            student_phone TEXT,
            student_name TEXT,
            status TEXT DEFAULT 'pending',
            timestamp TEXT,
            UNIQUE(teacher_phone, student_phone))''')

        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            teacher_phone TEXT, 
            title TEXT,
            description TEXT,
            media_type TEXT, 
            file_path TEXT, 
            status TEXT DEFAULT 'approved', 
            views_count INTEGER DEFAULT 0, 
            visibility TEXT DEFAULT 'subscriber',
            timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            post_id INTEGER, 
            student_name TEXT, 
            comment_text TEXT, 
            timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS smart_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            teacher_phone TEXT, 
            student_phone TEXT, 
            sender_role TEXT, 
            message TEXT, 
            timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            sender_phone TEXT, 
            sender_name TEXT, 
            role TEXT, 
            complaint_text TEXT, 
            timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            teacher_phone TEXT, 
            question TEXT,
            opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT, 
            correct_answer TEXT, 
            timestamp TEXT)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS homeworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_phone TEXT,
            title TEXT,
            description TEXT,
            deadline TEXT,
            timestamp TEXT)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS homework_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            homework_id INTEGER,
            student_phone TEXT,
            student_name TEXT,
            answer_text TEXT,
            file_path TEXT,
            grade_score TEXT DEFAULT 'قيد المراجعة',
            timestamp TEXT)''')

        c.execute("INSERT OR IGNORE INTO allowed_teachers (phone) VALUES ('01000000000')")
        conn.commit()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 3. إدارة الجلسات
# ==========================================
params = st.query_params

if "is_logged_in" not in st.session_state:
    saved_phone = params.get("nova_phone", "")
    saved_role = params.get("nova_role", "")
    if saved_phone and saved_role:
        st.session_state.is_logged_in = True
        st.session_state.user_phone = saved_phone
        st.session_state.user_role = saved_role
    else:
        st.session_state.is_logged_in = False
        st.session_state.user_phone = ""
        st.session_state.user_role = None

if "sub_target_teacher" not in st.session_state:
    st.session_state.sub_target_teacher = None

if "inside_teacher_room" not in st.session_state:
    st.session_state.inside_teacher_room = False

def login_user(phone, role):
    st.session_state.is_logged_in = True
    st.session_state.user_phone = phone
    st.session_state.user_role = role
    st.query_params["nova_phone"] = phone
    st.query_params["nova_role"] = role

def logout_user():
    st.session_state.is_logged_in = False
    st.session_state.user_phone = ""
    st.session_state.user_role = None
    st.session_state.sub_target_teacher = None
    st.session_state.inside_teacher_room = False
    st.query_params.clear()

# ==========================================
# 4. الوظائف والأقسام التفاعلية
# ==========================================
@st.fragment
def render_smart_chat(teacher_phone, student_phone, current_user_role):
    st_autorefresh(interval=2500, key=f"smart_chat_ref_{teacher_phone}_{student_phone}")
    st.markdown("💬 **الشات الخاص الفوري مع الأستاذ:**")
    
    with st.form(f"smart_chat_form_{teacher_phone}_{student_phone}", clear_on_submit=True):
        msg = st.text_input("اكتب رسالتك للأستاذ هنا...")
        send_btn = st.form_submit_button("إرسال الرسالة")
        if send_btn and msg:
            t_now = datetime.datetime.now().strftime("%H:%M - %Y/%m/%d")
            sender_role = "أستاذ" if current_user_role == "أستاذ" else "طالب"
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO smart_chat (teacher_phone, student_phone, sender_role, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                              (teacher_phone, student_phone, sender_role, msg, t_now))
                    conn.commit()
                st.rerun()
            except:
                pass

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT sender_role, message, timestamp FROM smart_chat WHERE teacher_phone=? AND student_phone=? ORDER BY id DESC LIMIT 20", 
                      (teacher_phone, student_phone))
            chats = c.fetchall()
            
        if chats:
            for s_role, s_msg, s_time in reversed(chats):
                bg_color = "#e0e7ff" if s_role == "أستاذ" else "#f3f4f6"
                st.markdown(f"<div style='background: {bg_color}; color: #000; padding: 10px; border-radius: 4px; margin-bottom: 6px; border: 1px solid #d1d5db;'><small style='color: #4b5563;'>[{s_time}] <b>{s_role}:</b></small><br>{s_msg}</div>", unsafe_allow_html=True)
        else:
            st.info("لا توجد رسائل سابقة في الشات.")
    except:
        pass

@st.fragment
def render_live_broadcast_section(teacher_phone, student_phone=None, is_subscriber=False, is_teacher_owner=False):
    st_autorefresh(interval=2500, key=f"live_broadcast_ref_{teacher_phone}_{student_phone}")
    
    if is_teacher_owner:
        st.subheader("📡 إعدادات البث المباشر والحصص")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT title, is_active, visibility, countdown_hours FROM live_broadcasts WHERE teacher_phone=?", (teacher_phone,))
                b_setting = c.fetchone()
        except:
            b_setting = None

        cur_b_title = b_setting[0] if b_setting else ""
        cur_b_active = b_setting[1] if b_setting else 0
        cur_b_vis = b_setting[2] if b_setting else "subscriber"
        cur_b_cd = b_setting[3] if b_setting else 0

        with st.form("teacher_live_settings_form_inside_room"):
            live_title_input = st.text_input("عنوان الحصة أو البث:", value=cur_b_title)
            live_active_toggle = st.selectbox("حالة البث:", ["إيقاف البث", "تشغيل البث"], index=1 if cur_b_active==1 else 0)
            live_vis_input = st.selectbox("صلاحية المشاهدة:", ["subscriber (للمشتركين فقط)", "public (للجميع)"], index=0 if cur_b_vis=="subscriber" else 1)
            live_countdown_input = st.number_input("مدة العد التنازلي لإغلاق البث بالساعات:", min_value=0, value=int(cur_b_cd))
            
            if st.form_submit_button("حفظ إعدادات البث"):
                new_active_val = 1 if live_active_toggle == "تشغيل البث" else 0
                new_vis_val = "subscriber" if "للمشتركين" in live_vis_input else "public"
                t_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("""INSERT OR REPLACE INTO live_broadcasts (teacher_phone, title, is_active, visibility, countdown_hours, started_at) 
                                   VALUES (?, ?, ?, ?, ?, ?)""", 
                                  (teacher_phone, live_title_input, new_active_val, new_vis_val, int(live_countdown_input), t_now_str))
                        conn.commit()
                    st.success("تم تحديث حالة البث بنجاح!")
                    st.rerun()
                except:
                    pass
        st.write("---")

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT title, is_active, visibility, countdown_hours, started_at FROM live_broadcasts WHERE teacher_phone=?", (teacher_phone,))
            b_row = c.fetchone()
            
        if b_row and b_row[1] == 1:
            title, active_status, visibility, countdown_h, started_str = b_row
            
            can_watch = False
            if visibility == "public":
                can_watch = True
            else:
                if is_subscriber or is_teacher_owner:
                    can_watch = True

            if can_watch or is_teacher_owner:
                st.markdown(f"<div class='success-badge'>🔴 بث مباشر نشط حالياً: {title}</div>", unsafe_allow_html=True)
                st.info("تم تفعيل البث بنجاح، يمكنك متابعة المحتوى هنا.")
            else:
                st.markdown("<div class='cash-banner'>🔒 عذراً، هذا البث المباشر مخصص **للمشتركين فقط** داخل غرفة الأستاذ.</div>", unsafe_allow_html=True)
        else:
            st.info("لا يوجد بث مباشر نشط حالياً من الأستاذ.")
    except:
        pass

@st.fragment
def render_student_exams(teacher_phone, student_phone):
    st.subheader("📝 الامتحانات التفاعلية")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, question, opt1, opt2, opt3, opt4, correct_answer FROM exams WHERE teacher_phone=? ORDER BY id DESC", (teacher_phone,))
            exams = c.fetchall()
            
        if exams:
            for idx, (ex_id, q, o1, o2, o3, o4, correct) in enumerate(exams):
                st.markdown(f"**السؤال ({idx+1}): {q}**")
                options = [o1, o2, o3, o4]
                with st.form(f"exam_q_{ex_id}"):
                    ans_choice = st.radio("اختر الإجابة:", options, key=f"ans_radio_{ex_id}")
                    submit_ans = st.form_submit_button("تأكيد الإجابة")
                    if submit_ans:
                        if ans_choice == correct:
                            st.success("🎉 إجابة صحيحة! تم منحك نقاط تفوق.")
                            try:
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET points = points + 10 WHERE phone=?", (student_phone,))
                                    conn.commit()
                            except:
                                pass
                        else:
                            st.error(f"❌ إجابة غير صحيحة. الإجابة الصحيحة: {correct}")
                st.write("---")
        else:
            st.info("لا توجد امتحانات مضافة.")
    except:
        pass

@st.fragment
def render_student_homeworks(teacher_phone, student_phone, student_name):
    st.subheader("📚 الواجبات المنزلية")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, title, description, deadline FROM homeworks WHERE teacher_phone=? ORDER BY id DESC", (teacher_phone,))
            hws = c.fetchall()
            
        if hws:
            for hw_id, hw_title, hw_desc, hw_dead in hws:
                st.markdown(f"📌 **{hw_title}** | الموعد: `{hw_dead}`")
                st.write(f"التفاصيل: {hw_desc}")
                with st.form(f"hw_submit_form_{hw_id}"):
                    ans_text = st.text_area("إجابتك النصية:", key=f"hw_txt_{hw_id}")
                    hw_file = st.file_uploader("إرفاق ملف:", type=["png", "jpg", "pdf"], key=f"hw_f_{hw_id}")
                    submit_hw_btn = st.form_submit_button("إرسال الحل")
                    if submit_hw_btn:
                        file_path = ""
                        if hw_file:
                            file_path = os.path.join(MEDIA_DIR, hw_file.name)
                            with open(file_path, "wb") as f:
                                f.write(hw_file.getbuffer())
                        t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO homework_submissions (homework_id, student_phone, student_name, answer_text, file_path, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                                          (hw_id, student_phone, student_name, ans_text, file_path, t_now))
                                conn.commit()
                            st.success("تم إرسال الحل بنجاح!")
                        except:
                            st.error("خطأ أثناء الإرسال.")
                st.write("---")
        else:
            st.info("لا توجد واجبات منزلية مطلوبة حالياً.")
    except:
        pass

@st.fragment
def display_student_media(teacher_phone, student_phone, is_subscriber=True):
    st_autorefresh(interval=2500, key=f"refresh_media_{teacher_phone}_{is_subscriber}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM users WHERE phone=?", (student_phone,))
            st_user_row = c.fetchone()
            student_name = st_user_row[0] if st_user_row else "طالب"

            if is_subscriber:
                c.execute("SELECT id, title, description, media_type, file_path, views_count, visibility FROM posts WHERE teacher_phone=? AND status='approved' ORDER BY id DESC", (teacher_phone,))
            else:
                c.execute("SELECT id, title, description, media_type, file_path, views_count, visibility FROM posts WHERE teacher_phone=? AND status='approved' AND visibility='public' ORDER BY id DESC", (teacher_phone,))
            posts = c.fetchall()
        
        if posts:
            for p_id, p_title, p_desc, p_type, p_path, views, p_vis in posts:
                display_views = max(30, views + 1)
                st.markdown(f"📌 **{p_title}** | 👁️ المشاهدات: **{display_views}**")
                if p_desc:
                    st.write(p_desc)
                
                if p_path and os.path.exists(p_path):
                    if p_type == "image":
                        st.image(p_path)
                    elif p_type == "video":
                        st.video(p_path)
                
                with st.expander("💬 التعليقات والمناقشة"):
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT student_name, comment_text, timestamp FROM comments WHERE post_id=? ORDER BY id DESC", (p_id,))
                        comms = c.fetchall()
                    if comms:
                        for c_name, c_text, c_time in comms:
                            st.markdown(f"💬 **{c_name}**: {c_text} <small style='color:gray;'>({c_time})</small>", unsafe_allow_html=True)
                    
                    with st.form(f"comm_form_{p_id}", clear_on_submit=True):
                        c_text_input = st.text_input("أضف تعليقك:", key=f"txt_{p_id}")
                        if st.form_submit_button("إرسال", key=f"btn_c_{p_id}") and c_text_input:
                            t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO comments (post_id, student_name, comment_text, timestamp) VALUES (?, ?, ?, ?)",
                                          (p_id, student_name, c_text_input, t_now))
                                conn.commit()
                            st.rerun()
                st.write("---")
        else:
            st.info("لا توجد منشورات متاحة.")
    except:
        pass

@st.fragment
def display_teacher_requests(teacher_phone):
    st_autorefresh(interval=2000, key=f"refresh_subs_{teacher_phone}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT student_phone, status, orange_cash_sender, requested_at FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
            subs = c.fetchall()
            
            if subs:
                now = datetime.datetime.now()
                for s_ph, status, orange_sender, req_at in subs:
                    c.execute("SELECT name FROM users WHERE phone=?", (s_ph,))
                    st_data = c.fetchone()
                    st_display_name = st_data[0] if st_data else s_ph

                    st.markdown(f"🎓 **{st_display_name}** | هاتف: `{s_ph}` | الحالة: **{status}**")
                    st.markdown(f"💳 **محول من:** `{orange_sender or 'غير متوفر'}` | وقت الطلب: `{req_at}`")
                    
                    with st.form(f"sub_manage_form_{s_ph}"):
                        col1, col2, col3 = st.columns(3)
                        acc_btn = col1.form_submit_button("✅ قبول دائم")
                        cancel_sub_btn = col2.form_submit_button("🗑️ إلغاء الاشتراك")
                        ref_btn = col3.form_submit_button("❌ رفض")
                        
                        if acc_btn:
                            exp_time = (now + datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE subscriptions SET status='active', expires_at=?, is_permanently_accepted=1 WHERE student_phone=? AND teacher_phone=?", 
                                      (exp_time, s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم قبول الطالب بنجاح!")
                            st.rerun()
                            
                        if cancel_sub_btn:
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم إلغاء الاشتراك وحذف الطالب!")
                            st.rerun()

                        if ref_btn:
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم حذف الطلب!")
                            st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد طلبات اشتراك معلقة.")
    except:
        pass

def render_top_complaint_section(phone, name, role):
    with st.expander("📢 إرسال شكوى أو مقترح للإدارة", expanded=False):
        with st.form("top_complaint_form", clear_on_submit=True):
            c_text = st.text_area("تفاصيل الشكوى أو الطلب:")
            if st.form_submit_button("إرسال الشكوى") and c_text:
                t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO complaints (sender_phone, sender_name, role, complaint_text, timestamp) VALUES (?, ?, ?, ?, ?)",
                                  (phone, name, role, c_text, t_now))
                        conn.commit()
                    st.success("تم إرسال شكواك بنجاح!")
                except:
                    pass

# ==========================================
# 5. الواجهة الرئيسية (Login & Dashboards)
# ==========================================
st.markdown("<h2 style='text-align: center;'>منصة نوفا التعليمية</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4b5563; margin-bottom: 20px;'>نظام إدارة الدروس الخصوصية والمكالمات الحية</p>", unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.markdown('<div class="classic-box">', unsafe_allow_html=True)
    role_choice = st.radio("اختر نوع الحساب:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if role_choice == "طالب 👨‍🎓":
        st.markdown('<div class="classic-box">', unsafe_allow_html=True)
        student_mode = st.radio("العملية:", ["تسجيل دخول", "حساب جديد", "نسيت كلمة المرور؟"], horizontal=True)
        st.write("---")
        
        if student_mode == "حساب جديد":
            with st.form("student_signup"):
                st.subheader("إنشاء حساب طالب")
                s_name = st.text_input("الاسم الكامل:")
                s_phone = st.text_input("رقم المحمول:")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_grade = st.text_input("المرحلة الدراسية:")
                if st.form_submit_button("تسجيل الحساب"):
                    if s_pass and s_phone and s_name:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=?", (s_phone,))
                                if c.fetchone():
                                    st.error("رقم المحمول مسجل مسبقاً!")
                                else:
                                    hashed_pass = hash_password(s_pass)
                                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                    c.execute("INSERT INTO users (phone, password, name, grade, role, points, is_blocked, created_at) VALUES (?, ?, ?, ?, 'طالب', 10, 0, ?)", 
                                              (s_phone, hashed_pass, s_name, s_grade, t_now))
                                    conn.commit()
                                    login_user(s_phone, "طالب")
                                    st.success("تم إنشاء الحساب بنجاح!")
                                    st.rerun()
                        except:
                            pass
                    else:
                        st.error("أكمل الحقول المطلوبة.")
        elif student_mode == "نسيت كلمة المرور؟":
            with st.form("student_forgot"):
                st.subheader("استعادة كلمة المرور")
                f_phone = st.text_input("رقم المحمول:")
                new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
                if st.form_submit_button("تحديث كلمة السر") and f_phone and new_pass:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT id FROM users WHERE phone=? AND role='طالب'", (f_phone,))
                            if c.fetchone():
                                hashed_new = hash_password(new_pass)
                                c.execute("UPDATE users SET password=? WHERE phone=? AND role='طالب'", (hashed_new, f_phone))
                                conn.commit()
                                st.success("تم التحديث بنجاح!")
                            else:
                                st.error("رقم المحمول غير مسجل!")
                    except:
                        pass
        else:
            with st.form("student_login"):
                st.subheader("دخول الطالب")
                s_phone_in = st.text_input("رقم المحمول:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                if st.form_submit_button("دخول المنصة"):
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_pass = hash_password(s_pass_in)
                            c.execute("SELECT phone, is_blocked FROM users WHERE phone=? AND password=? AND role='طالب'", (s_phone_in, hashed_pass))
                            user_row = c.fetchone()
                        if user_row:
                            p_val, is_blocked = user_row
                            if is_blocked == 1:
                                st.error("❌ حسابك محظور!")
                            else:
                                login_user(p_val, "طالب")
                                st.rerun()
                        else:
                            st.error("بيانات الدخول غير صحيحة!")
                    except:
                        pass
        st.markdown('</div>', unsafe_allow_html=True)

    elif role_choice == "أستاذ 👨‍🏫":
        st.markdown('<div class="classic-box">', unsafe_allow_html=True)
        teacher_mode = st.radio("العملية:", ["دخول الأستاذ", "حساب أستاذ جديد", "نسيت كلمة المرور؟"], horizontal=True)
        st.write("---")
        
        if teacher_mode == "حساب أستاذ جديد":
            with st.form("teacher_signup"):
                st.subheader("تسجيل أستاذ جديد")
                t_name_reg = st.text_input("الاسم الكامل:")
                t_phone_reg = st.text_input("رقم المحمول:")
                t_sub_reg = st.text_input("المادة الدراسية:")
                t_price_reg = st.number_input("سعر الاشتراك الشهري (جنيه):", min_value=10.0, value=100.0)
                t_secret_code = st.text_input("الكود السري المعتمد (901000):", type="password")
                if st.form_submit_button("إنشاء حساب الأستاذ"):
                    if t_secret_code.strip() == "901000" and t_phone_reg:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT phone FROM allowed_teachers WHERE phone=?", (t_phone_reg,))
                                if not c.fetchone():
                                    st.error("❌ هذا الرقم غير مصرح له!")
                                else:
                                    hashed_t_pass = hash_password(t_secret_code)
                                    c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id, rating, is_blocked) 
                                               VALUES (?, ?, ?, ?, 'عام', 35, ?, '', ?, 5.0, 0)""", 
                                              (t_phone_reg, hashed_t_pass, t_name_reg, t_sub_reg, t_price_reg, f"room_{t_phone_reg}"))
                                    c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (t_phone_reg, t_name_reg))
                                    conn.commit()
                                    login_user(t_phone_reg, "أستاذ")
                                    st.success("تم إنشاء الحساب بنجاح!")
                                    st.rerun()
                        except:
                            pass
                    else:
                        st.error("الكود السري خطأ أو الرقم غير مكتمل.")
        elif teacher_mode == "نسيت كلمة المرور؟":
            with st.form("teacher_forgot"):
                st.subheader("استعادة كلمة المرور للأستاذ")
                f_phone_t = st.text_input("رقم المحمول:")
                t_new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
                t_secret_code_f = st.text_input("الكود السري المعتمد (901000):", type="password")
                if st.form_submit_button("تحديث كلمة السر") and f_phone_t and t_new_pass:
                    if t_secret_code_f.strip() == "901000":
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM teachers WHERE phone=?", (f_phone_t,))
                                if c.fetchone():
                                    hashed_t_new = hash_password(t_new_pass)
                                    c.execute("UPDATE teachers SET password=? WHERE phone=?", (hashed_t_new, f_phone_t))
                                    c.execute("UPDATE users SET password=? WHERE phone=? AND role='أستاذ'", (hashed_t_new, f_phone_t))
                                    conn.commit()
                                    st.success("تم تحديث كلمة المرور بنجاح!")
                                else:
                                    st.error("رقم الأستاذ غير مسجل!")
                        except:
                            pass
                    else:
                        st.error("الكود السري غير صحيح!")
        else:
            with st.form("teacher_login"):
                st.subheader("دخول الأستاذ")
                t_phone_in = st.text_input("رقم المحمول:")
                t_pass_in = st.text_input("كلمة المرور أو الكود السري:", type="password")
                if st.form_submit_button("دخول لوحة التحكم"):
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_t_pass = hash_password(t_pass_in)
                            c.execute("SELECT phone, is_blocked FROM teachers WHERE phone=? AND password=?", (t_phone_in, hashed_t_pass))
                            t_row = c.fetchone()
                        if t_row:
                            p_val, is_blocked = t_row
                            if is_blocked == 1:
                                st.error("❌ حسابك محظور!")
                            else:
                                login_user(p_val, "أستاذ")
                                st.rerun()
                        else:
                            st.error("بيانات الدخول غير صحيحة!")
                    except:
                        pass
        st.markdown('</div>', unsafe_allow_html=True)

    elif role_choice == "مطور 👑":
        st.markdown('<div class="classic-box">', unsafe_allow_html=True)
        with st.form("developer_login"):
            st.subheader("دخول المطور الرئيسي")
            dev_code = st.text_input("كلمة مرور المطور:", type="password")
            if st.form_submit_button("دخول لوحة المطورين"):
                if dev_code == "901000":
                    login_user("01000000000", "مطور")
                    st.success("تم الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("كلمة مرور المطور غير صحيحة!")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    current_phone = st.session_state.user_phone
    current_role = st.session_state.user_role

    st.sidebar.markdown(f"👤 **حساب:** {current_role}")
    st.sidebar.markdown(f"📱 **الهاتف:** `{current_phone}`")
    if st.sidebar.button("تسجيل الخروج 🚪"):
        logout_user()
        st.rerun()

    st.sidebar.write("---")

    if current_role == "طالب":
        st.subheader("🎓 لوحة تحكم الطالب")
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, points, grade FROM users WHERE phone=?", (current_phone,))
                u_data = c.fetchone()
                if u_data:
                    st.markdown(f"أهلاً بك يا **{u_data[0]}** | المرحلة الدراسية: `{u_data[2]}` | نقاط التفوق: ⭐ **{u_data[1]}**")
        except:
            pass

        st.write("---")
        st.markdown("### 👨‍🏫 قائمة الأساتذة المتاحين:")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT phone, name, subject, price FROM teachers WHERE is_blocked=0")
                teachers_list = c.fetchall()

            if teachers_list:
                for t_ph, t_name, t_subj, t_prc in teachers_list:
                    with st.expander(f"الأستاذ: {t_name} - المادة: {t_subj} (السعر: {t_prc} جنيه)"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (current_phone, t_ph))
                            sub_row = c.fetchone()
                        
                        sub_status = sub_row[0] if sub_row else None

                        if sub_status == "active":
                            st.success("✅ أنت مشترك مع هذا الأستاذ بنجاح!")
                            
                            if st.button(f"الدخول لغرفة الأستاذ {t_name} 🚀", key=f"enter_room_{t_ph}"):
                                st.session_state.sub_target_teacher = t_ph
                                st.session_state.inside_teacher_room = True
                                st.rerun()
                        else:
                            st.warning("⚠️ لست مشتركاً حالياً أو طلبك قيد المراجعة.")
                            with st.form(f"sub_req_{t_ph}"):
                                orange_sender_phone = st.text_input("أدخل رقم محفظة أورانج كاش المحول منها:")
                                st.markdown(f"💳 تحويل الاشتراك بقيمة **{t_prc} جنيه** على رقم: `01200000000`")
                                submit_sub = st.form_submit_button("تأكيد طلب الاشتراك وإرسال البيانات")
                                if submit_sub and orange_sender_phone:
                                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                    try:
                                        with sqlite3.connect(DB_NAME) as conn:
                                            c = conn.cursor()
                                            c.execute("""INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status, orange_cash_sender, requested_at) 
                                                       VALUES (?, ?, 'pending', ?, ?)""", 
                                                      (current_phone, t_ph, orange_sender_phone, t_now))
                                            conn.commit()
                                        st.success("تم إرسال طلب الاشتراك للأستاذ بنجاح، في انتظار الموافقة!")
                                        st.rerun()
                                    except:
                                        pass
            else:
                st.info("لا يوجد أساتذة مسجلين حالياً.")
        except:
            pass

        if st.session_state.inside_teacher_room and st.session_state.sub_target_teacher:
            t_ph_room = st.session_state.sub_target_teacher
            st.write("---")
            if st.button("⬅️ العودة لقائمة الأساتذة"):
                st.session_state.inside_teacher_room = False
                st.session_state.sub_target_teacher = None
                st.rerun()

            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject FROM teachers WHERE phone=?", (t_ph_room,))
                    t_info = c.fetchone()
                    t_room_name = t_info[0] if t_info else "الأستاذ"
            except:
                t_room_name = "الأستاذ"

            st.markdown(f"## 🏫 غرفة الأستاذ: {t_room_name}")

            tab_live, tab_posts, tab_chat, tab_exams, tab_hw = st.tabs(["📡 البث الحي", "📚 المنشورات والملفات", "💬 الشات الخاص", "📝 الامتحانات", "📌 الواجبات"])

            with tab_live:
                render_live_broadcast_section(t_ph_room, student_phone=current_phone, is_subscriber=True, is_teacher_owner=False)

            with tab_posts:
                display_student_media(t_ph_room, current_phone, is_subscriber=True)

            with tab_chat:
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT name FROM users WHERE phone=?", (current_phone,))
                        st_name_row = c.fetchone()
                        st_name_val = st_name_row[0] if st_name_row else "طالب"
                except:
                    st_name_val = "طالب"
                render_smart_chat(t_ph_room, current_phone, st_name_val)

            with tab_exams:
                render_student_exams(t_ph_room, current_phone)

            with tab_hw:
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT name FROM users WHERE phone=?", (current_phone,))
                        st_name_row = c.fetchone()
                        st_name_val = st_name_row[0] if st_name_row else "طالب"
                except:
                    st_name_val = "طالب"
                render_student_homeworks(t_ph_room, current_phone, st_name_val)

        render_top_complaint_section(current_phone, "طالب", "طالب")

    elif current_role == "أستاذ":
        st.subheader("👨‍🏫 لوحة تحكم الأستاذ")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, subject, price FROM teachers WHERE phone=?", (current_phone,))
                t_profile = c.fetchone()
                if t_profile:
                    st.markdown(f"مرحباً أستاذ **{t_profile[0]}** | المادة: `{t_profile[1]}` | سعر الاشتراك: `{t_profile[2]} جنيه`")
        except:
            pass

        st.write("---")
        
        if st.button("🚀 الدخول إلى غرفة البث المباشر الخاصة بي"):
            st.session_state.sub_target_teacher = current_phone
            st.session_state.inside_teacher_room = True
            st.rerun()

        st.write("---")
        t_tab2, t_tab3, t_tab4, t_tab5, t_tab6 = st.tabs(["👥 طلبات الاشتراكات", "📝 إدارة المنشورات", "💬 الشات مع الطلاب", "📝 الامتحانات والواجبات", "⚙️ الإعدادات"])

        if st.session_state.inside_teacher_room and st.session_state.sub_target_teacher == current_phone:
            st.write("---")
            if st.button("⬅️ العودة للوحة التحكم الرئيسية للأستاذ"):
                st.session_state.inside_teacher_room = False
                st.session_state.sub_target_teacher = None
                st.rerun()

            st.markdown("## 🏫 غرفة البث المباشر الخاصة بك (الأستاذ)")
            render_live_broadcast_section(current_phone, student_phone=None, is_subscriber=True, is_teacher_owner=True)

        with t_tab2:
            st.markdown("### متابعة وقبول طلاب الاشتراك")
            display_teacher_requests(current_phone)

        with t_tab3:
            st.markdown("### إضافة منشور أو حصة مرئية جديدة")
            with st.form("teacher_add_post", clear_on_submit=True):
                p_title = st.text_input("عنوان المنشور أو الدرس:")
                p_desc = st.text_area("وصف المحتوى:")
                p_type = st.selectbox("نوع الملف:", ["image", "video", "text"])
                p_file = st.file_uploader("رفع ملف (صورة أو فيديو):", type=["png", "jpg", "mp4", "mov"])
                p_vis = st.selectbox("الظهور:", ["subscriber", "public"])
                
                if st.form_submit_button("نشر المحتوى"):
                    file_path = ""
                    if p_file:
                        file_path = os.path.join(MEDIA_DIR, p_file.name)
                        with open(file_path, "wb") as f:
                            f.write(p_file.getbuffer())
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("""INSERT INTO posts (teacher_phone, title, description, media_type, file_path, visibility, timestamp) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                                      (current_phone, p_title, p_desc, p_type, file_path, p_vis, t_now))
                            conn.commit()
                        st.success("تم النشر بنجاح!")
                        st.rerun()
                    except:
                        pass

        with t_tab4:
            st.markdown("### الرد على رسائل الطلاب الفورية")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT DISTINCT student_phone FROM smart_chat WHERE teacher_phone=?", (current_phone,))
                    chats_students = c.fetchall()
                
                if chats_students:
                    st_phone_list = [row[0] for row in chats_students]
                    chosen_student = st.selectbox("اختر الطالب للمحادثة:", st_phone_list)
                    if chosen_student:
                        render_smart_chat(current_phone, chosen_student, "أستاذ")
                else:
                    st.info("لا توجد محادثات نشطة مع الطلاب حتى الآن.")
            except:
                pass

        with t_tab5:
            st.markdown("### إضافة امتحان أو واجب منزلي")
            sub_opt = st.radio("اختر القسم:", ["إضافة سؤال امتحاني", "إضافة واجب منزلي"], horizontal=True)
            if sub_opt == "إضافة سؤال امتحاني":
                with st.form("add_exam_form", clear_on_submit=True):
                    q_text = st.text_input("نص السؤال:")
                    o1 = st.text_input("الخيار الأول:")
                    o2 = st.text_input("الخيار الثاني:")
                    o3 = st.text_input("الخيار الثالث:")
                    o4 = st.text_input("الخيار الرابع:")
                    correct_ans = st.text_input("الإجابة الصحيحة (يجب أن تطابق أحد الخيارات تماماً):")
                    if st.form_submit_button("حفظ وإضافة السؤال") and q_text:
                        t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("""INSERT INTO exams (teacher_phone, question, opt1, opt2, opt3, opt4, correct_answer, timestamp) 
                                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                                          (current_phone, q_text, o1, o2, o3, o4, correct_ans, t_now))
                                conn.commit()
                            st.success("تم إضافة السؤال بنجاح!")
                        except:
                            pass
            else:
                with st.form("add_hw_form", clear_on_submit=True):
                    hw_title = st.text_input("عنوان الواجب:")
                    hw_desc = st.text_area("تفاصيل الواجب والمطلوب:")
                    hw_dead = st.text_input("الموعد النهائي للتسليم (مثال: 2026-08-20):")
                    if st.form_submit_button("نشر الواجب") and hw_title:
                        t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("""INSERT INTO homeworks (teacher_phone, title, description, deadline, timestamp) 
                                           VALUES (?, ?, ?, ?, ?)""", 
                                          (current_phone, hw_title, hw_desc, hw_dead, t_now))
                                conn.commit()
                            st.success("تم نشر الواجب بنجاح!")
                        except:
                            pass

        with t_tab6:
            st.markdown("### إعدادات الحساب الشخصية للأستاذ")
            with st.form("update_teacher_profile"):
                new_t_name = st.text_input("تعديل الاسم:", value=t_profile[0] if 't_profile' in locals() and t_profile else "")
                new_t_price = st.number_input("تعديل سعر الاشتراك:", value=float(t_profile[2]) if 't_profile' in locals() and t_profile else 100.0)
                if st.form_submit_button("حفظ التعديلات"):
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE teachers SET name=?, price=? WHERE phone=?", (new_t_name, new_t_price, current_phone))
                            c.execute("UPDATE users SET name=? WHERE phone=?", (new_t_name, current_phone))
                            conn.commit()
                        st.success("تم تحديث البيانات بنجاح!")
                        st.rerun()
                    except:
                        pass

        render_top_complaint_section(current_phone, "أستاذ", "أستاذ")

    elif current_role == "مطور":
        st.subheader("👑 لوحة تحكم المطور الرئيسي")
        dev_tab1, dev_tab2 = st.tabs(["👥 إدارة الأساتذة المصرحين", "📢 شكاوى المستخدمين"])

        with dev_tab1:
            st.markdown("### إضافة رقم أستاذ جديد لقائمة السماح")
            with st.form("add_allowed_teacher_form", clear_on_submit=True):
                new_t_allowed_phone = st.text_input("رقم هاتف الأستاذ الجديد:")
                if st.form_submit_button("إضافة لقائمة السماح") and new_t_allowed_phone:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT OR IGNORE INTO allowed_teachers (phone) VALUES (?)", (new_t_allowed_phone,))
                            conn.commit()
                        st.success("تمت الإضافة بنجاح!")
                    except:
                        pass

            st.markdown("### قائمة الأساتذة المصرحين المسجلين حالياً")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT phone FROM allowed_teachers")
                    allowed_rows = c.fetchall()
                if allowed_rows:
                    for row in allowed_rows:
                        st.write(f"- هاتف مصرح: `{row[0]}`")
            except:
                pass

        with dev_tab2:
            st.markdown("### الشكاوى والمقترحات الواردة للإدارة")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT sender_phone, sender_name, role, complaint_text, timestamp FROM complaints ORDER BY id DESC")
                    comp_rows = c.fetchall()
                if comp_rows:
                    for c_ph, c_name, c_role, c_txt, c_time in comp_rows:
                        st.markdown(f"📌 **{c_name}** ({c_role}) | الهاتف: `{c_ph}` | الوقت: `{c_time}`")
                        st.write(f"الشكوى: {c_txt}")
                        st.write("---")
                else:
                    st.info("لا توجد شكاوى مسجلة.")
            except:
                pass
