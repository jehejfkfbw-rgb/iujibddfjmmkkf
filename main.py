import streamlit as st
import streamlit.components.v1 as components
import sqlite3

# ==================== 1. إعداد قاعدة البيانات ====================
DB_NAME = 'nova_final_v2.db'

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

# ==================== 2. إعداد الصفحة والتصميم ====================
st.set_page_config(
    page_title="منصة نوفا التعليمية",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
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

    .post-card {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. آلية الثبات وحفظ تسجيل الدخول ====================
params = st.query_params

# التحقق من وجود بيانات مسجلة مسبقاً في الـ URL
if "user_email" in params and "user_role" in params:
    st.session_state.is_logged_in = True
    st.session_state.user_email = params["user_email"]
    st.session_state.user_role = params["user_role"]
else:
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
        st.session_state.user_role = None
        st.session_state.user_email = ""

def save_login(email, role):
    st.session_state.is_logged_in = True
    st.session_state.user_email = email
    st.session_state.user_role = role
    # حفظ البيانات في الـ Query Params للتأكد من إنها مش هتمسح مع الريفرش
    st.query_params["user_email"] = email
    st.query_params["user_role"] = role

def logout():
    st.session_state.is_logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = ""
    st.query_params.clear()

st.title("⚡ منصة نوفا التعليمية")
st.write("---")

# ==================== 4. شاشة الدخول (تظهر فقط لو مش مسجل) ====================
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
    top_col.success(f"مرحباً بك: **{st.session_state.user_role}** ({st.session_state.user_email})")
    
    # زر الخروج الصريح فقط هو اللي بيمسح التسجيل
    if logout_col.button("🚪 تسجيل الخروج", use_container_width=True):
        logout()
        st.rerun()

    # ---------------- A. واجهة الطالب ----------------
    if st.session_state.user_role == "طالب 👨‍🎓":
        st.subheader("🔍 استعراض الأساتذة والدروس")
        search_q = st.text_input("ابحث باسم الأستاذ أو المادة الدراسية:")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        if search_q:
            c.execute("SELECT id, name, subject, age, price, room_id, email FROM teachers WHERE name LIKE ? OR subject LIKE ?", 
                      (f"%{search_q}%", f"%{search_q}%"))
        else:
            c.execute("SELECT id, name, subject, age, price, room_id, email FROM teachers")
            
        teachers = c.fetchall()
        
        if teachers:
            for t in teachers:
                t_id, t_name, t_sub, t_age, t_price, room_id, t_email = t
                st.markdown('<div class="teacher-card">', unsafe_allow_html=True)
                st.markdown(f"## 👨‍🏫 الأستاذ: **{t_name}**")
                st.markdown(f"📖 **المادة:** {t_sub} | 🎂 **العمر:** {t_age} سنة | 💰 **سعر الاشتراك:** {t_price} جنيه")
                st.write("---")
                
                # البث المباشر
                st.write("🔴 **البث المباشر للأستاذ:**")
                student_stream_html = f"""
                <iframe src="https://vdo.ninja/?view={room_id}&autostart=1&cleanoutput=1" 
                        style="width: 100%; height: 400px; border: 2px solid #6366f1; border-radius: 12px; background: #000;"
                        allow="camera; microphone; autoplay" allowfullscreen>
                </iframe>
                """
                components.html(student_stream_html, height=420)

                # المنشورات
                st.write("🎬 **المحتوى المنشور والدروس:**")
                c.execute("SELECT title, media_type, media_data FROM posts WHERE teacher_email=?", (t_email,))
                posts = c.fetchall()
                if posts:
                    for post in posts:
                        p_title, p_type, p_data = post
                        st.markdown(f'<div class="post-card"><b>📌 {p_title}</b>', unsafe_allow_html=True)
                        if p_type == "image":
                            st.image(p_data)
                        elif p_type == "video":
                            st.video(p_data)
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("لا توجد منشورات أو صور حالياً لهذا الأستاذ.")

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("لم يتم العثور على أي أساتذة.")
        conn.close()

    # ---------------- B. واجهة الأستاذ ----------------
    elif st.session_state.user_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 لوحة تحكم واستوديو الأستاذ")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, age, price, room_id FROM teachers WHERE email=?", (st.session_state.user_email,))
        t_data = c.fetchone()
        
        tab_live, tab_upload, tab_profile = st.tabs(["🔴 تشغيل البث المباشر", "📤 نشر صور وفيديوهات", "👤 تعديل البيانات الشخصية"])
        
        # 1. استوديو البث
        with tab_live:
            st.write("🎙️ **استوديو الكاميرا للبث المباشر للطلاب:**")
            room_id = t_data[5] if t_data else f"room_{st.session_state.user_email.split('@')[0]}"
            
            teacher_stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1&cleanoutput=1" 
                    style="width: 100%; height: 450px; border: 2px solid #7c3aed; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(teacher_stream_html, height=470)

        # 2. رفع المنشورات
        with tab_upload:
            st.write("📤 **نشر دروس أو صور أوراق للطلاب:**")
            post_title = st.text_input("عنوان الدرس أو الصورة:")
            uploaded_file = st.file_uploader("اختر فيديو أو صورة من المعرض:", type=["png", "jpg", "jpeg", "mp4", "mov"])
            
            if st.button("🚀 نشر الآن", use_container_width=True):
                if uploaded_file and post_title:
                    file_bytes = uploaded_file.read()
                    file_type = "video" if uploaded_file.type.startswith("video") else "image"
                    
                    c.execute("INSERT INTO posts (teacher_email, title, media_type, media_data) VALUES (?, ?, ?, ?)",
                              (st.session_state.user_email, post_title, file_type, file_bytes))
                    conn.commit()
                    st.success("تم النشر بنجاح وظهرت في صفحة الطلاب!")
                    st.rerun()
                else:
                    st.error("يرجى كتابة العنوان واختيار الملف أولاً!")

        # 3. تعديل البيانات
        with tab_profile:
            with st.form("update_profile"):
                curr_name = t_data[1] if t_data else ""
                curr_sub = t_data[2] if t_data else ""
                curr_age = t_data[3] if t_data else 30
                curr_price = t_data[4] if t_data else 0.0
                
                name_in = st.text_input("اسم الأستاذ الكامل:", value=curr_name)
                sub_in = st.text_input("المادة الدراسية:", value=curr_sub)
                age_in = st.number_input("العمر:", value=curr_age)
                price_in = st.number_input("سعر الحصة / الكورس:", value=curr_price)
                
                if st.form_submit_button("حفظ التغييرات"):
                    c.execute("UPDATE teachers SET name=?, subject=?, age=?, price=? WHERE email=?", 
                              (name_in, sub_in, age_in, price_in, st.session_state.user_email))
                    conn.commit()
                    st.success("تم حفظ البيانات بنجاح!")
                    st.rerun()
        conn.close()

    # ---------------- C. واجهة المطور ----------------
    elif st.session_state.user_role == "المطور التنفيذي 👑":
        st.subheader("👑 لوحة التحكم المركزية")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        st.write("📋 **جدول الأساتذة:**")
        c.execute("SELECT id, name, subject, age, price, email FROM teachers")
        st.dataframe(c.fetchall(), use_container_width=True)
        
        st.write("📋 **جدول المنشورات:**")
        c.execute("SELECT id, teacher_email, title, media_type FROM posts")
        st.dataframe(c.fetchall(), use_container_width=True)
        conn.close()

st.write("---")
st.caption("⚡ منصة نوفا التعليمية © 2026")
