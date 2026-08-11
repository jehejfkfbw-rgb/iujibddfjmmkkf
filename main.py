import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components
import hashlib
import random
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
    
    .stTextInput input, .stNumberInput input, .stPasswordInput input {
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
# 2. إعداد قاعدة البيانات وتحديث الأعمدة تلقائياً
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
            grade_level TEXT, age INTEGER, price REAL, image_url TEXT, room_id TEXT)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, teacher_phone TEXT,
            status TEXT DEFAULT 'pending', expires_at TEXT, UNIQUE(student_phone, teacher_phone))''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, title TEXT,
            media_type TEXT, file_path TEXT, status TEXT DEFAULT 'approved')''')

        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
            phone TEXT PRIMARY KEY, code TEXT)''')
        
        user_columns = [col[1] for col in c.execute("PRAGMA table_info(users)").fetchall()]
        if "age" not in user_columns:
            c.execute("ALTER TABLE users ADD COLUMN age TEXT DEFAULT ''")
        if "grade" not in user_columns:
            c.execute("ALTER TABLE users ADD COLUMN grade TEXT DEFAULT ''")
        if "email" not in user_columns:
            c.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''")
        if "is_blocked" not in user_columns:
            c.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")

        teacher_columns = [col[1] for col in c.execute("PRAGMA table_info(teachers)").fetchall()]
        if "password" not in teacher_columns:
            c.execute("ALTER TABLE teachers ADD COLUMN password TEXT DEFAULT ''")
        if "grade_level" not in teacher_columns:
            c.execute("ALTER TABLE teachers ADD COLUMN grade_level TEXT DEFAULT 'جميع المراحل'")
        if "age" not in teacher_columns:
            c.execute("ALTER TABLE teachers ADD COLUMN age INTEGER DEFAULT 30")
        if "price" not in teacher_columns:
            c.execute("ALTER TABLE teachers ADD COLUMN price REAL DEFAULT 100.0")
        if "image_url" not in teacher_columns:
            c.execute("ALTER TABLE teachers ADD COLUMN image_url TEXT DEFAULT ''")
        if "room_id" not in teacher_columns:
            c.execute("ALTER TABLE teachers ADD COLUMN room_id TEXT DEFAULT ''")

        sub_columns = [col[1] for col in c.execute("PRAGMA table_info(subscriptions)").fetchall()]
        if "expires_at" not in sub_columns:
            c.execute("ALTER TABLE subscriptions ADD COLUMN expires_at TEXT DEFAULT ''")

        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('teacher_secret', '901000')")
        conn.commit()

init_db()

def get_setting(key, default=""):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = c.fetchone()
            return row[0] if row else default
    except:
        return default

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 3. إدارة الجلسات عبر الـ Query Params (تثبيت الدخول)
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
# 4. التحديثات التلقائية الفورية (كل ثانية لتحديث حالة الاشتراك فوراً)
# ==========================================
@st.fragment
def display_student_media(teacher_phone):
    st_autorefresh(interval=2000, key=f"refresh_media_{teacher_phone}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT title, media_type, file_path FROM posts WHERE teacher_phone=? AND status='approved' ORDER BY id DESC", (teacher_phone,))
            posts = c.fetchall()
        
        if posts:
            for p_title, p_type, p_path in posts:
                st.markdown(f"📌 **{p_title}**")
                if os.path.exists(p_path):
                    if p_type == "image":
                        st.image(p_path)
                    elif p_type == "video":
                        st.video(p_path)
                st.write("---")
        else:
            st.info("لا توجد منشورات أو فيديوهات متاحة حالياً.")
    except:
        st.info("جارٍ تحميل المحتوى...")

@st.fragment
def display_teacher_requests(teacher_phone):
    st_autorefresh(interval=2000, key=f"refresh_subs_{teacher_phone}")
    import datetime
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT student_phone, status, expires_at FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
            subs = c.fetchall()
            
            if subs:
                for s_ph, status, expires_at in subs:
                    c.execute("SELECT name, age, grade FROM users WHERE phone=?", (s_ph,))
                    st_data = c.fetchone()
                    st_display_name = st_data[0] if st_data else s_ph
                    st_display_age = st_data[1] if st_data else "غير محدد"
                    st_display_grade = st_data[2] if st_data else "غير محدد"

                    st.markdown(f"🎓 **{st_display_name}** | السن: {st_display_age} | المرحلة: {st_display_grade}")
                    st.markdown(f"📱 الهاتف: `{s_ph}` | الحالة: **{status}**")
                    
                    if expires_at:
                        st.markdown(f"⏱️ تنتهي المهلة/الاشتراك في: `{expires_at}`")

                    col_a, col_b, col_c = st.columns(3)
                    if status == 'pending':
                        if col_a.button("✅ قبول", key=f"acc_{s_ph}"):
                            c.execute("UPDATE subscriptions SET status='active' WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                            st.rerun()
                    
                    if status == 'active':
                        if col_b.button("⏳ مهلة سريعة", key=f"timeout_{s_ph}"):
                            expire_time = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE subscriptions SET expires_at=? WHERE student_phone=? AND teacher_phone=?", (expire_time, s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم منح المهلة!")
                            st.rerun()

                    if col_c.button("❌ إلغاء الاشتراك", key=f"ref_{s_ph}"):
                        c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                        conn.commit()
                        st.warning("تم إلغاء اشتراك الطالب وإزالة الصلاحيات فوراً.")
                        st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد طلبات اشتراك حالياً.")
    except Exception as e:
        st.info(f"جارٍ تحديث الطلبات... ({e})")

# دالة مخصصة لتحديث كارد الأستاذ عند الطالب كل ثانية لفتح المنصة فور الموافقة
@st.fragment
def render_student_teacher_card(t_name, t_sub, t_price, room_id, t_phone, student_phone):
    st_autorefresh(interval=2000, key=f"student_card_refresh_{t_phone}")
    
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown(f"### 👨‍🏫 الأستاذ: {t_name}")
    st.markdown(f"📖 **المادة:** {t_sub} | 💰 **السعر:** {t_price} جـ")
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT status, expires_at FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                  (student_phone, t_phone))
        sub_info = c.fetchone()

    sub_status = sub_info[0] if sub_info else None
    expires_at = sub_info[1] if sub_info else None

    import datetime
    is_expired = False
    if expires_at:
        try:
            exp_dt = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > exp_dt:
                is_expired = True
        except:
            pass

    if sub_status == 'active' and not is_expired:
        st.success("✅ مشترك - تم قبول اشتراكك! يمكنك المشاهدة والبث المباشر الآن بكل سهولة")
        tab_live, tab_media = st.tabs(["🔴 البث المباشر", "🎬 الفيديوهات"])
        with tab_live:
            stream_html = f"""
            <iframe src="https://vdo.ninja/?view={room_id}&autostart=1" 
                    style="width: 100%; height: 350px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(stream_html, height=370)
        with tab_media:
            display_student_media(t_phone)
            
    elif sub_status == 'pending':
        st.warning("⏳ طلبك قيد المراجعة لدى الأستاذ... (سيتم فتح المنصة تلقائياً فور القبول في نفس اللحظة)")
    else:
        if sub_info is None:
            st.info("⚠️ تم إلغاء الاشتراك مع هذا المدرس أو لم تقم بالاشتراك بعد.")
        elif is_expired:
            st.error("⏳ انتهت مهلتك المؤقتة مع هذا الأستاذ، يرجى تجديد الاشتراك.")
            
        st.markdown(f"""
        <div class="cash-box">
            حول ({t_price} جـ) فودافون كاش على: <b>01213783090</b>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🚀 طلب الاشتراك", key=f"btn_{t_phone}"):
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status, expires_at) VALUES (?, ?, 'pending', '')",
                          (student_phone, t_phone))
                conn.commit()
            st.success("تم إرسال الطلب!")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. واجهة التطبيق الرئيسية
# ==========================================
st.markdown("<h2 style='text-align: center;'>⚡ منصة نوفا التعليمية</h2>", unsafe_allow_html=True)
st.write("---")

if not st.session_state.is_logged_in:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    role_choice = st.radio("حدد نوع الحساب:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑", "نسيت كلمة السر 🔑"], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("")

    if role_choice == "طالب 👨‍🎓":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        student_mode = st.radio("اختر العملية:", ["تسجيل دخول", "حساب جديد"], horizontal=True)
        st.write("---")
        
        if student_mode == "حساب جديد":
            with st.form("student_signup"):
                st.subheader("إنشاء حساب طالب جديد")
                s_name = st.text_input("الاسم الكامل:")
                s_email = st.text_input("البريد الإلكتروني:")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_phone = st.text_input("رقم المحمول:")
                s_age = st.text_input("السن:")
                s_grade = st.text_input("المرحلة الدراسية:")
                s_signup_btn = st.form_submit_button("تسجيل الحساب")
                
                if s_signup_btn:
                    if s_pass and s_phone:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=?", (s_phone,))
                                if c.fetchone():
                                    st.error("🚫 رقم المحمول مسجل مسبقاً في السيستم!")
                                else:
                                    hashed_pass = hash_password(s_pass)
                                    c.execute("INSERT INTO users (phone, email, password, name, age, grade, role, is_blocked) VALUES (?, ?, ?, ?, ?, ?, 'طالب', 0)", 
                                              (s_phone, s_email, hashed_pass, s_name if s_name else "طالب", s_age, s_grade))
                                    conn.commit()
                                    login_user(s_phone, "طالب")
                                    st.success("تم حفظ الطالب في السيستم وتسجيل الدخول بنجاح!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"🚫 حدث خطأ أثناء التسجيل: {e}")
                    else:
                        st.error("يرجى إدخال رقم المحمول وكلمة المرور على الأقل!")
        
        else:
            with st.form("student_login"):
                st.subheader("تسجيل دخول الطالب")
                s_phone_in = st.text_input("رقم المحمول:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                s_login_btn = st.form_submit_button("دخول")
                
                if s_login_btn:
                    if s_phone_in and s_pass_in:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                hashed_pass = hash_password(s_pass_in)
                                c.execute("SELECT phone, is_blocked FROM users WHERE phone=? AND password=? AND role='طالب'", (s_phone_in, hashed_pass))
                                user_row = c.fetchone()
                            
                            if user_row:
                                p_val, is_blocked = user_row
                                if is_blocked == 1:
                                    st.error("🚫 هذا الحساب محظور حالياً!")
                                else:
                                    login_user(p_val, "طالب")
                                    st.success("تم الدخول بنجاح!")
                                    st.rerun()
                            else:
                                st.error("🚫 رقم المحمول أو كلمة المرور غير صحيحة!")
                        except Exception as e:
                            st.error(f"🚫 حدث خطأ أثناء تسجيل الدخول: {e}")
                    else:
                        st.error("يرجى إدخال رقم المحمول وكلمة المرور!")
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "أستاذ 👨‍🏫":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        teacher_mode = st.radio("اختر العملية:", ["تسجيل دخول الأستاذ", "حساب جديد للأستاذ"], horizontal=True)
        st.write("---")
        
        if teacher_mode == "حساب جديد للأستاذ":
            with st.form("teacher_signup"):
                st.subheader("إنشاء حساب أستاذ جديد")
                t_name_reg = st.text_input("اسم الأستاذ:")
                t_phone_reg = st.text_input("رقم المحمول:")
                t_sub_reg = st.text_input("المادة الدراسية:")
                t_secret_code = st.text_input("الكود السري:", type="password")
                t_signup_btn = st.form_submit_button("إنشاء الحساب وحفظه في السيستم")
                
                if t_signup_btn:
                    correct_teacher_code = get_setting("teacher_secret", "901000")
                    if t_secret_code.strip() != correct_teacher_code:
                        st.error("🚫 الكود السري غير صحيح!")
                    elif t_phone_reg and t_name_reg:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM teachers WHERE phone=?", (t_phone_reg,))
                                if c.fetchone():
                                    st.error("🚫 رقم المحمول مسجل مسبقاً لأستاذ آخر في السيستم!")
                                else:
                                    hashed_t_pass = hash_password(t_secret_code)
                                    c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id) 
                                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                                              (t_phone_reg, hashed_t_pass, t_name_reg, t_sub_reg if t_sub_reg else "غير محدد", 'جميع المراحل', 30, 100.0, '', f"room_{t_phone_reg}"))
                                    c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (t_phone_reg, t_name_reg))
                                    conn.commit()
                                    login_user(t_phone_reg, "أستاذ")
                                    st.success("تم حفظ الأستاذ في السيستم وتسجيل الدخول بنجاح!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء حفظ البيانات: {e}")
                    else:
                        st.error("أدخل اسم الأستاذ ورقم المحمول والكود السري!")
        
        else:
            with st.form("teacher_login"):
                st.subheader("تسجيل دخول الأستاذ")
                t_phone_in = st.text_input("رقم المحمول:")
                t_secret_in = st.text_input("كلمة المرور أو الكود السري:", type="password")
                t_login_btn = st.form_submit_button("دخول الأستاذ")
                
                if t_login_btn:
                    correct_teacher_code = get_setting("teacher_secret", "901000")
                    if t_phone_in:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                hashed_t_pass = hash_password(t_secret_in)
                                c.execute("SELECT phone FROM teachers WHERE phone=? AND (password=? OR ?=?)", (t_phone_in, hashed_t_pass, t_secret_in, correct_teacher_code))
                                t_row = c.fetchone()
                            
                            if t_row:
                                login_user(t_phone_in, "أستاذ")
                                st.success("تم الدخول بنجاح!")
                                st.rerun()
                            else:
                                st.error("🚫 رقم المحمول أو كلمة المرور غير صحيحة!")
                        except Exception as e:
                            st.error(f"🚫 حدث خطأ أثناء تسجيل الدخول: {e}")
                    else:
                        st.error("يرجى إدخال رقم المحمول وكلمة المرور!")
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "مطور 👑":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        with st.form("dev_reg"):
            st.subheader("تسجيل دخول المطور الرئيسي")
            dev_code = st.text_input("كود المطور السري:", type="password")
            dev_btn = st.form_submit_button("دخول لوحة التحكم")
            
            if dev_btn:
                correct_dev_code = "900800"
                if dev_code.strip() == correct_dev_code:
                    login_user("dev_admin", "مطور")
                    st.success("أهلاً بك يا مطورنا!")
                    st.rerun()
                else:
                    st.error("🚫 كود المطور غير صحيح!")
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "نسيت كلمة السر 🔑":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        st.subheader("استعادة كلمة المرور عبر السيستم")
        
        reset_step = st.radio("الخطوة:", ["1. إرسال كود التأكيد", "2. تعيين كلمة سر جديدة"], horizontal=True)
        reset_phone = st.text_input("أدخل رقم المحمول المسجل:")
        
        if reset_step == "1. إرسال كود التأكيد":
            if st.button("إرسال الرمز"):
                if reset_phone:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT phone FROM users WHERE phone=?", (reset_phone,))
                        if c.fetchone():
                            gen_code = str(random.randint(1000, 9999))
                            c.execute("INSERT OR REPLACE INTO password_resets (phone, code) VALUES (?, ?)", (reset_phone, gen_code))
                            conn.commit()
                            st.info(f"تم حفظ كود التأكيد في السيستم بنجاح. الكود الخاص بك هو: **{gen_code}**")
                        else:
                            st.error("🚫 رقم المحمول غير مسجل في قاعدة البيانات!")
                else:
                    st.error("يرجى إدخال رقم المحمول أولاً.")
        else:
            code_input = st.text_input("أدخل كود التأكيد المولد:")
            new_password_input = st.text_input("كلمة السر الجديدة:", type="password")
            if st.button("تحديث كلمة السر"):
                if reset_phone and code_input and new_password_input:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT code FROM password_resets WHERE phone=?", (reset_phone,))
                        row_res = c.fetchone()
                        if row_res and row_res[0] == code_input:
                            hashed_new_pass = hash_password(new_password_input)
                            c.execute("UPDATE users SET password=? WHERE phone=?", (hashed_new_pass, reset_phone))
                            c.execute("DELETE FROM password_resets WHERE phone=?", (reset_phone,))
                            conn.commit()
                            st.success("✔️ تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول.")
                        else:
                            st.error("🚫 كود التأكيد غير صحيح!")
                else:
                    st.error("يرجى ملء جميع الحقول المطلوبة.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"مرحباً بك: **{st.session_state.user_role}**")
    if logout_col.button("🚪 خروج"):
        logout_user()
        st.rerun()

    # ------------------------------------------
    # واجهة الطالب
    # ------------------------------------------
    if st.session_state.user_role == "طالب":
        st.subheader("🎓 الأساتذة المتاحون في السيستم")
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id, phone FROM teachers")
            teachers = c.fetchall()

        if teachers:
            for t in teachers:
                t_name, t_sub, t_grade, t_age, t_price, t_img, room_id, t_phone = t
                # استدعاء الدالة المحدثة التي تتحدث تلقائياً كل ثانية لتجاوز الانتظار فوراً عند القبول
                render_student_teacher_card(t_name, t_sub, t_price, room_id, t_phone, st.session_state.user_phone)
        else:
            st.info("لا يوجد أساتذة مسجلون حالياً في السيستم.")

    # ------------------------------------------
    # واجهة الأستاذ
    # ------------------------------------------
    elif st.session_state.user_role == "أستاذ":
        st.subheader("👨‍🏫 استوديو الأستاذ")
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id FROM teachers WHERE phone=?", (st.session_state.user_phone,))
            t_info = c.fetchone()
        room_id = t_info[6] if t_info else f"room_{st.session_state.user_phone}"

        tab_stream, tab_post, tab_manage_posts, tab_subs, tab_prof = st.tabs(["🔴 البث المباشر", "📤 نشر محتوى", "🗑️ إدارة ومسح الفيديوهات", "👥 إدارة الطلاب", "⚙️ الإعدادات"])

        with tab_stream:
            st.info("شغل الكاميرا والبث المباشر من هاتفك أو جهازك مباشرة:")
            t_stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1" 
                    style="width: 100%; height: 380px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(t_stream_html, height=400)

        with tab_post:
            p_title = st.text_input("عنوان الفيديو أو المحتوى:")
            up_file = st.file_uploader("اختر فيديو أو صورة:", type=["png", "jpg", "jpeg", "mp4"])
            if st.button("🚀 رفع المحتوى"):
                if up_file and p_title:
                    file_path = os.path.join(MEDIA_DIR, up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    f_type = "video" if up_file.type.startswith("video") else "image"
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, status) VALUES (?, ?, ?, ?, 'approved')",
                                  (st.session_state.user_phone, p_title, f_type, file_path))
                        conn.commit()
                    st.success("✔️ تم رفع ونشر المحتوى بنجاح!")
                    st.rerun()

        with tab_manage_posts:
            st.write("🗑️ **قائمة فيديوهاتك ومنشوراتك (يمكنك مسح أي فيديو نهائياً ولن يظهر للطلاب بعد الآن):**")
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT id, title, media_type, file_path FROM posts WHERE teacher_phone=?", (st.session_state.user_phone,))
                my_posts = c.fetchall()

            if my_posts:
                for mp_id, mp_title, mp_type, mp_path in my_posts:
                    st.markdown(f"📌 **العنوان:** {mp_title}")
                    if os.path.exists(mp_path):
                        if mp_type == "image":
                            st.image(mp_path, width=200)
                        elif mp_type == "video":
                            st.video(mp_path)
                    
                    if st.button(f"🗑️ مسح هذا الفيديو نهائياً", key=f"del_post_{mp_id}"):
                        try:
                            if os.path.exists(mp_path):
                                os.remove(mp_path)
                        except:
                            pass
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM posts WHERE id=?", (mp_id,))
                            conn.commit()
                        st.success("تم مسح الفيديو بنجاح ولم يعد يظهر لأي طالب!")
                        st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد فيديوهات أو منشورات مرفوعة حالياً.")

        with tab_subs:
            st.write("📋 **طلبات واشتراكات الطلاب (إلغاء الاشتراك يزيل البث والفيديوهات من عند الطالب فوراً):**")
            display_teacher_requests(st.session_state.user_phone)

        with tab_prof:
            with st.form("prof_form"):
                name_in = st.text_input("الاسم:", value=t_info[0] if t_info else "")
                sub_in = st.text_input("المادة:", value=t_info[1] if t_info else "")
                price_in = st.number_input("السعر (جـ):", value=float(t_info[4]) if t_info and t_info[4] else 100.0)
                if st.form_submit_button("حفظ التعديلات"):
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE teachers SET name=?, subject=?, price=? WHERE phone=?",
                                  (name_in, sub_in, price_in, st.session_state.user_phone))
                        conn.commit()
                    st.success("تم الحفظ!")
                    st.rerun()

    # ------------------------------------------
    # واجهة المطور
    # ------------------------------------------
    elif st.session_state.user_role == "مطور":
        st.subheader("👑 لوحة تحكم المطور الشاملة")
        dev_tab1, dev_tab2 = st.tabs(["🎥 مراجعة المحتوى المنشور", "👨‍🏫 إضافة وإدارة الأساتذة"])
        
        with dev_tab1:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT id, teacher_phone, title, media_type, file_path FROM posts WHERE status='pending'")
                pending_posts = c.fetchall()
            
            if pending_posts:
                for p_id, p_teacher, p_title, p_type, p_path in pending_posts:
                    st.markdown(f"📱 **أستاذ:** {p_teacher} | 📌 **العنوان:** {p_title}")
                    if os.path.exists(p_path):
                        if p_type == "image":
                            st.image(p_path, width=250)
                        elif p_type == "video":
                            st.video(p_path)
                    col_ok, col_no = st.columns(2)
                    if col_ok.button(f"✅ موافقة", key=f"app_{p_id}"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE posts SET status='approved' WHERE id=?", (p_id,))
                            conn.commit()
                        st.rerun()
                    if col_no.button(f"❌ رفض", key=f"rej_{p_id}"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM posts WHERE id=?", (p_id,))
                            conn.commit()
                        st.rerun()
            else:
                st.info("لا يوجد محتوى معلق للمراجعة.")

        with dev_tab2:
            st.write("➕ **إضافة أستاذ جديد للسيستم:**")
            with st.form("add_teacher_dev"):
                new_t_name = st.text_input("اسم الأستاذ:")
                new_t_phone = st.text_input("رقم المحمول:")
                new_t_sub = st.text_input("المادة الدراسية:")
                new_t_price = st.number_input("سعر الاشتراك (جـ):", value=100.0)
                add_t_btn = st.form_submit_button("إضافة الأستاذ فوراً للسيستم")
                
                if add_t_btn:
                    if new_t_phone and new_t_name:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT id FROM teachers WHERE phone=?", (new_t_phone,))
                            if c.fetchone():
                                st.error("رقم المحمول مسجل مسبقاً لأستاذ آخر في السيستم!")
                            else:
                                hashed_tp = hash_password("901000")
                                c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id) 
                                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                          (new_t_phone, hashed_tp, new_t_name, new_t_sub, 'جميع المراحل', 30, new_t_price, '', f"room_{new_t_phone}"))
                                c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (new_t_phone, new_t_name))
                                conn.commit()
                                st.success("✔️ تم إضافة الأستاذ بنجاح للسيستم!")
                                st.rerun()
                    else:
                        st.error("يرجى ملء الحقول المطلوبة.")
