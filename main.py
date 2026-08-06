import streamlit as st
import streamlit.components.v1 as components
import sqlite3

# ==================== 1. إعداد قاعدة البيانات ====================
DB_NAME = 'nova_v7.db'

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

# ==================== 2. التصميم الفخم والمستقبلي (UI/UX) ====================
st.set_page_config(
    page_title="منصة نوفا التعليمية",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    /* خلفية متدرجة وجذابة للتطبيق بالكامل */
    .stApp { 
        direction: rtl; 
        text-align: right; 
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%);
        color: #f8fafc !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* توضيح كل النصوص والتسميات */
    label, p, span, div, h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }

    /* تصميم خانات الإدخال بشكل عصري */
    .stTextInput input, .stNumberInput input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #6366f1 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }

    /* أزرار تفاعلية بإضاءة متدرجة */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6);
    }

    /* كروت المدرسين والمنشورات احترافية */
    .teacher-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    
    .post-card {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 18px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. نظام الجلسة والدخول الدائم ====================
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
st.caption("الجيل الجديد للتعليم التفاعلي والبث المباشر")
st.write("---")

# ==================== 4. شاشة تسجيل الدخول ====================
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
                                  (t_email, t_email.split('@')[0], "لم تحدد", 30, 0.0, f"nova_room_{t_email.split('@')[0]}"))
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

# ==================== 5. لوحات التحكم الداخلية ====================
else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"أهلاً بك: **{st.session_state.user_role}** ({st.session_state.user_email})")
    if logout_col.button("🚪 تسجيل الخروج", use_container_width=True):
        logout()
        st.rerun()

    # ---------------- A. واجهة الطالب ----------------
    if st.session_state.user_role == "طالب 👨‍🎓":
        st.subheader("🔍 البحث عن الأساتذة والبث المباشر")
        
        search_query = st.text_input("ابحث باسم الأستاذ أو المادة الدراسية:", "")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        if search_query:
            c.execute("SELECT id, name, subject, age, price, room_id, email FROM teachers WHERE name LIKE ? OR subject LIKE ?", 
                      (f"%{search_query}%", f"%{search_query}%"))
        else:
            c.execute("SELECT id, name, subject, age, price, room_id, email FROM teachers")
            
        teachers = c.fetchall()
        
        if teachers:
            for t in teachers:
                t_id, t_name, t_sub, t_age, t_price, room_id, t_email = t
                
                st.markdown('<div class="teacher-card">', unsafe_allow_html=True)
                st.markdown(f"## 👨‍🏫 الأستاذ: **{t_name}**")
                st.markdown(f"📖 **المادة:** {t_sub} | 🎂 **العمر:** {t_age} سنة | 💰 **المصاريف:** {t_price} جنيه")
                st.write("---")
                
                # البث المباشر المحدث للطلاب عبر VDO.ninja البسيط والواقعي
                st.write("🔴 **البث المباشر الحالي للأستاذ:**")
                live_url = f"https://vdo.ninja/?view={room_id}&autoplay=1"
                
                live_iframe = f"""
                <iframe src="{live_url}" 
                        style="height: 500px; width: 100%; border: 2px solid #6366f1; border-radius: 16px; background-color: #000;"
                        allow="camera; microphone; autoplay" allowfullscreen>
                </iframe>
                """
                components.html(live_iframe, height=515)

                # معرض المرفوعات
                st.write("🎬 **المحتوى التعليمي والفيديوهات:**")
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
                    st.caption("لا توجد فيديوهات أو صور منشور حالياً.")

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("لم يتم العثور على نتائج.")
        conn.close()

    # ---------------- B. واجهة الأستاذ ----------------
    elif st.session_state.user_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 استوديو بث الأستاذ")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, age, price, room_id FROM teachers WHERE email=?", (st.session_state.user_email,))
        t_data = c.fetchone()
        
        tab_live, tab_upload, tab_profile = st.tabs(["🔴 استوديو البث الحي", "📤 نشر صور/فيديوهات", "👤 تعديل الحساب"])
        
        # 1. استوديو البث الواقعي
        with tab_live:
            st.write("🎙️ **اضغط على الكاميرا والمايك لبدء البث فوراً للطلاب بدون أي تعقيد:**")
            room_id = t_data[5] if t_data else f"nova_room_{st.session_state.user_email.split('@')[0]}"
            
            teacher_push_url = f"https://vdo.ninja/?push={room_id}&webcam=1"
            
            teacher_iframe = f"""
            <iframe src="{teacher_push_url}" 
                    style="height: 530px; width: 100%; border: 2px solid #a855f7; border-radius: 16px; background-color: #000;"
                    allow="camera; microphone; display-capture; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(teacher_iframe, height=545)

        # 2. رفـع الملفات من استوديو الموبايل/الكمبيوتر
        with tab_upload:
            st.write("📤 **رفع فيديو أو صورة من المعرض:**")
            post_title = st.text_input("عنوان المنشور:")
            uploaded_file = st.file_uploader("اختر ملف من استوديو الجهاز:", type=["png", "jpg", "jpeg", "mp4", "mov"])
            
            if st.button("🚀 نشر للطلاب الآن", use_container_width=True):
                if uploaded_file and post_title:
                    file_bytes = uploaded_file.read()
                    file_type = "video" if uploaded_file.type.startswith("video") else "image"
                    
                    c.execute("INSERT INTO posts (teacher_email, title, media_type, media_data) VALUES (?, ?, ?, ?)",
                              (st.session_state.user_email, post_title, file_type, file_bytes))
                    conn.commit()
                    st.success("تم النشر بنجاح!")
                    st.rerun()
                else:
                    st.error("يرجى كتابة العنوان واختيار الملف!")

        # 3. تعديل البيانات
        with tab_profile:
            with st.form("update_profile"):
                curr_name = t_data[1] if t_data else ""
                curr_sub = t_data[2] if t_data else ""
                curr_age = t_data[3] if t_data else 30
                curr_price = t_data[4] if t_data else 0.0
                
                name_in = st.text_input("الاسم الكامل:", value=curr_name)
                sub_in = st.text_input("المادة الدراسية:", value=curr_sub)
                age_in = st.number_input("العمر:", value=curr_age)
                price_in = st.number_input("سعر الدورة/الحصة:", value=curr_price)
                
                if st.form_submit_button("حفظ التغييرات"):
                    c.execute("UPDATE teachers SET name=?, subject=?, age=?, price=? WHERE email=?", 
                              (name_in, sub_in, age_in, price_in, st.session_state.user_email))
                    conn.commit()
                    st.success("تم تحديث البيانات بنجاح!")
                    st.rerun()
        conn.close()

    # ---------------- C. واجهة المطور ----------------
    elif st.session_state.user_role == "المطور التنفيذي 👑":
        st.subheader("👑 لوحة التحكم المركزية")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        st.write("📋 **سجل الأساتذة:**")
        c.execute("SELECT id, name, subject, age, price, email FROM teachers")
        st.dataframe(c.fetchall(), use_container_width=True)
        
        st.write("📋 **سجل المنشورات:**")
        c.execute("SELECT id, teacher_email, title, media_type FROM posts")
        st.dataframe(c.fetchall(), use_container_width=True)
        conn.close()

st.write("---")
st.caption("⚡ منصة نوفا التعليمية © 2026")
