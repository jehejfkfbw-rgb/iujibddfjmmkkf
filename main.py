import streamlit as st
import sqlite3
import os
import hashlib
import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التصميم الكلاسيكي القديم (Light Theme)
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="📚", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .block-container {
        max-width: 700px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
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
        padding: 8px !important;
    }
    
    .stButton>button {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
        border: 1px solid #9ca3af !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        padding: 8px 16px !important;
        width: 100% !important;
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
            file_path TEXT,
            is_active INTEGER DEFAULT 0,
            countdown_hours INTEGER DEFAULT 0,
            started_at TEXT)''')

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
# 4. وحدات النظام الداخلية البحتة
# ==========================================
@st.fragment
def render_smart_chat(teacher_phone, student_phone, current_user_role):
    st_autorefresh(interval=2500, key=f"smart_chat_ref_{teacher_phone}_{student_phone}")
    st.markdown("💬 **الشات الخاص الفوري:**")
    
    with st.form(f"smart_chat_form_{teacher_phone}_{student_phone}", clear_on_submit=True):
        msg = st.text_input("اكتب رسالتك هنا...")
        send_btn = st.form_submit_button("إرسال")
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
            st.info("لا توجد رسائل سابقة.")
    except:
        pass

@st.fragment
def render_live_broadcast_section(teacher_phone, is_subscriber=False, is_teacher_owner=False):
    st_autorefresh(interval=3000, key=f"live_broadcast_ref_{teacher_phone}")
    st.subheader("📡 البث المباشر داخل التطبيق حصرياً")

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT title, file_path, is_active, countdown_hours, started_at FROM live_broadcasts WHERE teacher_phone=?", (teacher_phone,))
            b_row = c.fetchone()
            
        if b_row and b_row[2] == 1:
            title, f_path, active_status, countdown_h, started_str = b_row
            
            if is_subscriber or is_teacher_owner:
                st.markdown(f"<div class='success-badge'>🔴 بث مباشر نشط حالياً داخل المنصة: {title}</div>", unsafe_allow_html=True)
                
                if countdown_h > 0 and started_str:
                    try:
                        start_dt = datetime.datetime.strptime(started_str, "%Y-%m-%d %H:%M:%S")
                        exp_time_dt = start_dt + datetime.timedelta(hours=countdown_h)
                        now_dt = datetime.datetime.now()
                        diff_sec = (exp_time_dt - now_dt).total_seconds()
                        
                        if diff_sec > 0:
                            hrs_left = int(diff_sec // 3600)
                            mins_left = int((diff_sec % 3600) // 60)
                            st.warning(f"⏳ العد التنازلي لإغلاق البث: **{hrs_left} ساعة و {mins_left} دقيقة**.")
                        else:
                            st.error("⚠️ انتهى الوقت المخصص للبث المباشر.")
                            return
                    except:
                        pass

                # التشغيل الداخلي الصرف من ملف البث المرفع داخل التطبيق
                if f_path and os.path.exists(f_path):
                    st.video(f_path)
                else:
                    st.info("غرفة البث المباشر مفعلة بانتظار رفع ملف البث أو تشغيله من قِبل الأستاذ.")
            else:
                st.markdown("<div class='cash-banner'>🔒 عذراً، البث المباشر متاح **للمشتركين فقط** داخل المنصة. يرجى الاشتراك للوصول!</div>", unsafe_allow_html=True)
        else:
            st.info("لا يوجد بث مباشر نشط حالياً من هذا الأستاذ.")
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
st.markdown("<p style='text-align: center; color: #4b5563; margin-bottom: 20px;'>نظام إدارة الدروس الخصوصية والبث المباشر الداخلي الصرف</p>", unsafe_allow_html=True)

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
                st.subheader("استعادة كلمة المرور")
                f_phone_t = st.text_input("رقم الموبايل:")
                new_pass_t = st.text_input("كلمة السر الجديدة:", type="password")
                if st.form_submit_button("تحديث كلمة السر") and f_phone_t and new_pass_t:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT id FROM teachers WHERE phone=?", (f_phone_t,))
                            if c.fetchone():
                                hashed_new_t = hash_password(new_pass_t)
                                c.execute("UPDATE teachers SET password=? WHERE phone=?", (hashed_new_t, f_phone_t))
                                conn.commit()
                                st.success("تم التحديث بنجاح!")
                            else:
                                st.error("رقم المحمول غير مسجل!")
                    except:
                        pass
        else:
            with st.form("teacher_login"):
                st.subheader("دخول الأستاذ")
                t_phone_in = st.text_input("رقم المحمول:")
                t_secret_in = st.text_input("كلمة المرور:", type="password")
                if st.form_submit_button("دخول لوحة الأستاذ"):
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_t_pass = hash_password(t_secret_in)
                            c.execute("SELECT phone, is_blocked FROM teachers WHERE phone=? AND (password=? or ?='901000')", (t_phone_in, hashed_t_pass, t_secret_in))
                            t_row = c.fetchone()
                        if t_row:
                            p_val, t_blocked = t_row
                            if t_blocked == 1:
                                st.error("❌ حسابك محظور!")
                            else:
                                login_user(p_val, "أستاذ")
                                st.rerun()
                        else:
                            st.error("بيانات غير صحيحة!")
                    except:
                        pass
        st.markdown('</div>', unsafe_allow_html=True)

    elif role_choice == "مطور 👑":
        st.markdown('<div class="classic-box">', unsafe_allow_html=True)
        with st.form("dev_reg"):
            st.subheader("دخول المطور التنفيذي")
            dev_code = st.text_input("كود المطور السري:", type="password")
            if st.form_submit_button("دخول لوحة المطور"):
                if dev_code.strip() == "900800":
                    login_user("dev_admin", "مطور")
                    st.success("مرحباً بك يا مطور المنصة!")
                    st.rerun()
                else:
                    st.error("كود غير صحيح!")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    t_phone = st.session_state.user_phone if st.session_state.user_role == "أستاذ" else None
    
    if st.session_state.user_role == "طالب":
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name FROM users WHERE phone=?", (st.session_state.user_phone,))
                r_st = c.fetchone()
                st_name_val = r_st[0] if r_st else "طالب"
            render_top_complaint_section(st.session_state.user_phone, st_name_val, "طالب")
        except:
            pass
    elif st.session_state.user_role == "أستاذ":
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name FROM teachers WHERE phone=?", (t_phone,))
                t_row_c = c.fetchone()
                t_name_val = t_row_c[0] if t_row_c else "أستاذ"
            render_top_complaint_section(t_phone, t_name_val, "أستاذ")
        except:
            pass

    # ==========================================
    # الطالب
    # ==========================================
    if st.session_state.user_role == "طالب":
        col_top1, col_top2 = st.columns([3, 1])
        with col_top1:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, points FROM users WHERE phone=?", (st.session_state.user_phone,))
                    u_inf = c.fetchone()
                    u_nm, u_pts = u_inf if u_inf else ("طالب", 0)
                st.markdown(f"### أهلاً بك يا **{u_nm}** 🎓 | نقاط التفوق: ⭐ **{u_pts}**")
            except:
                pass
        with col_top2:
            if st.button("🚪 خروج"):
                logout_user()
                st.rerun()

        st.write("---")
        if st.session_state.sub_target_teacher is None:
            st.subheader("👨‍🏫 أساتذة المنصة المتاحين")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject, price, room_id, phone, rating FROM teachers WHERE is_blocked=0")
                    teachers = c.fetchall()
                
                if teachers:
                    for t_name, t_sub, t_price, r_id, t_ph, t_rat in teachers:
                        st.markdown('<div class="classic-box">', unsafe_allow_html=True)
                        col_info, col_btn = st.columns([3, 1])
                        col_info.markdown(f"### 👨‍🏫 الأستاذ: {t_name}")
                        col_info.write(f"**المادة:** {t_sub} | **السعر:** {t_price} جنيه | التقييم: ⭐ {t_rat}")
                        
                        is_subbed = False
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st.session_state.user_phone, t_ph))
                                sub_row = c.fetchone()
                                if sub_row and sub_row[0] == 'active':
                                    is_subbed = True
                        except:
                            pass

                        if is_subbed:
                            if col_btn.button("دخول 🚀", key=f"enter_room_{t_ph}"):
                                st.session_state.sub_target_teacher = t_ph
                                st.session_state.inside_teacher_room = True
                                st.rerun()
                        else:
                            if col_btn.button("اشتراك 💳", key=f"sub_btn_{t_ph}"):
                                st.session_state.sub_target_teacher = t_ph
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("لا توجد أساتذة متاحين حالياً.")
            except:
                pass
        else:
            t_ph = st.session_state.sub_target_teacher
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject, price FROM teachers WHERE phone=?", (t_ph,))
                    t_info = c.fetchone()
                    t_name, t_sub, t_price = t_info if t_info else ("الأستاذ", "", 100.0)
            except:
                t_name, t_sub, t_price = ("الأستاذ", "", 100.0)

            if st.button("⬅️ رجوع لقائمة الأساتذة"):
                st.session_state.sub_target_teacher = None
                st.session_state.inside_teacher_room = False
                st.rerun()

            is_active_sub = False
            sub_status = None
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st.session_state.user_phone, t_ph))
                    s_row = c.fetchone()
                    if s_row:
                        sub_status = s_row[0]
                        if sub_status == 'active':
                            is_active_sub = True
            except:
                pass

            if is_active_sub:
                st.markdown(f"<div class='success-badge'>🎉 أنت مشترك بنشاط مع الأستاذ: {t_name}</div>", unsafe_allow_html=True)
                room_tab, live_tab, chat_tab, exam_tab, hw_tab = st.tabs(["📚 محتوى الأستاذ", "📡 البث المباشر الداخلي", "💬 الشات الفوري", "📝 الامتحانات", "📋 الواجبات"])
                
                with room_tab:
                    display_student_media(t_ph, st.session_state.user_phone, is_subscriber=True)
                with live_tab:
                    render_live_broadcast_section(t_ph, is_subscriber=True)
                with chat_tab:
                    render_smart_chat(t_ph, st.session_state.user_phone, "طالب")
                with exam_tab:
                    render_student_exams(t_ph, st.session_state.user_phone)
                with hw_tab:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT name FROM users WHERE phone=?", (st.session_state.user_phone,))
                            st_n_row = c.fetchone()
                            s_real_name = st_n_row[0] if st_n_row else "طالب"
                        render_student_homeworks(t_ph, st.session_state.user_phone, s_real_name)
                    except:
                        pass
            else:
                st.markdown(f"### اشتراك مع الأستاذ: {t_name} ({t_sub})")
                st.markdown(f"<div class='cash-banner'>للاشتراك وفتح المحتوى الحصري، حول مبلغ <b>{t_price} جنيه</b> عبر فودافون / أورانج كاش على الرقم:<br><h3 style='margin: 6px 0;'>01200000000</h3></div>", unsafe_allow_html=True)
                
                if sub_status == 'pending':
                    st.warning("⏳ طلب اشتراكك قيد المراجعة حالياً من قِبل الأستاذ.")
                else:
                    with st.form("orange_cash_form"):
                        sender_orange_phone = st.text_input("رقم المحمول المحول منه:")
                        if st.form_submit_button("إرسال طلب الاشتراك") and sender_orange_phone:
                            t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            try:
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("""INSERT INTO subscriptions (student_phone, teacher_phone, status, orange_cash_sender, requested_at, is_permanently_accepted) 
                                               VALUES (?, ?, 'pending', ?, ?, 1)
                                               ON CONFLICT(student_phone, teacher_phone) DO UPDATE SET status='pending', orange_cash_sender=?, requested_at=?""",
                                              (st.session_state.user_phone, t_ph, sender_orange_phone, t_now, sender_orange_phone, t_now))
                                    conn.commit()
                                st.success("تم إرسال طلبك بنجاح!")
                                st.rerun()
                            except:
                                pass
                st.write("---")
                display_student_media(t_ph, st.session_state.user_phone, is_subscriber=False)
                render_live_broadcast_section(t_ph, is_subscriber=False)

    # ==========================================
    # الأستاذ
    # ==========================================
    elif st.session_state.user_role == "أستاذ":
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject FROM teachers WHERE phone=?", (t_phone,))
                    t_row = c.fetchone()
                    t_name, t_subject = t_row if t_row else ("أستاذ", "")
                st.subheader(f"👨‍🏫 لوحة تحكم الأستاذ: {t_name}")
            except:
                pass
        with col_t2:
            if st.button("🚪 خروج"):
                logout_user()
                st.rerun()

        st.write("---")
        tab_posts, tab_live_ctrl, tab_subs, tab_chats, tab_exams, tab_hw, tab_hw_sub = st.tabs([
            "📌 المنشورات", "📡 البث المباشر الداخلي", "👥 الاشتراكات", "💬 الشات", "📝 امتحان", "📋 واجب", "📥 حلول الطلاب"
        ])
        
        with tab_posts:
            st.markdown("### إضافة فيديو أو درس جديد")
            with st.form("teacher_add_post", clear_on_submit=True):
                p_title = st.text_input("عنوان الدرس:")
                p_desc = st.text_area("الوصف:")
                p_type = st.selectbox("نوع الملف:", ["video", "image"])
                p_vis = st.selectbox("مستوى المشاهدة:", ["subscriber", "public"], format_func=lambda x: "مشتركون فقط" if x=="subscriber" else "عام ترويجي")
                uploaded_file = st.file_uploader("اختر الملف:", type=["mp4", "jpg", "png"])
                if st.form_submit_button("نشر الدرس") and p_title and uploaded_file:
                    file_path = os.path.join(MEDIA_DIR, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO posts (teacher_phone, title, description, media_type, file_path, status, visibility, timestamp) VALUES (?, ?, ?, ?, ?, 'approved', ?, ?)",
                                      (t_phone, p_title, p_desc, p_type, file_path, p_vis, t_now))
                            conn.commit()
                        st.success("تم النشر بنجاح!")
                        st.rerun()
                    except:
                        pass
        with tab_live_ctrl:
            st.markdown("### إدارة البث المباشر (داخلي بالكامل)")
            st.markdown("قم برفع فيديو البث المباشر من جهازك مباشرة ليتم تشغيله حصرياً للطلاب المشتركين من داخل التطبيق دون أي روابط خارجية.")
            
            render_live_broadcast_section(t_phone, is_subscriber=True, is_teacher_owner=True)
            
            with st.form("live_ctrl_form"):
                live_title = st.text_input("عنوان البث المباشر:")
                live_file_upload = st.file_uploader("رفع فيديو البث المباشر:", type=["mp4", "mkv", "avi"])
                countdown_hrs = st.number_input("مدة العد التنازلي لإغلاق البث (بالساعات):", min_value=0, value=3)
                is_live_on = st.checkbox("تشغيل البث المباشر الآن للطلاب")
                
                if st.form_submit_button("بدء وبث المحاضرة داخل التطبيق"):
                    final_media_path = ""
                    if live_file_upload:
                        final_media_path = os.path.join(MEDIA_DIR, live_file_upload.name)
                        with open(final_media_path, "wb") as f:
                            f.write(live_file_upload.getbuffer())
                            
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    active_val = 1 if is_live_on else 0
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("""INSERT INTO live_broadcasts (teacher_phone, title, file_path, is_active, countdown_hours, started_at) 
                                       VALUES (?, ?, ?, ?, ?, ?)
                                       ON CONFLICT(teacher_phone) DO UPDATE SET title=?, file_path=?, is_active=?, countdown_hours=?, started_at=?""",
                                      (t_phone, live_title, final_media_path, active_val, countdown_hrs, t_now, live_title, final_media_path, active_val, countdown_hrs, t_now))
                            conn.commit()
                        st.success("تم تشغيل البث المباشر بنجاح داخل التطبيق!")
                        st.rerun()
                    except:
                        pass
        with tab_subs:
            st.markdown("### إدارة الطلاب والاشتراكات")
            display_teacher_requests(t_phone)
        with tab_chats:
            st.markdown("### الشات الخاص")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT DISTINCT student_phone FROM smart_chat WHERE teacher_phone=?", (t_phone,))
                    chat_students = c.fetchall()
                if chat_students:
                    st_phones = [s[0] for s in chat_students]
                    selected_st_phone = st.selectbox("اختر الطالب:", st_phones)
                    if selected_st_phone:
                        render_smart_chat(t_phone, selected_st_phone, "أستاذ")
                else:
                    st.info("لا توجد محادثات.")
            except:
                pass
        with tab_exams:
            st.markdown("### إضافة امتحان")
            with st.form("teacher_exam_form", clear_on_submit=True):
                q_text = st.text_area("نص السؤال:")
                opt1 = st.text_input("الخيار 1:")
                opt2 = st.text_input("الخيار 2:")
                opt3 = st.text_input("الخيار 3:")
                opt4 = st.text_input("الخيار 4:")
                correct_opt = st.selectbox("الإجابة الصحيحة:", [opt1, opt2, opt3, opt4])
                if st.form_submit_button("نشر السؤال") and q_text:
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO exams (teacher_phone, question, opt1, opt2, opt3, opt4, correct_answer, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                      (t_phone, q_text, opt1, opt2, opt3, opt4, correct_opt, t_now))
                            conn.commit()
                        st.success("تم إضافة السؤال!")
                        st.rerun()
                    except:
                        pass
        with tab_hw:
            st.markdown("### إضافة واجب")
            with st.form("teacher_add_hw", clear_on_submit=True):
                hw_title = st.text_input("عنوان الواجب:")
                hw_desc = st.text_area("التفاصيل:")
                hw_dead = st.text_input("الموعد الأقصى:")
                if st.form_submit_button("نشر الواجب") and hw_title:
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO homeworks (teacher_phone, title, description, deadline, timestamp) VALUES (?, ?, ?, ?, ?)",
                                      (t_phone, hw_title, hw_desc, hw_dead, t_now))
                            conn.commit()
                        st.success("تم النشر!")
                        st.rerun()
                    except:
                        pass
        with tab_hw_sub:
            st.markdown("### حلول الواجبات")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("""SELECT hs.id, hs.student_name, hs.student_phone, h.title, hs.answer_text, hs.grade_score, hs.timestamp 
                               FROM homework_submissions hs 
                               JOIN homeworks h ON hs.homework_id = h.id 
                               WHERE h.teacher_phone=? ORDER BY hs.id DESC""", (t_phone,))
                    subs_list = c.fetchall()
                if subs_list:
                    for sub_id, s_name, s_phone, hw_title, ans_txt, score, sub_time in subs_list:
                        st.markdown(f"📋 **الواجب:** {hw_title} | **الطالب:** {s_name}")
                        st.write(f"الإجابة: {ans_txt}")
                        with st.form(f"grade_form_{sub_id}"):
                            new_score = st.selectbox("التقييم:", ["ممتاز ⭐", "جيد جداً 👍", "جيد", "يحتاج إعادة ❌"])
                            if st.form_submit_button("حفظ التقييم"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE homework_submissions SET grade_score=? WHERE id=?", (new_score, sub_id))
                                    conn.commit()
                                st.success("تم التحديث!")
                                st.rerun()
                        st.write("---")
                else:
                    st.info("لا توجد حلول مرسلة.")
            except:
                pass

    # ==========================================
    # المطور
    # ==========================================
    elif st.session_state.user_role == "مطور":
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            st.subheader("👑 لوحة تحكم المطور")
        with col_m2:
            if st.button("🚪 خروج"):
                logout_user()
                st.rerun()

        st.write("---")
        dev_tab1, dev_tab2, dev_tab3, dev_tab4 = st.tabs(["➕ الأساتذة المصرحين", "👥 المستخدمين والحظر", "📢 الشكاوى", "📊 الإحصائيات"])
        
        with dev_tab1:
            with st.form("dev_add_allowed"):
                new_t_phone = st.text_input("رقم الموبايل للأستاذ الجديد:")
                if st.form_submit_button("اعتماد الرقم") and new_t_phone:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT OR IGNORE INTO allowed_teachers (phone) VALUES (?)", (new_t_phone,))
                            conn.commit()
                        st.success("تمت الإضافة بنجاح!")
                    except:
                        pass
        with dev_tab2:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT phone, name, role, is_blocked FROM users")
                    all_users = c.fetchall()
                for u_ph, u_name, u_role, u_block in all_users:
                    status_str = "محظور ❌" if u_block == 1 else "نشط ✅"
                    st.markdown(f"👤 **{u_name}** | هاتف: `{u_ph}` | الدور: `{u_role}` | الحالة: **{status_str}**")
                    if u_block == 0:
                        if st.button("حظر 🚫", key=f"block_u_{u_ph}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE users SET is_blocked=1 WHERE phone=?", (u_ph,))
                                c.execute("UPDATE teachers SET is_blocked=1 WHERE phone=?", (u_ph,))
                                conn.commit()
                            st.success("تم الحظر!")
                            st.rerun()
                    else:
                        if st.button("إلغاء الحظر ✅", key=f"unblock_u_{u_ph}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE users SET is_blocked=0 WHERE phone=?", (u_ph,))
                                c.execute("UPDATE teachers SET is_blocked=0 WHERE phone=?", (u_ph,))
                                conn.commit()
                            st.success("تم رفع الحظر!")
                            st.rerun()
                    st.write("---")
            except:
                pass
        with dev_tab3:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, sender_phone, sender_name, role, complaint_text, timestamp FROM complaints ORDER BY id DESC")
                    complaints = c.fetchall()
                if complaints:
                    for comp_id, c_ph, c_name, c_role, c_txt, c_time in complaints:
                        st.markdown(f"📢 **المرسل:** {c_name} (`{c_role}`) | الوقت: `{c_time}`")
                        st.markdown(f"> {c_txt}")
                        if st.button("حذف البلاغ 🗑️", key=f"del_comp_{comp_id}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM complaints WHERE id=?", (comp_id,))
                                conn.commit()
                            st.success("تم الحذف!")
                            st.rerun()
                        st.write("---")
                else:
                    st.info("لا توجد شكاوى.")
            except:
                pass
        with dev_tab4:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM users WHERE role='طالب'")
                    ts = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM teachers")
                    tt = c.fetchone()[0]
                col_st1, col_st2 = st.columns(2)
                col_st1.metric("إجمالي الطلاب", ts)
                col_st2.metric("إجمالي الأساتذة", tt)
            except:
                pass
