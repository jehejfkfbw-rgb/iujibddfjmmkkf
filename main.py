import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import base64

# ==================== 1. إعداد قاعدة البيانات ====================
DB_NAME = 'nova_v6.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول الحسابات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    # جدول المدرسين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            subject TEXT,
            age INTEGER,
            price REAL,
            room_name TEXT
        )
    ''')
    
    # جدول منشورات المدرسين (فيديوهات وصور من الاستوديو)
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

# ==================== 2. التصميم وإعدادات الصفحة ====================
st.set_page_config(
    page_title="منصة نوفا التعليمية",
    page_icon="🌟",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #0f172a; color: #f8fafc; }
    .teacher-card {
        background-color: #1e293b;
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 25px;
    }
    .post-card {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. الجلسة والدخول الدائم ====================
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

st.title("🌟 منصة نوفا التعليمية")
st.caption("البث المباشر، الفيديوهات، والمنشورات التفاعلية")
st.write("---")

# ==================== 4. تسجيل الدخول ====================
if not st.session_state.is_logged_in:
    selected_role = st.radio("اختر نوع الحساب للدخول:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "المطور التنفيذي 👑"], horizontal=True)
    st.write("---")

    if selected_role == "طالب 👨‍🎓":
        st.subheader("👨‍🎓 دخول الطالب")
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
        st.subheader("👨‍🏫 دخول الأستاذ")
        with st.form("teacher_form"):
            t_secret = st.text_input("كود السر الخاص بالأساتذة:", type="password")
            t_email = st.text_input("البريد الإلكتروني:")
            t_pass = st.text_input("كلمة السر:", type="password")
            if st.form_submit_button("دخول الأستاذ", use_container_width=True):
                if t_secret.strip() == "90100" and t_email and t_pass:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (t_email, t_pass, "أستاذ 👨‍🏫"))
                        c.execute("INSERT INTO teachers (email, name, subject, age, price, room_name) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (t_email, t_email.split('@')[0], "لم تحدد", 30, 0.0, f"novalive_{t_email.split('@')[0]}"))
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

# ==================== 5. الواجهات الداخلية ====================
else:
    top_col, logout_col = st.columns([3, 1])
    top_col.info(f"مرحباً: **{st.session_state.user_role}** ({st.session_state.user_email})")
    if logout_col.button("🚪 تسجيل الخروج", use_container_width=True):
        logout()
        st.rerun()

    # ---------------- A. واجهة الطالب ----------------
    if st.session_state.user_role == "طالب 👨‍🎓":
        st.subheader("📚 البحث عن الأساتذة ومتابعة الدروس")
        
        # شريط البحث عن الأساتذة
        search_query = st.text_input("🔍 ابحث عن أستاذ بـ اسمه أو المادة الدراسية:", "")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        if search_query:
            c.execute("SELECT id, name, subject, age, price, room_name, email FROM teachers WHERE name LIKE ? OR subject LIKE ?", 
                      (f"%{search_query}%", f"%{search_query}%"))
        else:
            c.execute("SELECT id, name, subject, age, price, room_name, email FROM teachers")
            
        teachers = c.fetchall()
        
        if teachers:
            for t in teachers:
                t_id, t_name, t_sub, t_age, t_price, room_name, t_email = t
                
                st.markdown('<div class="teacher-card">', unsafe_allow_html=True)
                st.markdown(f"## 👨‍🏫 الأستاذ: **{t_name}**")
                st.markdown(f"📖 **المادة:** {t_sub} | 🎂 **العمر:** {t_age} سنة | 💰 **المصاريف:** {t_price} جنيه")
                st.write("---")
                
                # عرض البث المباشر المباشر
                st.write("🔴 **شاشة البث المباشر للأستاذ:**")
                embedded_live_code = f"""
                <iframe src="https://meet.jit.si/{room_name}#config.prejoinPageEnabled=false&config.deeplinking.disabled=true" 
                        style="height: 480px; width: 100%; border: 2px solid #38bdf8; border-radius: 12px;"
                        allow="camera; microphone; display-capture; autoplay" allowfullscreen>
                </iframe>
                """
                components.html(embedded_live_code, height=495)

                # عرض فيديوهات وصور الأستاذ المرفوعة من الاستوديو
                st.write("🎬 **فيديوهات وصور الأستاذ (من الاستوديو):**")
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
                    st.caption("لم ينشر الأستاذ أي صور أو فيديوهات بعد.")

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("لم يتم العثور على أي أستاذ يطابق بحثك.")
        conn.close()

    # ---------------- B. واجهة الأستاذ ----------------
    elif st.session_state.user_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 استوديو الأستاذ")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, age, price, room_name FROM teachers WHERE email=?", (st.session_state.user_email,))
        t_data = c.fetchone()
        
        tab_live, tab_upload, tab_profile = st.tabs(["🎙️ بدء البث المباشر", "📤 نشر صور/فيديوهات من الاستوديو", "👤 تعديل البيانات"])
        
        # 1. شاشة البث المباشر المحدثة
        with tab_live:
            st.write("🔴 **اضغط لبدء البث المباشر فوراً (ستظهر الكاميرا للطلاب مباشرةً):**")
            room_code = t_data[5] if t_data else f"novalive_{st.session_state.user_email.split('@')[0]}"
            
            teacher_live = f"""
            <iframe src="https://meet.jit.si/{room_code}#config.prejoinPageEnabled=false&config.deeplinking.disabled=true" 
                    style="height: 520px; width: 100%; border: 0px; border-radius: 12px;"
                    allow="camera; microphone; display-capture; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(teacher_live, height=535)

        # 2. نشر فيديوهات وصور من معرض الصور بالموبايل/الكمبيوتر
        with tab_upload:
            st.write("📤 **اختر صورة أو فيديو من الاستوديو لنشره للطلاب:**")
            post_title = st.text_input("عنوان الفيديو أو الصورة:")
            uploaded_file = st.file_uploader("اختر ملف من معرض الصور/الاستوديو:", type=["png", "jpg", "jpeg", "mp4", "mov", "avi"])
            
            if st.button("🚀 نشر الآن للطلاب", use_container_width=True):
                if uploaded_file and post_title:
                    file_bytes = uploaded_file.read()
                    file_type = "video" if uploaded_file.type.startswith("video") else "image"
                    
                    c.execute("INSERT INTO posts (teacher_email, title, media_type, media_data) VALUES (?, ?, ?, ?)",
                              (st.session_state.user_email, post_title, file_type, file_bytes))
                    conn.commit()
                    st.success("تم نشر الملف بنجاح وظهر في صفحتك للطلاب!")
                    st.rerun()
                else:
                    st.error("يرجى كتابة عنوان وتحديد ملف من الاستوديو!")

        # 3. تعديل بيانات الأستاذ
        with tab_profile:
            st.write("📝 **تعديل البيانات الشخصية:**")
            with st.form("update_profile"):
                curr_name = t_data[1] if t_data else ""
                curr_sub = t_data[2] if t_data else ""
                curr_age = t_data[3] if t_data else 30
                curr_price = t_data[4] if t_data else 0.0
                
                name_in = st.text_input("الاسم الكامل:", value=curr_name)
                sub_in = st.text_input("المادة الدراسية:", value=curr_sub)
                age_in = st.number_input("العمر:", value=curr_age, min_value=18, max_value=80)
                price_in = st.number_input("المصاريف (بالجنيه):", value=curr_price)
                
                if st.form_submit_button("حفظ البيانات"):
                    c.execute("UPDATE teachers SET name=?, subject=?, age=?, price=? WHERE email=?", 
                              (name_in, sub_in, age_in, price_in, st.session_state.user_email))
                    conn.commit()
                    st.success("تم حفظ البيانات!")
                    st.rerun()
        conn.close()

    # ---------------- C. واجهة المطور ----------------
    elif st.session_state.user_role == "المطور التنفيذي 👑":
        st.subheader("👑 لوحة تحكم المطور")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        st.write("📋 **الأساتذة المسجلين:**")
        c.execute("SELECT id, name, subject, age, price, email FROM teachers")
        st.dataframe(c.fetchall(), use_container_width=True)
        
        st.write("📋 **المنشورات والفيديوهات المرفوعة:**")
        c.execute("SELECT id, teacher_email, title, media_type FROM posts")
        st.dataframe(c.fetchall(), use_container_width=True)
        conn.close()

st.write("---")
st.caption("🌟 منصة نوفا التعليمية © 2026")
