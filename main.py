import streamlit as st
import streamlit.components.v1 as components
import sqlite3

# ==================== 1. إعداد قاعدة البيانات ====================
DB_NAME = 'nova_v10.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            subject TEXT,
            age INTEGER,
            price REAL,
            room_id TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_email TEXT,
            title TEXT,
            media_type TEXT,
            media_data BLOB
        )
    ''')

    cursor.execute("SELECT * FROM users WHERE role = 'المطور التنفيذي 👑'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password, role) VALUES ('admin@nova.com', '20101999', 'المطور التنفيذي 👑')")
    
    conn.commit()
    conn.close()

init_db()

# ==================== 2. التصميم الفخم (UI) ====================
st.set_page_config(
    page_title="منصة نوفا التعليمية",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    /* خلفية داكنة وفخمة */
    .stApp { 
        direction: rtl; 
        text-align: right; 
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%);
        color: #f8fafc !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    label, p, span, div, h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }

    .stTextInput input, .stNumberInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #6366f1 !important;
        border-radius: 12px !important;
    }

    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
    }

    .teacher-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. حفظ الجلسة ====================
query_params = st.query_params

if "is_logged_in" not in st.session_state:
    if "user_email" in query_params and "user_role" in query_params:
        st.session_state.is_logged_in = True
        st.session_state.user_email = query_params["user_email"]
        st.session_state.user_role = query_params["user_role"]
    else:
        st.session_state.is_logged_in = False
        st.session_state.user_role = None
        st.session_state.user_email = ""

def save_login(email, role):
    st.session_state.is_logged_in = True
    st.session_state.user_email = email
    st.session_state.user_role = role
    st.query_params["user_email"] = email
    st.query_params["user_role"] = role

def logout():
    st.session_state.is_logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = ""
    st.query_params.clear()

st.title("⚡ منصة نوفا التعليمية الذكية")
st.caption("البث المباشر المدمج باللغة العربية بالكامل")
st.write("---")

# ==================== 4. شاشة الدخول ====================
if not st.session_state.is_logged_in:
    selected_role = st.radio("اختر صفة الدخول:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "المطور التنفيذي 👑"], horizontal=True)
    st.write("---")

    if selected_role == "طالب 👨‍🎓":
        st.subheader("👨‍🎓 تسجيل دخول الطلاب")
        with st.form("student_form"):
            s_email = st.text_input("البريد الإلكتروني:")
            s_pass = st.text_input("كلمة السر:", type="password")
            if st.form_submit_button("تسجيل الدخول", use_container_width=True):
                if s_email and s_pass:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (s_email, s_pass, "طالب 👨‍🎓"))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        pass
                    conn.close()
                    save_login(s_email, "طالب 👨‍🎓")
                    st.rerun()

    elif selected_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 تسجيل دخول الأساتذة")
        with st.form("teacher_form"):
            t_secret = st.text_input("كود السر الخاص بالأساتذة:", type="password")
            t_email = st.text_input("البريد الإلكتروني:")
            t_pass = st.text_input("كلمة السر:", type="password")
            if st.form_submit_button("دخول الاستوديو", use_container_width=True):
                if t_secret.strip() == "90100" and t_email and t_pass:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (t_email, t_pass, "أستاذ 👨‍🏫"))
                        c.execute("INSERT INTO teachers (email, name, subject, age, price, room_id) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (t_email, t_email.split('@')[0], "لم تحدد", 30, 0.0, f"room_{t_email.split('@')[0]}"))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        pass
                    conn.close()
                    save_login(t_email, "أستاذ 👨‍🏫")
                    st.rerun()
                else:
                    st.error("كود السر أو البيانات غير صحيحة!")

    elif selected_role == "المطور التنفيذي 👑":
        secret_code = st.text_input("الرقم السري للمطور:", type="password")
        if st.button("دخول لوحة التحكم", use_container_width=True):
            if secret_code.strip() == "20101999":
                save_login("admin@nova.com", "المطور التنفيذي 👑")
                st.rerun()

# ==================== 5. اللوحات الداخلية ====================
else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"أهلاً بك: **{st.session_state.user_role}** ({st.session_state.user_email})")
    if logout_col.button("🚪 تسجيل الخروج", use_container_width=True):
        logout()
        st.rerun()

    # ---------------- A. واجهة الطالب ----------------
    if st.session_state.user_role == "طالب 👨‍🎓":
        st.subheader("🔍 مشاهدة البث المباشر للأساتذة")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, age, price, room_id, email FROM teachers")
        teachers = c.fetchall()
        
        if teachers:
            for t in teachers:
                t_id, t_name, t_sub, t_age, t_price, room_id, t_email = t
                st.markdown('<div class="teacher-card">', unsafe_allow_html=True)
                st.markdown(f"## 👨‍🏫 الأستاذ: **{t_name}** ({t_sub})")
                
                # واجهة استقبال البث المباشر باللغة العربية
                student_stream_html = f"""
                <div style="background-color: #000; border-radius: 16px; padding: 15px; text-align: center; border: 2px solid #6366f1;">
                    <h3 style="color: #fff; font-family: sans-serif; margin-bottom: 10px;">🔴 شاشة البث المباشر للدرس</h3>
                    <iframe src="https://vdo.ninja/?view={room_id}&autostart=1&cleanoutput=1&nobuttons=1" 
                            style="width: 100%; height: 420px; border: none; border-radius: 12px; background: #111;"
                            allow="camera; microphone; autoplay" allowfullscreen>
                    </iframe>
                </div>
                """
                components.html(student_stream_html, height=500)
                st.markdown('</div>', unsafe_allow_html=True)
        conn.close()

    # ---------------- B. واجهة الأستاذ ----------------
    elif st.session_state.user_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 استوديو البث المباشر الخاص بالأستاذ")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT room_id FROM teachers WHERE email=?", (st.session_state.user_email,))
        t_data = c.fetchone()
        room_id = t_data[0] if t_data else f"room_{st.session_state.user_email.split('@')[0]}"
        
        # واجهة بث عربية 100% بدون زراير إنجليزي
        teacher_stream_html = f"""
        <div style="background: #1e293b; border-radius: 16px; padding: 20px; text-align: center; border: 2px solid #7c3aed; direction: rtl;">
            <h2 style="color: #4f46e5; font-family: sans-serif; margin-bottom: 15px;">🎥 استوديو البث المباشر للأساتذة</h2>
            <p style="color: #cbd5e1; font-family: sans-serif;">اضغط على الزرار الأسفل لبدء تشغيل الكاميرا والمايك فوراً للطلاب:</p>
            
            <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1&cleanoutput=1" 
                    style="width: 100%; height: 450px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
        </div>
        """
        components.html(teacher_stream_html, height=560)
        conn.close()

    # ---------------- C. واجهة المطور ----------------
    elif st.session_state.user_role == "المطور التنفيذي 👑":
        st.subheader("👑 لوحة التحكم")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, email FROM teachers")
        st.dataframe(c.fetchall(), use_container_width=True)
        conn.close()

st.write("---")
st.caption("⚡ منصة نوفا التعليمية © 2026")
