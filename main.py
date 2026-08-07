import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components
import hashlib
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. الإعدادات الأساسية وإعدادات الصفحة
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# إخفاء شريط التحميل، الروابط الخارجية، وعلامات Streamlit بالكامل
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stStatusWidget"] {visibility: hidden; display: none;}
    div[data-testid="stToolbar"] {visibility: hidden; display: none;}
    div[data-testid="stDecoration"] {visibility: hidden; display: none;}
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    .stApp {
        direction: rtl;
        text-align: right;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
        color: #0f172a !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    label, p, span, h1, h2, h3, h4, div {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    .stTextInput input, .stNumberInput input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    .card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08) !important;
        margin-bottom: 20px !important;
    }
    .cash-box {
        background: #16a34a !important;
        color: #ffffff !important;
        padding: 14px !important;
        border-radius: 12px !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 16px !important;
        margin: 12px 0 !important;
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
        id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, name TEXT, subject TEXT,
        grade_level TEXT, age INTEGER, price REAL, image_url TEXT, room_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, teacher_phone TEXT,
        status TEXT DEFAULT 'pending', UNIQUE(student_phone, teacher_phone))''')
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, title TEXT,
        media_type TEXT, file_path TEXT, status TEXT DEFAULT 'pending')''')
    conn.commit()
    conn.close()

init_db()

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
            st.write(f"📌 **{p_title}**")
            if os.path.exists(p_path):
                if p_type == "image":
                    st.image(p_path)
                elif p_type == "video":
                    st.video(p_path)
            st.write("---")
    else:
        st.info("لا توجد منشورات أو فيديوهات معتمدة ومتاحة حالياً.")

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

            col_a, col_b, col_c = st.columns([2, 1, 1])
            col_a.write(f"🎓 الطالب: **{st_display_name}** | السن: {st_display_age} | المرحلة: {st_display_grade} (رقم: {s_ph}) [الحالة: {status}]")
            
            if status == 'pending':
                if col_b.button("✅ قبول", key=f"acc_{s_ph}"):
                    c.execute("UPDATE subscriptions SET status='active' WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                    conn.commit()
                    st.rerun()
                if col_c.button("❌ رفض", key=f"ref_{s_ph}"):
                    c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                    conn.commit()
                    st.rerun()
            st.write("---")
    else:
        st.info("لا توجد طلبات اشتراك حالياً.")
    conn.close()

# ==========================================
# 5. واجهة المستخدم الرئيسية (UI)
# ==========================================
st.title("⚡ منصة نوفا التعليمية")
st.write("---")

if not st.session_state.is_logged_in:
    role_choice = st.radio("اختر صفتك في التطبيق:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑"], horizontal=True)
    st.write("---")

    if role_choice == "طالب 👨‍🎓":
        student_mode = st.radio("اختر العملية:", ["تسجيل دخول", "حساب جديد"], horizontal=True)
        
        if student_mode == "حساب جديد":
            with st.form("student_signup"):
                s_name = st.text_input("الاسم الكامل:")
                s_email = st.text_input("البريد الإلكتروني:")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_phone = st.text_input("رقم التليفون:")
                s_age = st.text_input("السن:")
                s_grade = st.text_input("المرحلة الدراسية:")
                s_signup_btn = st.form_submit_button("تسجيل الحساب والدخول")
                
                if s_signup_btn:
                    if s_email and s_pass and s_phone:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("SELECT id FROM users WHERE email=? OR phone=?", (s_email, s_phone))
                        if c.fetchone():
                            st.error("🚫 البريد الإلكتروني أو رقم التليفون مسجل من قبل!")
                        else:
                            hashed_pass = hash_password(s_pass)
                            c.execute("INSERT INTO users (phone, email, password, name, age, grade, role, is_blocked) VALUES (?, ?, ?, ?, ?, ?, 'طالب', 0)", 
                                      (s_phone, s_email, hashed_pass, s_name if s_name else "طالب", s_age, s_grade))
                            conn.commit()
                            login_user(s_phone, "طالب")
                            st.success("تم إنشاء الحساب والدخول بنجاح!")
                            st.rerun()
                        conn.close()
                    else:
                        st.error("يرجى إدخال البريد الإلكتروني وكلمة المرور ورقم التليفون على الأقل!")
        
        else:
            with st.form("student_login"):
                s_email_in = st.text_input("البريد الإلكتروني:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                s_login_btn = st.form_submit_button("دخول التطبيق")
                
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
                                login_user(p_val, "طالب")
                                st.success("تم الدخول بنجاح!")
                                st.rerun()
                        else:
                            st.error("البريد الإلكتروني أو كلمة المرور غير صحيحة!")
                    else:
                        st.error("يرجى إدخال البيانات!")

    elif role_choice == "أستاذ 👨‍🏫":
        with st.form("teacher_reg"):
            t_phone = st.text_input("رقم التليفون:")
            t_name = st.text_input("الاسم:")
            t_code = st.text_input("الكود السري:", type="password")
            t_btn = st.form_submit_button("دخول الأستاذ")
            
            if t_btn:
                correct_t_code = st.secrets.get("TEACHER_SECRET", "90100")
                if t_code.strip() == correct_t_code and t_phone:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("SELECT is_blocked FROM users WHERE phone=?", (t_phone,))
                    u_stat = c.fetchone()
                    if u_stat and u_stat[0] == 1:
                        st.error("🚫 هذا الحساب محظور!")
                    else:
                        c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (t_phone, t_name if t_name else "أستاذ"))
                        c.execute("INSERT OR IGNORE INTO teachers (phone, name, subject, grade_level, age, price, image_url, room_id) VALUES (?, ?, 'غير محدد', 'جميع المراحل', 30, 100, '', ?)", 
                                  (t_phone, t_name if t_name else "أستاذ", f"room_{t_phone}"))
                        conn.commit()
                        login_user(t_phone, "أستاذ")
                        st.success("أهلاً بك يا استاذنا!")
                        st.rerun()
                    conn.close()
                else:
                    st.error("بيانات غير صحيحة!")

    elif role_choice == "مطور 👑":
        with st.form("dev_reg"):
            dev_code = st.text_input("الكود السري للمطور:", type="password")
            dev_btn = st.form_submit_button("دخول لوحة المطور")
            
            if dev_btn:
                correct_dev_code = st.secrets.get("DEV_SECRET", "900800")
                if dev_code.strip() == correct_dev_code:
                    login_user("dev_admin", "مطور")
                    st.success("أهلاً بك يا مطورنا!")
                    st.rerun()
                else:
                    st.error("الكود السري للمطور خطأ!")

else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"مرحباً بك: **{st.session_state.user_role}**")
    if logout_col.button("🚪 تسجيـل الخروج"):
        logout_user()
        st.rerun()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ------------------------------------------
    # واجهة الطالب
    # ------------------------------------------
    if st.session_state.user_role == "طالب":
        st.subheader("🎓 قائمة الأساتذة والمواد الدراسية")
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id, phone FROM teachers")
        teachers = c.fetchall()

        if teachers:
            for t in teachers:
                t_name, t_sub, t_grade, t_age, t_price, t_img, room_id, t_phone = t
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 3])
                with col1:
                    if t_img:
                        st.image(t_img, width=130)
                    else:
                        st.title("👨‍🏫")
                with col2:
                    st.markdown(f"### الأستاذ: {t_name}")
                    st.markdown(f"📖 **المادة:** {t_sub} | 🏫 **المرحلة:** {t_grade}")
                    st.markdown(f"🎂 **العمر:** {t_age} سنة | 💰 **السعر:** {t_price} جنيه")
                
                c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                          (st.session_state.user_phone, t_phone))
                sub_status = c.fetchone()

                if sub_status and sub_status[0] == 'active':
                    st.success("✅ أنت مشترك - يمكنك مشاهدة البث والفيديوهات")
                    tab_live, tab_media = st.tabs(["🔴 البث المباشر", "🎬 الفيديوهات"])
                    with tab_live:
                        stream_html = f"""
                        <iframe src="https://vdo.ninja/?view={room_id}&autostart=1" 
                                style="width: 100%; height: 430px; border: 2px solid #2563eb; border-radius: 12px; background: #000;"
                                allow="camera; microphone; autoplay" allowfullscreen>
                        </iframe>
                        """
                        components.html(stream_html, height=450)
                    with tab_media:
                        display_student_media(t_phone)
                        
                elif sub_status and sub_status[0] == 'pending':
                    st.warning("⏳ طلبك قيد المراجعة.")
                else:
                    st.markdown(f"""
                    <div class="cash-box">
                        💸 للاشتراك حول ({t_price} جنيه) على فودافون كاش: <b>01213783090</b>
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
        st.subheader("👨‍🏫 استوديو إدارة الدروس")
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id FROM teachers WHERE phone=?", (st.session_state.user_phone,))
        t_info = c.fetchone()
        room_id = t_info[6] if t_info else f"room_{st.session_state.user_phone}"

        tab_stream, tab_post, tab_subs, tab_prof = st.tabs(["🔴 البث المباشر", "📤 نشر محتوى", "👥 طلبات الطلاب", "⚙️ الإعدادات"])

        with tab_stream:
            t_stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1" 
                    style="width: 100%; height: 450px; border: 2px solid #2563eb; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(t_stream_html, height=470)

        with tab_post:
            p_title = st.text_input("عنوان الفيديو:")
            up_file = st.file_uploader("اختر فيديو أو صورة:", type=["png", "jpg", "jpeg", "mp4"])
            if st.button("🚀 إرسال للمراجعة"):
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

            st.write("---")
            c.execute("SELECT title, status FROM posts WHERE teacher_phone=?", (st.session_state.user_phone,))
            my_posts = c.fetchall()
            if my_posts:
                for p_t, p_s in my_posts:
                    stat_msg = "منشور ✅" if p_s == 'approved' else "قيد المراجعة ⏳"
                    st.write(f"✔️ **{p_t}** — ({stat_msg})")
            else:
                st.info("لم تنشر شيء بعد.")

        with tab_subs:
            st.write("📋 **الطلاب المتقدمين:**")
            display_teacher_requests(st.session_state.user_phone)

        with tab_prof:
            with st.form("prof_form"):
                name_in = st.text_input("الاسم:", value=t_info[0] if t_info else "")
                sub_in = st.text_input("المادة:", value=t_info[1] if t_info else "")
                grade_in = st.text_input("المرحلة:", value=t_info[2] if t_info else "")
                age_in = st.number_input("العمر:", value=int(t_info[3]) if t_info and t_info[3] else 30)
                price_in = st.number_input("السعر (جنيه):", value=float(t_info[4]) if t_info and t_info[4] else 100.0)
                img_in = st.text_input("رابط الصورة:", value=t_info[5] if t_info else "")
                if st.form_submit_button("حفظ"):
                    c.execute("UPDATE teachers SET name=?, subject=?, grade_level=?, age=?, price=?, image_url=? WHERE phone=?",
                              (name_in, sub_in, grade_in, age_in, price_in, img_in, st.session_state.user_phone))
                    conn.commit()
                    st.success("تم الحفظ!")
                    st.rerun()

    # ------------------------------------------
    # واجهة المطور
    # ------------------------------------------
    elif st.session_state.user_role == "مطور":
        st.subheader("👑 لوحة تحكم المطور")
        c.execute("SELECT COUNT(*) FROM users WHERE role='طالب'")
        st_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE role='أستاذ'")
        tc_count = c.fetchone()[0]
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("الطلاب", st_count)
        col_m2.metric("الأساتذة", tc_count)
        st.write("---")
        
        dev_tab1, dev_tab2 = st.tabs(["🎥 مراجعة المحتوى", "🚫 إدارة المستخدمين"])
        with dev_tab1:
            c.execute("SELECT id, teacher_phone, title, media_type, file_path FROM posts WHERE status='pending'")
            pending_posts = c.fetchall()
            if pending_posts:
                for p_id, p_teacher, p_title, p_type, p_path in pending_posts:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.write(f"📱 **رقم الأستاذ:** {p_teacher} | 📌 **العنوان:** {p_title}")
                    if os.path.exists(p_path):
                        if p_type == "image":
                            st.image(p_path, width=300)
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
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("لا يوجد محتوى للمراجعة.")

        with dev_tab2:
            c.execute("SELECT id, phone, email, name, role, is_blocked FROM users WHERE role != 'مطور'")
            users = c.fetchall()
            if users:
                for u_id, u_phone, u_email, u_name, u_role, is_blocked in users:
                    u_col1, u_col2, u_col3 = st.columns([2, 1, 1])
                    ident = u_email if u_email else u_phone
                    u_col1.write(f"👤 **{u_name}** | {ident} ({u_role})")
                    if is_blocked == 1:
                        u_col2.error("محظور 🚫")
                        if u_col3.button("فك الحظر", key=f"unblock_{u_id}"):
                            c.execute("UPDATE users SET is_blocked=0 WHERE id=?", (u_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        u_col2.success("نشط ✅")
                        if u_col3.button("حظر", key=f"block_{u_id}"):
                            c.execute("UPDATE users SET is_blocked=1 WHERE id=?", (u_id,))
                            conn.commit()
                            st.rerun()

    conn.close()

st.write("---")
st.caption("⚡ منصة نوفا التعليمية © 2026")
