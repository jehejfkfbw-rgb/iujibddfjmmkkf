import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components
import hashlib
import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التطبيق وتصميم الواجهة
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .block-container {
        max-width: 600px !important;
        padding-top: 1.0rem !important;
        padding-bottom: 2rem !important;
    }
    
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #f8fafc !important;
        color: #1e293b !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    h1, h2, h3, h4 {
        color: #4f46e5 !important;
        font-weight: bold !important;
    }
    
    .stTextInput input, .stNumberInput input, .stPasswordInput input, .stTextArea textarea {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 12px 20px !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
    }
    
    .app-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 16px !important;
    }
    
    .cash-box {
        background: #fff7ed !important;
        color: #9a3412 !important;
        padding: 14px !important;
        border-radius: 12px !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 15px !important;
        margin: 12px 0 !important;
        border: 1px solid #fdba74 !important;
    }
    
    .success-alert {
        background: #f0fdf4 !important;
        color: #166534 !important;
        padding: 15px !important;
        border-radius: 14px !important;
        border: 1px solid #bbf7d0 !important;
        font-weight: bold !important;
        text-align: center !important;
        margin: 15px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد قاعدة البيانات والجداول
# ==========================================
MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

DB_NAME = 'nova_complete_system.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, email TEXT UNIQUE,
            password TEXT, name TEXT, age TEXT, grade TEXT, role TEXT, is_blocked INTEGER DEFAULT 0)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, password TEXT, name TEXT, subject TEXT,
            grade_level TEXT, age INTEGER, price REAL, image_url TEXT, room_id TEXT, is_blocked INTEGER DEFAULT 0)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS allowed_teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, teacher_phone TEXT,
            status TEXT DEFAULT 'pending', orange_cash_sender TEXT, requested_at TEXT, expires_at TEXT, UNIQUE(student_phone, teacher_phone))''')
            
        try:
            c.execute("ALTER TABLE subscriptions ADD COLUMN orange_cash_sender TEXT")
        except:
            pass

        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, title TEXT,
            media_type TEXT, file_path TEXT, status TEXT DEFAULT 'approved', views_count INTEGER DEFAULT 0)''')

        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, student_name TEXT, comment_text TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS live_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT, sender_phone TEXT, sender_name TEXT, message TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS smart_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, student_phone TEXT, sender_role TEXT, message TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT, sender_phone TEXT, sender_name TEXT, role TEXT, complaint_text TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, question TEXT,
            opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT, correct_answer TEXT, timestamp TEXT)''')
            
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

# متغير لحالة الدخول لقاعة الأستاذ بعد قبول الاشتراك
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
# 4. الشات الذكي بين الأستاذ والطالب
# ==========================================
@st.fragment
def render_smart_chat(teacher_phone, student_phone, current_user_role):
    st_autorefresh(interval=2000, key=f"smart_chat_ref_{teacher_phone}_{student_phone}")
    st.markdown("💬 **الشات الخاص المباشر:**")
    
    with st.form(f"smart_chat_form_{teacher_phone}_{student_phone}", clear_on_submit=True):
        msg = st.text_input("اكتب رسالتك هنا...")
        send_btn = st.form_submit_button("إرسال الرسالة")
        if send_btn and msg:
            t_now = datetime.datetime.now().strftime("%H:%M")
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
            c.execute("SELECT sender_role, message, timestamp FROM smart_chat WHERE teacher_phone=? AND student_phone=? ORDER BY id DESC LIMIT 15", 
                      (teacher_phone, student_phone))
            chats = c.fetchall()
            
        if chats:
            for s_role, s_msg, s_time in reversed(chats):
                bg_color = "#4f46e5" if s_role == "أستاذ" else "#1e293b"
                align_style = "text-align: right;"
                st.markdown(f"<div style='background: {bg_color}; color: #fff; padding: 10px 14px; border-radius: 12px; margin-bottom: 6px; {align_style}'><small style='color: #cbd5e1;'>[{s_time}] <b>{s_role}:</b></small><br>{s_msg}</div>", unsafe_allow_html=True)
        else:
            st.info("لا توجد رسائل سابقة في الشات الخاص. ابدأ المحادثة الآن!")
    except:
        pass

# ==========================================
# 5. قسم الامتحانات للطالب
# ==========================================
@st.fragment
def render_student_exams(teacher_phone):
    st.subheader("📝 امتحانات واختبارات الأستاذ")
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
                    ans_choice = st.radio("اختر الإجابة الصحيحة:", options, key=f"ans_radio_{ex_id}")
                    submit_ans = st.form_submit_button("تأكيد الإجابة")
                    
                    if submit_ans:
                        if ans_choice == correct:
                            st.success("🎉 إجابة صحيحة برافو عليك!")
                        else:
                            st.error(f"❌ إجابة خاطئة. الإجابة الصحيحة هي: {correct}")
                st.write("---")
        else:
            st.info("لا توجد امتحانات مضافة من هذا الأستاذ حالياً.")
    except:
        pass

# ==========================================
# 6. عرض المحتوى والتحكم
# ==========================================
@st.fragment
def display_student_media(teacher_phone, student_phone):
    st_autorefresh(interval=2000, key=f"refresh_media_{teacher_phone}")

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM users WHERE phone=?", (student_phone,))
            st_user_row = c.fetchone()
            student_name = st_user_row[0] if st_user_row else "طالب"

            c.execute("SELECT id, title, media_type, file_path, views_count FROM posts WHERE teacher_phone=? AND status='approved' ORDER BY id DESC", (teacher_phone,))
            posts = c.fetchall()
        
        if posts:
            for p_id, p_title, p_type, p_path, views in posts:
                display_views = max(25, views + 25)
                st.markdown(f"📌 **{p_title}** | 👁️ المشاهدات: **{display_views}**")
                
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE posts SET views_count = views_count + 1 WHERE id=?", (p_id,))
                        conn.commit()
                except:
                    pass

                if p_path and os.path.exists(p_path):
                    if p_type == "image":
                        st.image(p_path)
                    elif p_type == "video":
                        st.video(p_path)
                else:
                    st.warning("⚠️ ملف الفيديو أو الصورة غير موجود في مسار التخزين.")
                
                with st.expander("💬 التعليقات والمناقشة"):
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT student_name, comment_text, timestamp FROM comments WHERE post_id=? ORDER BY id DESC", (p_id,))
                        comms = c.fetchall()
                    
                    if comms:
                        for c_name, c_text, c_time in comms:
                            st.markdown(f"💬 **{c_name}**: {c_text} <small style='color:gray;'>({c_time})</small>", unsafe_allow_html=True)
                    else:
                        st.write("لا توجد تعليقات بعد.")

                    with st.form(f"comm_form_{p_id}", clear_on_submit=True):
                        c_text_input = st.text_input("أضف تعليقك:", key=f"txt_{p_id}")
                        c_btn = st.form_submit_button("تعليق", key=f"btn_c_{p_id}")
                        if c_btn and c_text_input:
                            t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO comments (post_id, student_name, comment_text, timestamp) VALUES (?, ?, ?, ?)",
                                          (p_id, student_name, c_text_input, t_now))
                                conn.commit()
                            st.rerun()
                st.write("---")
        else:
            st.info("لا توجد منشورات أو فيديوهات متاحة حالياً من هذا الأستاذ.")
    except:
        pass

@st.fragment
def display_teacher_requests(teacher_phone):
    st_autorefresh(interval=1500, key=f"refresh_subs_{teacher_phone}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT student_phone, status, orange_cash_sender, requested_at, expires_at FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
            subs = c.fetchall()
            
            if subs:
                now = datetime.datetime.now()
                for s_ph, status, orange_sender, req_at, expires_at in subs:
                    if status == 'active' and expires_at:
                        try:
                            exp_dt = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                            if now > exp_dt:
                                c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                                conn.commit()
                                continue
                        except:
                            pass

                    c.execute("SELECT name FROM users WHERE phone=?", (s_ph,))
                    st_data = c.fetchone()
                    st_display_name = st_data[0] if st_data else s_ph

                    st.markdown(f"🎓 **{st_display_name}** | هاتف الطالب: `{s_ph}` | الحالة: **{status}**")
                    st.markdown(f"💳 **رقم أورانج كاش المحول منه:** `{orange_sender or 'غير متوفر'}` | وقت الطلب: `{req_at}`")
                    
                    with st.form(f"sub_manage_form_{s_ph}"):
                        col_act1, col_act2 = st.columns(2)
                        acc_btn = col_act1.form_submit_button("✅ قبول وتفعيل الاشتراك")
                        ref_btn = col_act2.form_submit_button("❌ حذف / رفض")
                        
                        if acc_btn:
                            exp_time = (now + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE subscriptions SET status='active', expires_at=? WHERE student_phone=? AND teacher_phone=?", 
                                      (exp_time, s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم تفعيل اشتراك الطالب بنجاح!")
                            st.rerun()
                            
                        if ref_btn:
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم حذف الطلب!")
                            st.rerun()
                            
                    st.write("---")
            else:
                st.info("لا توجد طلبات اشتراك معلقة حالياً.")
    except:
        pass

def render_top_complaint_section(phone, name, role):
    with st.expander("📢 إرسال شكوى أو بلاغ للمطور (اضغط هنا)", expanded=False):
        with st.form("top_complaint_form", clear_on_submit=True):
            st.markdown("<b>إرسال شكوى مباشرة للإدارة والمطور:</b>", unsafe_allow_html=True)
            c_text = st.text_area("اكتب تفاصيل الشكوى أو البلاغ هنا:")
            c_submit = st.form_submit_button("إرسال الشكوى فوراً")
            if c_submit and c_text:
                t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO complaints (sender_phone, sender_name, role, complaint_text, timestamp) VALUES (?, ?, ?, ?, ?)",
                                  (phone, name, role, c_text, t_now))
                        conn.commit()
                    st.success("تم إرسال شكواك بنجاح للمطور وسيتم مراجعتها فوراً.")
                except:
                    st.error("حدث خطأ أثناء الإرسال.")

# ==========================================
# 7. الواجهة الرئيسية
# ==========================================
st.markdown("<h2 style='text-align: center;'>⚡ منصة نوفا التعليمية</h2>", unsafe_allow_html=True)
st.write("---")

if not st.session_state.is_logged_in:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    role_choice = st.radio("نوع الحساب:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑"], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if role_choice == "طالب 👨‍🎓":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        student_mode = st.radio("العملية:", ["تسجيل دخول", "حساب جديد", "هل نسيت كلمة السر؟"], horizontal=True)
        st.write("---")
        
        if student_mode == "حساب جديد":
            with st.form("student_signup"):
                st.subheader("حساب طالب جديد")
                s_name = st.text_input("الاسم الكامل:")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_phone = st.text_input("رقم المحمول:")
                s_grade = st.text_input("المرحلة الدراسية:")
                s_signup_btn = st.form_submit_button("تسجيل")
                
                if s_signup_btn:
                    if s_pass and s_phone:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=?", (s_phone,))
                                if c.fetchone():
                                    st.error("رقم المحمول مسجل مسبقاً!")
                                else:
                                    hashed_pass = hash_password(s_pass)
                                    c.execute("INSERT INTO users (phone, password, name, grade, role, is_blocked) VALUES (?, ?, ?, ?, 'طالب', 0)", 
                                              (s_phone, hashed_pass, s_name if s_name else "طالب", s_grade))
                                    conn.commit()
                                    login_user(s_phone, "طالب")
                                    st.rerun()
                        except:
                            pass
                            
        elif student_mode == "هل نسيت كلمة السر؟":
            with st.form("student_forgot"):
                st.subheader("استعادة كلمة السر (طالب)")
                f_phone = st.text_input("أدخل رقم المحمول الخاص بك:")
                new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
                reset_btn = st.form_submit_button("تغيير كلمة السر")
                
                if reset_btn:
                    if f_phone and new_pass:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=? AND role='طالب'", (f_phone,))
                                if c.fetchone():
                                    hashed_new = hash_password(new_pass)
                                    c.execute("UPDATE users SET password=? WHERE phone=? AND role='طالب'", (hashed_new, f_phone))
                                    conn.commit()
                                    st.success("تم تغيير كلمة السر بنجاح! يمكنك تسجيل الدخول الآن.")
                                else:
                                    st.error("رقم المحمول غير مسجل في النظام!")
                        except:
                            pass
                    else:
                        st.error("الرجاء إدخال رقم الموبايل وكلمة المرور الجديدة.")
        else:
            with st.form("student_login"):
                st.subheader("دخول الطالب")
                s_phone_in = st.text_input("رقم المحمول:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                s_login_btn = st.form_submit_button("دخول")
                
                if s_login_btn:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_pass = hash_password(s_pass_in)
                            c.execute("SELECT phone, is_blocked FROM users WHERE phone=? AND password=? AND role='طالب'", (s_phone_in, hashed_pass))
                            user_row = c.fetchone()
                        
                        if user_row:
                            p_val, is_blocked = user_row
                            if is_blocked == 1:
                                st.error("❌ حسابك محظور من قبل الإدارة والمطور!")
                            else:
                                login_user(p_val, "طالب")
                                st.rerun()
                        else:
                            st.error("بيانات غير صحيحة!")
                    except:
                        pass
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "أستاذ 👨‍🏫":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        teacher_mode = st.radio("العملية:", ["دخول الأستاذ", "حساب جديد للأستاذ", "هل نسيت كلمة السر؟"], horizontal=True)
        st.write("---")
        
        if teacher_mode == "حساب جديد للأستاذ":
            with st.form("teacher_signup"):
                st.subheader("حساب أستاذ جديد")
                t_name_reg = st.text_input("اسم الأستاذ:")
                t_phone_reg = st.text_input("رقم المحمول:")
                t_sub_reg = st.text_input("المادة الدراسية:")
                t_secret_code = st.text_input("الكود السري (901000):", type="password")
                t_signup_btn = st.form_submit_button("إنشاء الحساب")
                
                if t_signup_btn:
                    if t_secret_code.strip() == "901000" and t_phone_reg:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT phone FROM allowed_teachers WHERE phone=?", (t_phone_reg,))
                                allowed_row = c.fetchone()
                                
                                if not allowed_row:
                                    st.error("❌ هذا الرقم غير مسجل ومصرح له من قبل المطور!")
                                else:
                                    c.execute("SELECT id FROM teachers WHERE phone=?", (t_phone_reg,))
                                    if c.fetchone():
                                        st.error("هذا الرقم مسجل بحساب أستاذ بالفعل!")
                                    else:
                                        hashed_t_pass = hash_password(t_secret_code)
                                        c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id, is_blocked) 
                                                   VALUES (?, ?, ?, ?, 'جميع المراحل', 30, 100.0, '', ?, 0)""", 
                                                  (t_phone_reg, hashed_t_pass, t_name_reg, t_sub_reg, f"room_{t_phone_reg}"))
                                        c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (t_phone_reg, t_name_reg))
                                        conn.commit()
                                        login_user(t_phone_reg, "أستاذ")
                                        st.rerun()
                        except:
                            pass
                    else:
                        st.error("الكود السري غير صحيح أو رقم المحمول ناقص!")
                        
        elif teacher_mode == "هل نسيت كلمة السر؟":
            with st.form("teacher_forgot"):
                st.subheader("استعادة كلمة السر (أستاذ)")
                f_phone_t = st.text_input("أدخل رقم محمول الأستاذ:")
                new_pass_t = st.text_input("كلمة المرور/الكود الجديد:", type="password")
                reset_btn_t = st.form_submit_button("تحديث كلمة السر")
                
                if reset_btn_t:
                    if f_phone_t and new_pass_t:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM teachers WHERE phone=?", (f_phone_t,))
                                if c.fetchone():
                                    hashed_new_t = hash_password(new_pass_t)
                                    c.execute("UPDATE teachers SET password=? WHERE phone=?", (hashed_new_t, f_phone_t))
                                    conn.commit()
                                    st.success("تم تحديث كلمة المرور للأستاذ بنجاح!")
                                else:
                                    st.error("رقم المحمول غير مسجل كأستاذ!")
                        except:
                            pass
                    else:
                        st.error("أدخل رقم الموبايل وكلمة السر الجديدة.")
        else:
            with st.form("teacher_login"):
                st.subheader("دخول الأستاذ")
                t_phone_in = st.text_input("رقم المحمول:")
                t_secret_in = st.text_input("كلمة المرور:", type="password")
                t_login_btn = st.form_submit_button("دخول")
                
                if t_login_btn:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_t_pass = hash_password(t_secret_in)
                            c.execute("SELECT phone, is_blocked FROM teachers WHERE phone=? AND (password=? or ?='901000')", (t_phone_in, hashed_t_pass, t_secret_in))
                            t_row = c.fetchone()
                        
                        if t_row:
                            p_val, t_blocked = t_row
                            if t_blocked == 1:
                                st.error("❌ حساب الأستاذ محظور من قبل المطور!")
                            else:
                                login_user(p_val, "أستاذ")
                                st.rerun()
                        else:
                            st.error("بيانات غير صحيحة!")
                    except:
                        pass
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "مطور 👑":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        with st.form("dev_reg"):
            st.subheader("دخول المطور")
            dev_code = st.text_input("كود المطور:", type="password")
            dev_btn = st.form_submit_button("دخول")
            
            if dev_btn:
                if dev_code.strip() == "900800":
                    login_user("dev_admin", "مطور")
                    st.rerun()
                else:
                    st.error("كود خطأ!")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    t_phone = st.session_state.user_phone if st.session_state.user_role == "أستاذ" else None
    room_id = f"room_{t_phone}" if t_phone else None

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

    if st.session_state.user_role == "طالب":
        if st.button("🚪 تسجيل الخروج"):
            logout_user()
            st.rerun()

        if st.session_state.sub_target_teacher is None:
            st.subheader("👨‍🏫 أساتذة المنصة المتاحين")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject, price, room_id, phone FROM teachers WHERE is_blocked=0")
                    teachers = c.fetchall()
                
                if teachers:
                    for t_name, t_sub, t_price, r_id, t_ph in teachers:
                        st.markdown('<div class="app-card">', unsafe_allow_html=True)
                        col_info, col_btn = st.columns([3, 1])
                        col_info.markdown(f"### 👨‍🏫 {t_name}")
                        col_info.markdown(f"📖 **المادة:** {t_sub}")
                        
                        # التحقق من حالة اشتراك الطالب مع هذا الأستاذ لمعرفة ماذا يظهر على الكارت
                        sub_check_status = None
                        try:
                            with sqlite3.connect(DB_NAME) as conn_sub:
                                cs = conn_sub.cursor()
                                cs.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                                          (st.session_state.user_phone, t_ph))
                                s_row = cs.fetchone()
                                if s_row:
                                    sub_check_status = s_row[0]
                        except:
                            pass

                        if sub_check_status == 'active':
                            if col_btn.button("دخول لقاعة الأستاذ 🎬", key=f"btn_enter_room_{t_ph}"):
                                st.session_state.sub_target_teacher = {
                                    "phone": t_ph,
                                    "name": t_name,
                                    "subject": t_sub,
                                    "price": t_price,
                                    "room_id": r_id
                                }
                                st.session_state.inside_teacher_room = True
                                st.rerun()
                        elif sub_check_status == 'pending':
                            col_btn.markdown("<span style='color:orange; font-weight:bold;'>قيد المراجعة ⏳</span>", unsafe_allow_html=True)
                        else:
                            if col_btn.button("اشتراك ⚡", key=f"btn_go_sub_{t_ph}"):
                                st.session_state.sub_target_teacher = {
                                    "phone": t_ph,
                                    "name": t_name,
                                    "subject": t_sub,
                                    "price": t_price,
                                    "room_id": r_id
                                }
                                st.session_state.inside_teacher_room = False
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("لا يوجد أساتذة متاحين حالياً.")
            except:
                pass
        else:
            target_t = st.session_state.sub_target_teacher
            t_phone_val = target_t["phone"]
            t_name_val = target_t["name"]
            t_price_val = target_t["price"]
            r_id_val = target_t["room_id"]
            
            if st.button("⬅️ العودة لقائمة الأساتذة"):
                st.session_state.sub_target_teacher = None
                st.session_state.inside_teacher_room = False
                st.rerun()
                
            st.markdown(f"## 👨‍🏫 الأستاذ: {t_name_val} ({target_t['subject']})")
            
            sub_info = None
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT status, expires_at FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                              (st.session_state.user_phone, t_phone_val))
                    sub_info = c.fetchone()
            except:
                pass

            sub_status = sub_info[0] if sub_info else None
            expires_at = sub_info[1] if sub_info and len(sub_info) > 1 else None

            is_expired = False
            if expires_at and sub_status == 'active':
                try:
                    exp_dt = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                    if datetime.datetime.now() > exp_dt:
                        is_expired = True
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st.session_state.user_phone, t_phone_val))
                            conn.commit()
                        sub_status = None
                except:
                    pass

            if sub_status == 'active' and not is_expired:
                # إذا كان الطالب لم يضغط بعد على زر الدخول للقاعة، نعرض له زر الدخول المميز ونخفي زر الاشتراك القديم
                if not st.session_state.inside_teacher_room:
                    st.markdown("""
                    <div class="success-alert">
                        🎉 مبروك! تم قبول اشتراكك بنجاح من الأستاذ.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("دخول لقاعة الأستاذ وعرض الفيديوهات والبث 🎬"):
                        st.session_state.inside_teacher_room = True
                        st.rerun()
                else:
                    # عند الضغط على زر الدخول، تفتح له محتويات القاعة والتبويبات
                    if st.button("❌ إلغاء الاشتراك والخروج من القاعة"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st.session_state.user_phone, t_phone_val))
                            conn.commit()
                        st.session_state.inside_teacher_room = False
                        st.rerun()

                    tab_live, tab_media, tab_exams, tab_chat = st.tabs(["🔴 البث المباشر والشات", "🎬 الفيديوهات", "📝 الامتحانات", "💬 الشات الخاص"])
                    with tab_live:
                        stream_html = f"""
                        <iframe src="https://vdo.ninja/?view={r_id_val}&autostart=1" 
                                style="width: 100%; height: 300px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                                allow="camera; microphone; autoplay" allowfullscreen>
                        </iframe>
                        """
                        components.html(stream_html, height=320)
                        
                    with tab_media:
                        display_student_media(t_phone_val, st.session_state.user_phone)
                        
                    with tab_exams:
                        render_student_exams(t_phone_val)
                        
                    with tab_chat:
                        render_smart_chat(t_phone_val, st.session_state.user_phone, "طالب")
                    
            elif sub_status == 'pending':
                st.markdown("""
                <div class="success-alert">
                    🎉 ✅ تم إرسال طلب الاشتراك بنجاح ووصل للأستاذ! في انتظار المراجعة والتفعيل.
                </div>
                """, unsafe_allow_html=True)
                if st.button("إلغاء الطلب المعلق"):
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st.session_state.user_phone, t_phone_val))
                        conn.commit()
                    st.rerun()
            else:
                fixed_orange_number = "01213783090"
                
                st.markdown(f"""
                <div class="cash-box">
                    مطلوب تحويل مبلغ ({t_price_val} جـ) على رقم أورانج كاش الآتي: <br>
                    <span style="font-size: 20px; color: #4f46e5;">{fixed_orange_number}</span><br>
                    ثم اكتب رقم أورانج كاش الذي حوّلت منه في الخانة أدناه واضغط إرسال طلب الاشتراك:
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"orange_pay_form_{t_phone_val}"):
                    orange_sender_input = st.text_input("اكتب رقم أورانج كاش الذي حوّلت منه:")
                    pay_btn = st.form_submit_button("إرسال طلب الاشتراك للأستاذ ⚡")
                    
                    if pay_btn:
                        if orange_sender_input:
                            t_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            try:
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("""INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status, orange_cash_sender, requested_at) 
                                               VALUES (?, ?, 'pending', ?, ?)""",
                                              (st.session_state.user_phone, t_phone_val, orange_sender_input, t_now_str))
                                    conn.commit()
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطأ في إرسال الطلب: {e}")
                        else:
                            st.error("الرجاء إدخال رقم أورانج كاش المحول منه!")

    elif st.session_state.user_role == "أستاذ":
        if st.button("🚪 تسجيل الخروج"):
            logout_user()
            st.rerun()

        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, room_id FROM teachers WHERE phone=?", (t_phone,))
                t_row = c.fetchone()
                t_name = t_row[0] if t_row else "أستاذ"
                room_id = t_row[1] if t_row else f"room_{t_phone}"
        except:
            t_name = "أستاذ"
            room_id = f"room_{t_phone}"

        st.subheader(f"لوحة تحكم الأستاذ: {t_name}")
        
        tab_broadcast, tab_subs, tab_upload, tab_manage_posts, tab_exams_manage, tab_smart_chat = st.tabs([
            "🔴 البث", "👥 الطلبات", "📤 رفع فيديو", "🎬 الفيديوهات", "📝 إنشاء الامتحانات", "💬 الشات"
        ])

        with tab_broadcast:
            st.markdown("### إدارة البث المباشر والشات العام")
            stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&autostart=1" 
                    style="width: 100%; height: 320px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(stream_html, height=340)
            
            st_autorefresh(interval=2000, key=f"chat_refresh_{room_id}")
            st.markdown("💬 **شات البث المباشر العام:**")
            with st.form(f"chat_form_{room_id}", clear_on_submit=True):
                msg = st.text_input("اكتب رسالة في الشات العام...")
                send_btn = st.form_submit_button("إرسال")
                if send_btn and msg:
                    t_now = datetime.datetime.now().strftime("%H:%M:%S")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO live_chat (room_id, sender_phone, sender_name, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                                      (room_id, t_phone, t_name, msg, t_now))
                            conn.commit()
                        st.rerun()
                    except:
                        pass
            
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, sender_phone, sender_name, message, timestamp FROM live_chat WHERE room_id=? ORDER BY id DESC LIMIT 10", (room_id,))
                    messages = c.fetchall()
                if messages:
                    for m_id, s_phone, s_name, s_msg, s_time in reversed(messages):
                        st.markdown(f"<div style='background: #1e293b; color: #fff; padding: 6px 10px; border-radius: 8px; margin-bottom: 4px;'><small style='color: #94a3b8;'>[{s_time}]</small> <b>{s_name}:</b> {s_msg}</div>", unsafe_allow_html=True)
            except:
                pass

        with tab_subs:
            st.markdown("### 📥 طلبات الاشتراك الواردة من الطلاب")
            display_teacher_requests(t_phone)

        with tab_upload:
            with st.form("upload_form", clear_on_submit=True):
                p_title = st.text_input("عنوان الفيديو أو المحتوى:")
                p_type = st.selectbox("النوع:", ["video", "image"])
                uploaded_file = st.file_uploader("اختر الملف:", type=["mp4", "mov", "avi", "mkv", "png", "jpg", "jpeg"])
                up_btn = st.form_submit_button("رفع ونشر الفوري")

                if up_btn:
                    if p_title and uploaded_file is not None:
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        unique_filename = f"{t_phone}_{int(datetime.datetime.now().timestamp())}{file_extension}"
                        file_path = os.path.join(MEDIA_DIR, unique_filename)
                        
                        try:
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, status) VALUES (?, ?, ?, ?, 'approved')",
                                          (t_phone, p_title, p_type, file_path))
                                conn.commit()
                            st.success("✅ تم إنشاء ونشر الفيديو بنجاح وأصبح متاحاً للطلاب المشتركين!")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء حفظ الملف: {e}")
                    else:
                        st.error("الرجاء كتابة عنوان الفيديو وإرفاق الملف بشكل صحيح.")

        with tab_manage_posts:
            st.subheader("🎬 قائمة فيديوهاتك المنشورة وإدارتها")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, title, media_type, file_path, views_count FROM posts WHERE teacher_phone=?", (t_phone,))
                    my_posts = c.fetchall()
                
                if my_posts:
                    for mp_id, mp_title, mp_type, mp_path, mp_views in my_posts:
                        display_mp_views = max(25, mp_views + 25)
                        st.markdown(f"📌 **{mp_title}** | المشاهدات: {display_mp_views}")
                        if mp_path and os.path.exists(mp_path):
                            if mp_type == "image":
                                st.image(mp_path, width=200)
                            else:
                                st.video(mp_path)
                        else:
                            st.warning("⚠️ الملف غير موجود في المسار المحلي.")
                        
                        if st.button(f"🗑️ حذف الفيديو", key=f"teacher_del_post_{mp_id}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM posts WHERE id=?", (mp_id,))
                                conn.commit()
                            st.success("تم حذف الفيديو بنجاح!")
                            st.rerun()
                        st.write("---")
                else:
                    st.info("لم تقم برفع أي فيديوهات بعد.")
            except:
                pass

        with tab_exams_manage:
            st.subheader("📝 إنشاء وإضافة أسئلة الامتحان لطلابك")
            with st.form("create_exam_form", clear_on_submit=True):
                q_text = st.text_area("نص السؤال:")
                o1 = st.text_input("الاختيار الأول:")
                o2 = st.text_input("الاختيار الثاني:")
                o3 = st.text_input("الاختيار الثالث:")
                o4 = st.text_input("الاختيار الرابع:")
                correct_opt = st.text_input("الإجابة الصحيحة بالضبط (اكتبها كما كتبتها في الاختيارات أعلاه):")
                add_exam_btn = st.form_submit_button("نشر السؤال لطلابك")

                if add_exam_btn:
                    if q_text and o1 and o2 and correct_opt:
                        t_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO exams (teacher_phone, question, opt1, opt2, opt3, opt4, correct_answer, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                          (t_phone, q_text, o1, o2, o3, o4, correct_opt, t_now_str))
                                conn.commit()
                            st.success("تم إضافة السؤال بنجاح وظهر لطلابك المشتركين!")
                            st.rerun()
                        except:
                            pass
                    else:
                        st.error("الرجاء إدخال السؤال واختيارين على الأقل وتحديد الإجابة الصحيحة.")

            st.write("---")
            st.subheader("📋 الأسئلة التي أنشأتها مسبقاً:")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, question, correct_answer FROM exams WHERE teacher_phone=?", (t_phone,))
                    t_exams = c.fetchall()
                
                if t_exams:
                    for te_id, te_q, te_c in t_exams:
                        st.markdown(f"❓ **السؤال:** {te_q} <br>✅ **الإجابة الصحيحة:** `{te_c}`", unsafe_allow_html=True)
                        if st.button(f"🗑️ حذف السؤال", key=f"del_exam_{te_id}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM exams WHERE id=?", (te_id,))
                                conn.commit()
                            st.success("تم الحذف!")
                            st.rerun()
                        st.write("---")
                else:
                    st.info("لا توجد أسئلة مضافة بعد.")
            except:
                pass

        with tab_smart_chat:
            st.subheader("💬 الشات الذكي الخاص مع الطلاب")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT DISTINCT student_phone FROM subscriptions WHERE teacher_phone=? AND status='active'", (t_phone,))
                    active_subs_students = c.fetchall()
                
                if active_subs_students:
                    student_phones_list = [s[0] for s in active_subs_students]
                    selected_st_phone = st.selectbox("اختر الطالب لبدء أو متابعة المحادثة معه:", student_phones_list)
                    
                    if selected_st_phone:
                        render_smart_chat(t_phone, selected_st_phone, "أستاذ")
                else:
                    st.info("لا توجد طلاب مشتركين حالياً لبدء الشات معهم.")
            except:
                pass

    elif st.session_state.user_role == "مطور":
        if st.button("🚪 تسجيل الخروج"):
            logout_user()
            st.rerun()

        st.subheader("لوحة تحكم المطور الخارقة 👑")
        
        dev_section = st.selectbox("اختر قسم التحكم:", [
            "👑 إدارة وتعديل الأساتذة بالكامل",
            "🎓 إدارة وتعديل الطلاب بالكامل",
            "🎬 إدارة المحتوى ومنشورات الأساتذة وحذفها",
            "🛡️ إدارة الحظر والفك", 
            "👨‍🏫 أرقام الأساتذة المسموح لهم بالتسجيل",
            "📢 قسم الشكاوى والبلاغات", 
            "📊 الإحصائيات وإدارة الشات"
        ])
        
        st.write("---")

        if dev_section == "👑 إدارة وتعديل الأساتذة بالكامل":
            st.subheader("👨‍🏫 قائمة الأساتذة (تعديل البيانات أو الحذف)")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, phone, name, subject, price FROM teachers")
                    all_teachers = c.fetchall()
                
                if all_teachers:
                    for t_id, t_ph, t_n, t_s, t_p in all_teachers:
                        with st.expander(f"👨‍🏫 {t_n} ({t_s}) - هاتف: {t_ph}"):
                            with st.form(f"edit_teacher_{t_id}"):
                                new_name = st.text_input("اسم الأستاذ:", value=t_n)
                                new_sub = st.text_input("المادة:", value=t_s)
                                new_price = st.number_input("سعر الاشتراك (جـ):", value=float(t_p))
                                update_t_btn = st.form_submit_button("حفظ التعديلات")
                                
                                if update_t_btn:
                                    with sqlite3.connect(DB_NAME) as conn:
                                        c = conn.cursor()
                                        c.execute("UPDATE teachers SET name=?, subject=?, price=? WHERE id=?", (new_name, new_sub, new_price, t_id))
                                        c.execute("UPDATE users SET name=? WHERE phone=?", (new_name, t_ph))
                                        conn.commit()
                                    st.success("تم تحديث بيانات الأستاذ بنجاح!")
                                    st.rerun()
                            
                            if st.button(f"🗑️ حذف الأستاذ نهائياً", key=f"del_teacher_{t_id}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("DELETE FROM teachers WHERE id=?", (t_id,))
                                    c.execute("DELETE FROM users WHERE phone=?", (t_ph,))
                                    conn.commit()
                                st.success("تم حذف الأستاذ بنجاح!")
                                st.rerun()
                else:
                    st.info("لا يوجد أساتذة مسجلين.")
            except:
                pass

        elif dev_section == "🎓 إدارة وتعديل الطلاب بالكامل":
            st.subheader("🎓 قائمة الطلاب (تعديل البيانات أو الحذف)")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, phone, name, grade FROM users WHERE role='طالب'")
                    all_students = c.fetchall()
                
                if all_students:
                    for st_id, st_ph, st_n, st_g in all_students:
                        with st.expander(f"🎓 {st_n or 'طالب'} - هاتف: {st_ph}"):
                            with st.form(f"edit_student_{st_id}"):
                                new_st_name = st.text_input("اسم الطالب:", value=st_n or "")
                                new_st_grade = st.text_input("المرحلة الدراسية:", value=st_g or "")
                                update_st_btn = st.form_submit_button("حفظ تعديلات الطالب")
                                
                                if update_st_btn:
                                    with sqlite3.connect(DB_NAME) as conn:
                                        c = conn.cursor()
                                        c.execute("UPDATE users SET name=?, grade=? WHERE id=?", (new_st_name, new_st_grade, st_id))
                                        conn.commit()
                                    st.success("تم تحديث بيانات الطالب!")
                                    st.rerun()
                            
                            if st.button(f"🗑️ حذف الطالب نهائياً", key=f"del_student_{st_id}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("DELETE FROM users WHERE id=?", (st_id,))
                                    conn.commit()
                                st.success("تم حذف الطالب بنجاح!")
                                st.rerun()
                else:
                    st.info("لا يوجد طلاب مسجلين.")
            except:
                pass

        elif dev_section == "🎬 إدارة المحتوى ومنشورات الأساتذة وحذفها":
            st.subheader("🎬 جميع فيديوهات ومنشورات الأساتذة في المنصة")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, teacher_phone, title, media_type, file_path, views_count FROM posts")
                    all_posts = c.fetchall()
                
                if all_posts:
                    for p_id, p_tph, p_title, p_type, p_path, p_views in all_posts:
                        display_p_views = max(25, p_views + 25)
                        st.markdown(f"📌 **{p_title}** | هاتف الأستاذ: `{p_tph}` | المشاهدات: {display_p_views}")
                        if p_path and os.path.exists(p_path):
                            if p_type == "image":
                                st.image(p_path, width=200)
                            else:
                                st.video(p_path)
                        if st.button(f"🗑️ حذف هذا المنشور/الفيديو نهائياً", key=f"dev_del_post_{p_id}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM posts WHERE id=?", (p_id,))
                                conn.commit()
                            st.success("تم حذف المنشور بنجاح!")
                            st.rerun()
                        st.write("---")
                else:
                    st.info("لا توجد منشورات مرفوعة حالياً.")
            except:
                pass

        elif dev_section == "🛡️ إدارة الحظر والفك":
            st.subheader("👥 الحظر السريع للأساتذة والمستخدمين")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT phone, name, role FROM users WHERE is_blocked=0")
                    active_users = c.fetchall()
                    
                    c.execute("SELECT phone, name, subject FROM teachers WHERE is_blocked=0")
                    active_teachers = c.fetchall()
                
                if active_users:
                    for u_ph, u_name, u_role in active_users:
                        col_u1, col_u2 = st.columns([3, 1])
                        with col_u1:
                            st.markdown(f"👤 **{u_name}** | هاتف: `{u_ph}` | النوع: {u_role}")
                        with col_u2:
                            if st.button(f"حظر 🚫", key=f"ban_u_{u_ph}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET is_blocked=1 WHERE phone=?", (u_ph,))
                                    c.execute("UPDATE teachers SET is_blocked=1 WHERE phone=?", (u_ph,))
                                    conn.commit()
                                st.success("تم الحظر!")
                                st.rerun()

                if active_teachers:
                    for t_ph, t_name, t_sub in active_teachers:
                        col_t1, col_t2 = st.columns([3, 1])
                        with col_t1:
                            st.markdown(f"👨‍🏫 **{t_name}** | مادة: {t_sub} | هاتف: `{t_ph}`")
                        with col_t2:
                            if st.button(f"حظر 🚫", key=f"ban_t_{t_ph}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE teachers SET is_blocked=1 WHERE phone=?", (t_ph,))
                                    c.execute("UPDATE users SET is_blocked=1 WHERE phone=?", (t_ph,))
                                    conn.commit()
                                st.success("تم الحظر!")
                                st.rerun()
            except:
                pass

            st.write("---")
            with st.form("admin_unban_form"):
                unban_phone_input = st.text_input("فك الحظر عن رقم هاتف:")
                unban_btn = st.form_submit_button("فك الحظر")
                if unban_btn and unban_phone_input:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE users SET is_blocked=0 WHERE phone=?", (unban_phone_input,))
                            c.execute("UPDATE teachers SET is_blocked=0 WHERE phone=?", (unban_phone_input,))
                            conn.commit()
                        st.success(f"تم فك الحظر عن {unban_phone_input}")
                    except:
                        pass

        elif dev_section == "👨‍🏫 أرقام الأساتذة المسموح لهم بالتسجيل":
            st.subheader("➕ إضافة رقم أستاذ مصرح له")
            with st.form("add_allowed_teacher_form"):
                new_t_phone = st.text_input("أدخل رقم محمول الأستاذ:")
                add_t_btn = st.form_submit_button("إضافة للقائمة")
                if add_t_btn and new_t_phone:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO allowed_teachers (phone) VALUES (?)", (new_t_phone,))
                            conn.commit()
                        st.success("تمت الإضافة بنجاح!")
                    except:
                        st.error("الرقم موجود مسبقاً.")

            st.write("---")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, phone FROM allowed_teachers")
                    allowed_list = c.fetchall()
                
                if allowed_list:
                    for a_id, a_ph in allowed_list:
                        col_a1, col_a2 = st.columns([3, 1])
                        with col_a1:
                            st.markdown(f"📞 `{a_ph}`")
                        with col_a2:
                            if st.button("حذف", key=f"del_allowed_{a_id}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("DELETE FROM allowed_teachers WHERE id=?", (a_id,))
                                    conn.commit()
                                st.rerun()
            except:
                pass

        elif dev_section == "📢 قسم الشكاوى والبلاغات":
            st.subheader("🚨 الشكاوى الواردة")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, sender_phone, sender_name, role, complaint_text, timestamp FROM complaints ORDER BY id DESC")
                    comps = c.fetchall()
                
                if comps:
                    for c_id, c_ph, c_name, c_role, c_text, c_time in comps:
                        st.markdown(f"""
                        <div class='app-card'>
                            <b>👤 الاسم:</b> {c_name} ({c_role})<br>
                            <b>📞 الهاتف:</b> {c_ph}<br>
                            <b>📝 الشكوى:</b> {c_text}
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"حذف الشكوى #{c_id}", key=f"del_comp_{c_id}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM complaints WHERE id=?", (c_id,))
                                conn.commit()
                            st.rerun()
                else:
                    st.info("لا توجد شكاوى.")
            except:
                pass

        elif dev_section == "📊 الإحصائيات وإدارة الشات":
            if st.button("🗑️ تفريغ جميع رسائل شات البث بالكامل"):
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM live_chat")
                        conn.commit()
                    st.success("تم مسح الشات بنجاح!")
                    st.rerun()
                except:
                    pass

            st.write("---")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM users")
                    u_cnt = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM teachers")
                    t_cnt = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM posts")
                    p_cnt = c.fetchone()[0]
                st.metric("إجمالي المستخدمين والطلاب", u_cnt)
                st.metric("إجمالي الأساتذة", t_cnt)
                st.metric("إجمالي الفيديوهات والمنشورات", p_cnt)
            except:
                pass
