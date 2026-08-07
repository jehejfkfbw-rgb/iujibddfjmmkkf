import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components
import hashlib
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التطبيق وتصميم واجهة الموبايل
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stStatusWidget"] {visibility: hidden; display: none;}
    div[data-testid="stToolbar"] {visibility: hidden; display: none;}
    div[data-testid="stDecoration"] {visibility: hidden; display: none;}
    
    /* جعل الحاوية الرئيسية تبدو كإطار تطبيق موبايل أنيق */
    .block-container {
        max-width: 500px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #0f172a !important;
        color: #f8fafc !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* تخصيص النصوص والعناوين داخل التطبيق */
    h1, h2, h3, h4, p, span, label {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
    
    /* تصميم الحقول كأنها حقول تطبيق حقيقي */
    .stTextInput input, .stNumberInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #334155 !important;
        border-radius: 14px !important;
        padding: 12px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3b82f6 !important;
    }
    
    /* أزرار التطبيق بتصميم جذاب */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 14px 20px !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* تصميم البطاقات (Cards) داخل التطبيق */
    .app-card {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 16px !important;
    }
    
    /* صندوق الدفع الفوري */
    .cash-box {
        background: #065f46 !important;
        color: #ecfdf5 !important;
        padding: 14px !important;
        border-radius: 14px !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 15px !important;
        margin: 12px 0 !important;
        border: 1px solid #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد قاعدة البيانات والملفات
# ==========================================
MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

DB_NAME = 'nova_complete_system.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, email TEXT UNIQUE,
        password TEXT, name TEXT, age TEXT, grade TEXT, role TEXT, is_blocked INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, password TEXT, name TEXT, subject TEXT,
        grade_level TEXT, age INTEGER, price REAL, image_url TEXT, room_id TEXT)''')
        
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, teacher_phone TEXT,
        status TEXT DEFAULT 'pending', UNIQUE(student_phone, teacher_phone))''')
        
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, title TEXT,
        media_type TEXT, file_path TEXT, status TEXT DEFAULT 'pending')''')

    # جدول الإعدادات العامة (يتحكم بها المطور من اللوحة)
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)''')
    
    # وضع قيمة افتراضية لكود الأساتذة لو لم يكن موجوداً
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('teacher_secret', '123456')")
    
    conn.commit()
    conn.close()

init_db()

def get_setting(key, default=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def update_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 3. إدارة الجلسات واسترجاعها من الرابط
# ==========================================
if "is_logged_in" not in st.session_state:
    params = st.query_params
    qp_phone = params.get("phone", None)
    qp_role = params.get("role", None)
    
    if qp_phone and qp_role:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT is_blocked FROM users WHERE phone=?", (qp_phone,))
        row = c.fetchone()
        conn.close()
        
        if row and row[0] == 0:
            st.session_state.is_logged_in = True
            st.session_state.user_phone = qp_phone
            st.session_state.user_role = qp_role
        else:
            st.session_state.is_logged_in = False
            st.session_state.user_phone = ""
            st.session_state.user_role = None
    else:
        st.session_state.is_logged_in = False
        st.session_state.user_phone = ""
        st.session_state.user_role = None

def login_user(phone, role):
    st.session_state.is_logged_in = True
    st.session_state.user_phone = phone
    st.session_state.user_role = role
    st.query_params["phone"] = phone
    st.query_params["role"] = role

def logout_user():
    st.session_state.is_logged_in = False
    st.session_state.user_phone = ""
    st.session_state.user_role = None
    st.query_params.clear()

# ==========================================
# 4. التحديثات التلقائية (Real-Time Fragments)
# ==========================================
@st.fragment
def display_student_media(teacher_phone):
    st_autorefresh(interval=5000, key=f"refresh_media_{teacher_phone}")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT title, media_type, file_path FROM posts WHERE teacher_phone=? AND status='approved' ORDER BY id DESC", (teacher_phone,))
    posts = c.fetchall()
    conn.close()
    
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

@st.fragment
def display_teacher_requests(teacher_phone):
    st_autorefresh(interval=5000, key=f"refresh_subs_{teacher_phone}")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT student_phone, status FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
    subs = c.fetchall()
    
    if subs:
        for s_ph, status in subs:
            c.execute("SELECT name, age, grade FROM users WHERE phone=?", (s_ph,))
            st_data = c.fetchone()
            st_display_name = st_data[0] if st_data else s_ph
            st_display_age = st_data[1] if st_data else "غير محدد"
            st_display_grade = st_data[2] if st_data else "غير محدد"

            st.markdown(f"🎓 **{st_display_name}** | السن: {st_display_age} | المرحلة: {st_display_grade}")
            st.markdown(f"📱 الهاتف: `{s_ph}` | الحالة: **{status}**")
            
            if status == 'pending':
                col_a, col_b = st.columns(2)
                if col_a.button("✅ قبول", key=f"acc_{s_ph}"):
                    c.execute("UPDATE subscriptions SET status='active' WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                    conn.commit()
                    st.rerun()
                if col_b.button("❌ رفض", key=f"ref_{s_ph}"):
                    c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                    conn.commit()
                    st.rerun()
            st.write("---")
    else:
        st.info("لا توجد طلبات اشتراك حالياً.")
    conn.close()

# ==========================================
# 5. واجهة التطبيق الرئيسية (Mobile App UI)
# ==========================================
st.markdown("<h2 style='text-align: center;'>⚡ تطبيق نوفا التعليمي</h2>", unsafe_allow_html=True)
st.write("---")

if not st.session_state.is_logged_in:
    role_choice = st.radio("اختر صفتك:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑"], horizontal=True)
    st.write("---")

    if role_choice == "طالب 👨‍🎓":
        student_mode = st.radio("الوضع:", ["تسجيل دخول", "حساب جديد"], horizontal=True)
        
        if student_mode == "حساب جديد":
            with st.form("student_signup"):
                s_name = st.text_input("الاسم الكامل:")
                s_email = st.text_input("البريد الإلكتروني:")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_phone = st.text_input("رقم التليفون:")
                s_age = st.text_input("السن:")
                s_grade = st.text_input("المرحلة الدراسية:")
                s_signup_btn = st.form_submit_button("إنشاء حساب ودخول")
                
                if s_signup_btn:
                    if s_email and s_pass and s_phone:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("SELECT id FROM users WHERE email=? OR phone=?", (s_email, s_phone))
                        if c.fetchone():
                            st.error("🚫 البريد أو الهاتف مسجل مسبقاً!")
                        else:
                            hashed_pass = hash_password(s_pass)
                            if s_email.strip() == "jehejfkfbw@gmail.com":
                                st.toast("مرحبا بك ايها المطور التنفيذي محمد عادل تبع شركه نوفا")
                            
                            c.execute("INSERT INTO users (phone, email, password, name, age, grade, role, is_blocked) VALUES (?, ?, ?, ?, ?, ?, 'طالب', 0)", 
                                      (s_phone, s_email, hashed_pass, s_name if s_name else "طالب", s_age, s_grade))
                            conn.commit()
                            login_user(s_phone, "طالب")
                            st.success("تم التسجيل بنجاح!")
                            st.rerun()
                        conn.close()
                    else:
                        st.error("يرجى ملء الحقول الأساسية!")
        
        else:
            with st.form("student_login"):
                s_email_in = st.text_input("البريد الإلكتروني:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                s_login_btn = st.form_submit_button("تسجيل الدخول")
                
                if s_login_btn:
                    if s_email_in and s_pass_in:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        hashed_pass = hash_password(s_pass_in)
                        c.execute("SELECT phone, is_blocked FROM users WHERE email=? AND password=? AND role='طالب'", (s_email_in, hashed_pass))
                        user_row = c.fetchone()
                        conn.close()
                        
                        if user_row:
                            p_val, is_blocked = user_row
                            if is_blocked == 1:
                                st.error("🚫 هذا الحساب محظور!")
                            else:
                                if s_email_in.strip() == "jehejfkfbw@gmail.com":
                                    st.toast("مرحبا بك ايها المطور التنفيذي محمد عادل تبع شركه نوفا")
                                login_user(p_val, "طالب")
                                st.success("تم الدخول بنجاح!")
                                st.rerun()
                        else:
                            st.error("البيانات غير صحيحة!")
                    else:
                        st.error("يرجى إدخال البيانات!")

    elif role_choice == "أستاذ 👨‍🏫":
        teacher_mode = st.radio("الوضع:", ["تسجيل دخول الأستاذ", "حساب جديد للأستاذ"], horizontal=True)
        
        if teacher_mode == "حساب جديد للأستاذ":
            with st.form("teacher_signup"):
                t_name_reg = st.text_input("الاسم:")
                t_phone_reg = st.text_input("رقم التليفون:")
                t_pass_reg = st.text_input("كلمة المرور:", type="password")
                t_sub_reg = st.text_input("المادة الدراسية:")
                t_secret_code = st.text_input("كود التسجيل السري للأستاذ:", type="password")
                t_signup_btn = st.form_submit_button("إنشاء حساب الأستاذ")
                
                if t_signup_btn:
                    correct_teacher_code = get_setting("teacher_secret", "123456")
                    if t_secret_code.strip() != correct_teacher_code:
                        st.error("🚫 كود التسجيل السري خطأ! تواصل مع المطور للحصول عليه.")
                    elif t_phone_reg and t_pass_reg:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("SELECT id FROM teachers WHERE phone=?", (t_phone_reg,))
                        if c.fetchone():
                            st.error("🚫 رقم التليفون مسجل مسبقاً!")
                        else:
                            hashed_t_pass = hash_password(t_pass_reg)
                            c.execute("INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id) VALUES (?, ?, ?, ?, 'جميع المراحل', 30, 100, '', ?)", 
                                      (t_phone_reg, hashed_t_pass, t_name_reg if t_name_reg else "أستاذ", t_sub_reg if t_sub_reg else "غير محدد", f"room_{t_phone_reg}"))
                            c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (t_phone_reg, t_name_reg if t_name_reg else "أستاذ"))
                            conn.commit()
                            login_user(t_phone_reg, "أستاذ")
                            st.success("تم الحفظ والدخول بنجاح!")
                            st.rerun()
                        conn.close()
                    else:
                        st.error("أدخل رقم الهاتف وكلمة المرور والكود السري!")
        
        else:
            with st.form("teacher_login"):
                t_phone_in = st.text_input("رقم التليفون:")
                t_pass_in = st.text_input("كلمة المرور:", type="password")
                t_login_btn = st.form_submit_button("دخول الأستاذ")
                
                if t_login_btn:
                    if t_phone_in and t_pass_in:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        hashed_t_pass = hash_password(t_pass_in)
                        c.execute("SELECT phone FROM teachers WHERE phone=? AND password=?", (t_phone_in, hashed_t_pass))
                        t_row = c.fetchone()
                        conn.close()
                        
                        if t_row:
                            login_user(t_phone_in, "أستاذ")
                            st.success("تم الدخول بنجاح!")
                            st.rerun()
                        else:
                            st.error("رقم الهاتف أو كلمة المرور خطأ!")
                    else:
                        st.error("يرجى إدخال البيانات!")

    elif role_choice == "مطور 👑":
        with st.form("dev_reg"):
            dev_code = st.text_input("كود المطور السري:", type="password")
            dev_btn = st.form_submit_button("دخول لوحة المطور")
            
            if dev_btn:
                correct_dev_code = st.secrets.get("DEV_SECRET", "900800")
                if dev_code.strip() == correct_dev_code:
                    login_user("dev_admin", "مطور")
                    st.success("أهلاً بك يا مطورنا!")
                    st.rerun()
                else:
                    st.error("الكود خطأ!")

else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"مرحباً بك: **{st.session_state.user_role}**")
    if logout_col.button("🚪 خروج"):
        logout_user()
        st.rerun()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ------------------------------------------
    # واجهة الطالب
    # ------------------------------------------
    if st.session_state.user_role == "طالب":
        st.subheader("🎓 الأساتذة المتاحون")
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id, phone FROM teachers")
        teachers = c.fetchall()

        if teachers:
            for t in teachers:
                t_name, t_sub, t_grade, t_age, t_price, t_img, room_id, t_phone = t
                st.markdown('<div class="app-card">', unsafe_allow_html=True)
                st.markdown(f"### 👨‍🏫 الأستاذ: {t_name}")
                st.markdown(f"📖 **المادة:** {t_sub} | 💰 **السعر:** {t_price} جـ")
                
                c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                          (st.session_state.user_phone, t_phone))
                sub_status = c.fetchone()

                if sub_status and sub_status[0] == 'active':
                    st.success("✅ مشترك - يمكنك المشاهدة")
                    tab_live, tab_media = st.tabs(["🔴 البث", "🎬 الفيديوهات"])
                    with tab_live:
                        stream_html = f"""
                        <iframe src="https://vdo.ninja/?view={room_id}&autostart=1" 
                                style="width: 100%; height: 350px; border: 2px solid #3b82f6; border-radius: 12px; background: #000;"
                                allow="camera; microphone; autoplay" allowfullscreen>
                        </iframe>
                        """
                        components.html(stream_html, height=370)
                    with tab_media:
                        display_student_media(t_phone)
                        
                elif sub_status and sub_status[0] == 'pending':
                    st.warning("⏳ طلبك قيد المراجعة.")
                else:
                    st.markdown(f"""
                    <div class="cash-box">
                        حول ({t_price} جـ) فودافون كاش على: <b>01213783090</b>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🚀 طلب الاشتراك", key=f"btn_{t_phone}"):
                        c.execute("INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status) VALUES (?, ?, 'pending')",
                                  (st.session_state.user_phone, t_phone))
                        conn.commit()
                        st.success("تم إرسال الطلب!")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("لا يوجد أساتذة مسجلون حالياً.")

    # ------------------------------------------
    # واجهة الأستاذ
    # ------------------------------------------
    elif st.session_state.user_role == "أستاذ":
        st.subheader("👨‍🏫 استوديو الأستاذ")
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id FROM teachers WHERE phone=?", (st.session_state.user_phone,))
        t_info = c.fetchone()
        room_id = t_info[6] if t_info else f"room_{st.session_state.user_phone}"

        tab_stream, tab_post, tab_subs, tab_prof = st.tabs(["🔴 البث", "📤 نشر", "👥 الطلبات", "⚙️ الإعدادات"])

        with tab_stream:
            t_stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1" 
                    style="width: 100%; height: 380px; border: 2px solid #3b82f6; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(t_stream_html, height=400)

        with tab_post:
            p_title = st.text_input("عنوان الفيديو:")
            up_file = st.file_uploader("اختر فيديو أو صورة:", type=["png", "jpg", "jpeg", "mp4"])
            if st.button("🚀 رفع المحتوى"):
                if up_file and p_title:
                    file_path = os.path.join(MEDIA_DIR, up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    f_type = "video" if up_file.type.startswith("video") else "image"
                    c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, status) VALUES (?, ?, ?, ?, 'pending')",
                              (st.session_state.user_phone, p_title, f_type, file_path))
                    conn.commit()
                    st.success("✔️ تم الرفع للمراجعة!")
                    st.rerun()

        with tab_subs:
            st.write("📋 **الطلاب:**")
            display_teacher_requests(st.session_state.user_phone)

        with tab_prof:
            with st.form("prof_form"):
                name_in = st.text_input("الاسم:", value=t_info[0] if t_info else "")
                sub_in = st.text_input("المادة:", value=t_info[1] if t_info else "")
                price_in = st.number_input("السعر (جـ):", value=float(t_info[4]) if t_info and t_info[4] else 100.0)
                if st.form_submit_button("حفظ التعديلات"):
                    c.execute("UPDATE teachers SET name=?, subject=?, price=? WHERE phone=?",
                              (name_in, sub_in, price_in, st.session_state.user_phone))
                    conn.commit()
                    st.success("تم الحفظ!")
                    st.rerun()

    # ------------------------------------------
    # واجهة المطور (الشاملة للتحكم في كل شيء)
    # ------------------------------------------
    elif st.session_state.user_role == "مطور":
        st.subheader("👑 لوحة تحكم المطور الشاملة")
        dev_tab1, dev_tab2, dev_tab3, dev_tab4 = st.tabs(["🎥 مراجعة المحتوى", "👨‍🏫 إدارة الأساتذة", "🚫 المستخدمين", "⚙️ الإعدادات العامة"])
        
        with dev_tab1:
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
                        c.execute("UPDATE posts SET status='approved' WHERE id=?", (p_id,))
                        conn.commit()
                        st.rerun()
                    if col_no.button(f"❌ رفض", key=f"rej_{p_id}"):
                        c.execute("DELETE FROM posts WHERE id=?", (p_id,))
                        conn.commit()
                        st.rerun()
            else:
                st.info("لا يوجد محتوى معلق للمراجعة.")

        with dev_tab2:
            st.write("➕ **إضافة أستاذ جديد:**")
            with st.form("add_teacher_dev"):
                new_t_name = st.text_input("اسم الأستاذ:")
                new_t_phone = st.text_input("رقم الهاتف:")
                new_t_pass = st.text_input("كلمة المرور:", type="password")
                new_t_sub = st.text_input("المادة الدراسية:")
                new_t_price = st.number_input("سعر الاشتراك (جـ):", value=100.0)
                add_t_btn = st.form_submit_button("إضافة الأستاذ فوراً")
                
                if add_t_btn:
                    if new_t_phone and new_t_pass and new_t_name:
                        c.execute("SELECT id FROM teachers WHERE phone=?", (new_t_phone,))
                        if c.fetchone():
                            st.error("رقم الهاتف مسجل مسبقاً لأستاذ آخر!")
                        else:
                            hashed_tp = hash_password(new_t_pass)
                            c.execute("INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id) VALUES (?, ?, ?, ?, 'جميع المراحل', 30, ?, '', ?)",
                                      (new_t_phone, hashed_tp, new_t_name, new_t_sub, new_t_price, f"room_{new_t_phone}"))
                            c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (new_t_phone, new_t_name))
                            conn.commit()
                            st.success("تم إضافة الأستاذ بنجاح!")
                            st.rerun()
                    else:
                        st.error("يرجى إكمال البيانات الأساسية للأستاذ.")

            st.write("---")
            st.write("📋 **الأساتذة الحاليون:**")
            c.execute("SELECT id, name, phone, subject, price FROM teachers")
            all_teachers = c.fetchall()
            if all_teachers:
                for t_id, t_n, t_p, t_s, t_pr in all_teachers:
                    st.write(f"👨‍🏫 **{t_n}** | المادة: {t_s} | الهاتف: `{t_p}` | السعر: {t_pr} جـ")
                    if st.button(f"🗑️ حذف الأستاذ {t_n}", key=f"del_t_{t_id}"):
                        c.execute("DELETE FROM teachers WHERE id=?", (t_id,))
                        c.execute("DELETE FROM users WHERE phone=?", (t_p,))
                        conn.commit()
                        st.success("تم الحذف بنجاح!")
                        st.rerun()
            else:
                st.info("لا يوجد أساتذة مسجلون حالياً.")

        with dev_tab3:
            c.execute("SELECT id, phone, email, name, role, is_blocked FROM users WHERE role != 'مطور'")
            users = c.fetchall()
            if users:
                for u_id, u_phone, u_email, u_name, u_role, is_blocked in users:
                    ident = u_email if u_email else u_phone
                    st.write(f"👤 {u_name} ({u_role}) - {ident}")
                    if is_blocked == 1:
                        if st.button(f"فك حظر", key=f"unblock_{u_id}"):
                            c.execute("UPDATE users SET is_blocked=0 WHERE id=?", (u_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        if st.button(f"حظر", key=f"block_{u_id}"):
                            c.execute("UPDATE users SET is_blocked=1 WHERE id=?", (u_id,))
                            conn.commit()
                            st.rerun()
            else:
                st.info("لا يوجد مستخدمون مسجلون.")

        with dev_tab4:
            st.write("⚙️ **إعدادات المنصة:**")
            current_secret = get_setting("teacher_secret", "123456")
            with st.form("settings_form"):
                new_secret_input = st.text_input("كود تسجيل الأساتذة السري الحالي:", value=current_secret)
                save_settings_btn = st.form_submit_button("حفظ التغييرات")
                if save_settings_btn:
                    update_setting("teacher_secret", new_secret_input.strip())
                    st.success("تم تحديث كود التسجيل السري بنجاح!")
                    st.rerun()

    conn.close()

st.write("---")
st.caption("⚡ تطبيق نوفا التعليمي © 2026")
