import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components
import hashlib
import random
import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التطبيق وتصميم الواجهة النظيفة
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
        padding-top: 1.5rem !important;
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
        background: #ecfdf5 !important;
        color: #065f46 !important;
        padding: 14px !important;
        border-radius: 12px !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 15px !important;
        margin: 12px 0 !important;
        border: 1px solid #10b981 !important;
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
            
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, teacher_phone TEXT,
            status TEXT DEFAULT 'pending', requested_at TEXT, expires_at TEXT, UNIQUE(student_phone, teacher_phone))''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, title TEXT,
            media_type TEXT, file_path TEXT, status TEXT DEFAULT 'approved', views_count INTEGER DEFAULT 0)''')

        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, student_name TEXT, comment_text TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS live_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT, sender_name TEXT, message TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT)''')
            
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
    st.query_params.clear()

# ==========================================
# 4. الشات التفاعلي للبث المباشر
# ==========================================
@st.fragment
def render_live_chat(room_id, user_name):
    st_autorefresh(interval=2000, key=f"chat_refresh_{room_id}")
    st.markdown("💬 **شات البث المباشر:**")
    
    with st.form(f"chat_form_{room_id}", clear_on_submit=True):
        msg = st.text_input("اكتب رسالة في الشات...")
        send_btn = st.form_submit_button("إرسال")
        if send_btn and msg:
            t_now = datetime.datetime.now().strftime("%H:%M:%S")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO live_chat (room_id, sender_name, message, timestamp) VALUES (?, ?, ?, ?)",
                              (room_id, user_name, msg, t_now))
                    conn.commit()
                st.rerun()
            except:
                pass

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT sender_name, message, timestamp FROM live_chat WHERE room_id=? ORDER BY id DESC LIMIT 15", (room_id,))
            messages = c.fetchall()
            
        if messages:
            chat_box_html = "<div style='background: #1e293b; color: #fff; padding: 12px; border-radius: 12px; height: 200px; overflow-y: auto; direction: rtl;'>"
            for s_name, s_msg, s_time in reversed(messages):
                chat_box_html += f"<div style='margin-bottom: 6px;'><small style='color: #94a3b8;'>[{s_time}]</small> <b>{s_name}:</b> {s_msg}</div>"
            chat_box_html += "</div>"
            st.markdown(chat_box_html, unsafe_allow_html=True)
        else:
            st.info("لا توجد رسائل حالياً في البث.")
    except:
        pass

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
                st.markdown(f"📌 **{p_title}** | 👁️ المشاهدات: **{views}**")
                
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("UPDATE posts SET views_count = views_count + 1 WHERE id=?", (p_id,))
                    conn.commit()

                if os.path.exists(p_path):
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
            st.info("لا توجد منشورات متاحة حالياً.")
    except:
        pass

@st.fragment
def display_teacher_requests(teacher_phone):
    st_autorefresh(interval=2000, key=f"refresh_subs_{teacher_phone}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT student_phone, status, requested_at, expires_at FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
            subs = c.fetchall()
            
            if subs:
                now = datetime.datetime.now()
                for s_ph, status, req_at, expires_at in subs:
                    c.execute("SELECT name, age, grade FROM users WHERE phone=?", (s_ph,))
                    st_data = c.fetchone()
                    st_display_name = st_data[0] if st_data else s_ph

                    st.markdown(f"🎓 **{st_display_name}** | هاتف المحفظة: `{s_ph}` | الحالة: **{status}**")
                    
                    col_act1, col_act2 = st.columns(2)
                    if status != 'active':
                        if col_act1.button(f"✅ قبول", key=f"acc_{s_ph}"):
                            exp_time = (now + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE subscriptions SET status='active', expires_at=? WHERE student_phone=? AND teacher_phone=?", (exp_time, s_ph, teacher_phone))
                            conn.commit()
                            st.rerun()
                    if col_act2.button(f"❌ حذف", key=f"ref_{s_ph}"):
                        c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                        conn.commit()
                        st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد طلبات اشتراك حالياً.")
    except:
        pass

@st.fragment
def render_student_teacher_card(t_name, t_sub, t_price, room_id, t_phone, student_phone):
    st_autorefresh(interval=2000, key=f"student_card_refresh_{t_phone}")
    
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown(f"### 👨‍🏫 الأستاذ: {t_name}")
    st.markdown(f"📖 **المادة:** {t_sub} | 💰 **السعر:** {t_price} جـ")
    
    sub_info = None
    st_current_name = "طالب"
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT status, expires_at FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                      (student_phone, t_phone))
            sub_info = c.fetchone()
            
            c.execute("SELECT name FROM users WHERE phone=?", (student_phone,))
            st_u_row = c.fetchone()
            if st_u_row:
                st_current_name = st_u_row[0]
    except:
        pass

    sub_status = sub_info[0] if sub_info else None
    expires_at = sub_info[1] if sub_info else None

    is_expired = False
    if expires_at and sub_status == 'active':
        try:
            exp_dt = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > exp_dt:
                is_expired = True
        except:
            pass

    if sub_status == 'active' and not is_expired:
        st.success("✅ مشترك مع الأستاذ (البث والمحتوى متاحان)")
        
        if st.button("❌ إلغاء الاشتراك", key=f"cancel_sub_{t_phone}"):
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (student_phone, t_phone))
                conn.commit()
            st.rerun()

        tab_live, tab_media = st.tabs(["🔴 البث المباشر والشات", "🎬 الفيديوهات"])
        with tab_live:
            stream_html = f"""
            <iframe src="https://vdo.ninja/?view={room_id}&autostart=1" 
                    style="width: 100%; height: 300px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(stream_html, height=320)
            render_live_chat(room_id, st_current_name)
            
        with tab_media:
            display_student_media(t_phone, student_phone)
            
    else:
        st.info("⚠️ غير مشترك. قم بتحويل المصاريف وأدخل رقم المحمول أدناه:")
        st.markdown(f"""
        <div class="cash-box">
            تحويل ({t_price} جـ) على محفظة: <b>01213783090</b>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form(f"cash_pay_form_{t_phone}"):
            cash_phone_used = st.text_input("رقم المحمول المحول منه:", value=student_phone)
            pay_btn = st.form_submit_button("إرسال طلب الانضمام")
            
            if pay_btn:
                if cash_phone_used:
                    t_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (cash_phone_used, t_phone))
                            c.execute("INSERT INTO subscriptions (student_phone, teacher_phone, status, requested_at) VALUES (?, ?, 'pending', ?)",
                                      (cash_phone_used, t_phone, t_now_str))
                            conn.commit()
                        st.success("تم إرسال الطلب بنجاح!")
                        st.rerun()
                    except:
                        pass
                else:
                    st.error("أدخل رقم المحمول!")
                    
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. الواجهة الرئيسية
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
                                st.error("الحساب محظور!")
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
                t_secret_code = st.text_input("الكود السري:", type="password")
                t_signup_btn = st.form_submit_button("إنشاء")
                
                if t_signup_btn:
                    if t_secret_code.strip() == "901000" and t_phone_reg:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
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
                        st.error("الكود السري غير صحيح أو بيانات ناقصة!")
                        
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
                                st.error("الحساب محظور!")
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
        if st.button("🚪 تسجيل الخروج"):
            logout_user()
            st.rerun()

        st.subheader("👨‍🏫 الأساتذة المتاحين")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, subject, price, room_id, phone FROM teachers WHERE is_blocked=0")
                teachers = c.fetchall()
            
            if teachers:
                for t_name, t_sub, t_price, r_id, t_ph in teachers:
                    render_student_teacher_card(t_name, t_sub, t_price, r_id, t_ph, st.session_state.user_phone)
            else:
                st.info("لا يوجد أساتذة حالياً.")
        except:
            pass

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
        
        tab_broadcast, tab_subs, tab_upload = st.tabs(["🔴 البث المباشر والشات", "👥 طلبات الطلاب", "📤 رفع فيديو"])

        with tab_broadcast:
            st.markdown("### إدارة البث المباشر")
            stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&autostart=1" 
                    style="width: 100%; height: 320px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(stream_html, height=340)
            
            render_live_chat(room_id, t_name)

        with tab_subs:
            display_teacher_requests(t_phone)

        with tab_upload:
            with st.form("upload_form", clear_on_submit=True):
                p_title = st.text_input("عنوان الفيديو:")
                p_type = st.selectbox("النوع:", ["video", "image"])
                uploaded_file = st.file_uploader("اختر الملف:", type=["mp4", "mov", "png", "jpg"])
                up_btn = st.form_submit_button("رفع ونشر")

                if up_btn:
                    if p_title and uploaded_file:
                        file_path = os.path.join(MEDIA_DIR, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, status) VALUES (?, ?, ?, ?, 'approved')",
                                          (t_phone, p_title, p_type, file_path))
                                conn.commit()
                            st.success("تم الرفع بنجاح!")
                            st.rerun()
                        except:
                            pass

    elif st.session_state.user_role == "مطور":
        if st.button("🚪 تسجيل الخروج"):
            logout_user()
            st.rerun()

        st.subheader("لوحة تحكم المطور 👑")
        
        if st.button("🗑️ مسح وتفريغ جميع رسائل شات البث المباشر بالكامل"):
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM live_chat")
                    conn.commit()
                st.success("تم مسح شات البث بالكامل بنجاح!")
                st.rerun()
            except:
                st.error("حدث خطأ أثناء مسح الشات.")

        st.write("---")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM users")
                u_cnt = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM teachers")
                t_cnt = c.fetchone()[0]
            st.metric("عدد المستخدمين", u_cnt)
            st.metric("عدد الأساتذة", t_cnt)
        except:
            pass
