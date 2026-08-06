import streamlit as st
import streamlit.components.v1 as components
import sqlite3

# ==================== 1. إعداد قاعدة البيانات (SQLite) ====================
DB_NAME = 'nova_v4.db'

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
    
    # جدول المدرسين التفيصلي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            subject TEXT,
            age INTEGER,
            price REAL,
            photo_url TEXT,
            room_name TEXT
        )
    ''')
    
    # جدول مواعيد الحصص
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            day TEXT,
            time TEXT,
            topic TEXT
        )
    ''')

    # حساب المطور التنفيذي
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
    .card-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 15px;
    }
    .teacher-card {
        background-color: #1e293b;
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. إدارة الجلسة ====================
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

st.title("🌟 منصة نوفا التعليمية")
st.caption("منصة البث المباشر والحصص التفاعلية الداخلي بالكامل")
st.write("---")

# ==================== 4. شاشة اختيار الحساب والدخول ====================
if not st.session_state.is_logged_in:
    st.write("### ⚙️ اختر نوع الحساب للبدء:")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card-box"><h2>👨‍🎓</h2><h3>طالب</h3><p>تصفح الأساتذة والبث المباشر الداخلي</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card-box"><h2>👨‍🏫</h2><h3>أستاذ</h3><p>إدارة البيانات والاستوديو</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card-box"><h2>👑</h2><h3>المطور</h3><p>لوحة الإدارة والبيانات</p></div>', unsafe_allow_html=True)

    selected_role = st.radio("تأكيد الصفة:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "المطور التنفيذي 👑"], horizontal=True)
    st.write("---")

    # دخول الطالب
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

                    st.session_state.is_logged_in = True
                    st.session_state.user_role = "طالب 👨‍🎓"
                    st.session_state.user_email = s_email
                    st.rerun()

    # دخول الأستاذ
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
                        c.execute("INSERT INTO teachers (email, name, subject, age, price, photo_url, room_name) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (t_email, t_email.split('@')[0], "لم تحدد", 30, 0.0, "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", f"novalive_{t_email.split('@')[0]}"))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        pass
                    conn.close()

                    st.session_state.is_logged_in = True
                    st.session_state.user_role = "أستاذ 👨‍🏫"
                    st.session_state.user_email = t_email
                    st.rerun()
                else:
                    st.error("كود السر أو البيانات غير صحيحة!")

    # دخول المطور
    elif selected_role == "المطور التنفيذي 👑":
        secret_code = st.text_input("الرقم السري للمطور:", type="password")
        if st.button("دخول لوحة التحكم", use_container_width=True):
            if secret_code.strip() == "20101999":
                st.session_state.is_logged_in = True
                st.session_state.user_role = "المطور التنفيذي 👑"
                st.session_state.user_email = "admin@nova.com"
                st.rerun()

# ==================== 5. الواجهات الداخلية ====================
else:
    top_col, logout_col = st.columns([3, 1])
    top_col.info(f"مرحباً: **{st.session_state.user_role}** ({st.session_state.user_email})")
    if logout_col.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.is_logged_in = False
        st.rerun()

    # ---------------- A. واجهة الطالب ----------------
    if st.session_state.user_role == "طالب 👨‍🎓":
        st.subheader("📚 قائمة المدرسين والبث المباشر")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, age, price, photo_url, room_name FROM teachers")
        teachers = c.fetchall()
        
        if teachers:
            for t in teachers:
                t_id, t_name, t_sub, t_age, t_price, t_photo, room_name = t
                
                st.markdown('<div class="teacher-card">', unsafe_allow_html=True)
                col_img, col_info = st.columns([1, 4])
                
                with col_img:
                    st.image(t_photo if t_photo else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=110)
                
                with col_info:
                    st.markdown(f"## 👨‍🏫 الأستاذ: **{t_name}**")
                    st.markdown(f"📖 **المادة:** {t_sub} | 🎂 **العمر:** {t_age} سنة | 💰 **المصاريف:** {t_price} جنيه")
                
                st.write("---")
                
                # جدول المواعيد
                st.write("🗓️ **جدول المواعيد:**")
                c.execute("SELECT day, time, topic FROM schedules WHERE teacher_id=?", (t_id,))
                schedules = c.fetchall()
                if schedules:
                    for s in schedules:
                        st.write(f"- **{s[0]}** الساعة **{s[1]}**: {s[2]}")
                else:
                    st.caption("لا توجد مواعيد مضافة حالياً.")

                # البث المباشر الداخلي للـ الطالب (إلغاء صفحة فتح التطبيقات الخارجية)
                st.write("🔴 **البث المباشر (داخلي مباشرةً):**")
                
                embedded_live_code = f"""
                <iframe src="https://meet.jit.si/{room_name}#config.prejoinPageEnabled=false&config.deeplinking.disabled=true&interfaceConfig.SHOW_JITSI_WATERMARK=false" 
                        style="height: 500px; width: 100%; border: 2px solid #38bdf8; border-radius: 12px;"
                        allow="camera; microphone; display-capture; autoplay; clipboard-write" allowfullscreen>
                </iframe>
                """
                components.html(embedded_live_code, height=515)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("لا يوجد أساتذة مسجلين حالياً.")
        conn.close()

    # ---------------- B. واجهة الأستاذ ----------------
    elif st.session_state.user_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 استوديو الأستاذ")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, age, price, photo_url, room_name FROM teachers WHERE email=?", (st.session_state.user_email,))
        t_data = c.fetchone()
        
        tab_profile, tab_live, tab_sch = st.tabs(["👤 الملف الشخصي والبيانات", "🎙️ استوديو البث الحي", "📅 إضافة المواعيد"])
        
        # 1. إدخال وتعديل البيانات
        with tab_profile:
            st.write("📝 **أدخل أو عدل بياناتك لتظهر للطلاب:**")
            with st.form("update_profile"):
                curr_name = t_data[1] if t_data else ""
                curr_sub = t_data[2] if t_data else ""
                curr_age = t_data[3] if t_data else 30
                curr_price = t_data[4] if t_data else 0.0
                curr_photo = t_data[5] if t_data else ""
                
                name_in = st.text_input("الاسم الكامل:", value=curr_name)
                sub_in = st.text_input("المادة الدراسية:", value=curr_sub)
                age_in = st.number_input("العمر:", value=curr_age, min_value=18, max_value=80)
                price_in = st.number_input("المصاريف (بالجنيه):", value=curr_price)
                photo_in = st.text_input("رابط الصورة الشخصية (URL):", value=curr_photo)
                
                if st.form_submit_button("حفظ البيانات"):
                    c.execute("""
                        UPDATE teachers 
                        SET name=?, subject=?, age=?, price=?, photo_url=? 
                        WHERE email=?
                    """, (name_in, sub_in, age_in, price_in, photo_in, st.session_state.user_email))
                    conn.commit()
                    st.success("تم تحديث بياناتك بنجاح!")
                    st.rerun()

        # 2. البث المباشر للأستاذ (داخلي)
        with tab_live:
            st.write("🔴 **شاشة استوديو البث (تفتح الكاميرا والمايك داخل الموقع):**")
            room_code = t_data[6] if t_data else f"novalive_{st.session_state.user_email.split('@')[0]}"
            
            teacher_embedded_code = f"""
            <iframe src="https://meet.jit.si/{room_code}#config.prejoinPageEnabled=false&config.deeplinking.disabled=true" 
                    style="height: 520px; width: 100%; border: 0px; border-radius: 12px;"
                    allow="camera; microphone; display-capture; autoplay; clipboard-write" allowfullscreen>
            </iframe>
            """
            components.html(teacher_embedded_code, height=535)

        # 3. جدول المواعيد
        with tab_sch:
            st.write("📅 **إضافة موعد حصة جديد:**")
            if t_data:
                with st.form("add_schedule"):
                    day = st.selectbox("اليوم:", ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"])
                    time_val = st.text_input("الوقت (مثال: 08:00 مساءً):")
                    topic = st.text_input("عنوان الحصة:")
                    if st.form_submit_button("حفظ الموعد"):
                        c.execute("INSERT INTO schedules (teacher_id, day, time, topic) VALUES (?, ?, ?, ?)",
                                  (t_data[0], day, time_val, topic))
                        conn.commit()
                        st.success("تم إضافة الموعد!")
                        st.rerun()
        conn.close()

    # ---------------- C. واجهة المطور ----------------
    elif st.session_state.user_role == "المطور التنفيذي 👑":
        st.subheader("👑 لوحة تحكم المطور وقاعدة البيانات")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        st.write("📋 **جدول الأساتذة المسجلين بكافة التفاصيل:**")
        c.execute("SELECT id, name, subject, age, price, photo_url FROM teachers")
        st.dataframe(c.fetchall(), use_container_width=True)
        
        st.write("📋 **جدول الحسابات (Users):**")
        c.execute("SELECT id, email, role FROM users")
        st.dataframe(c.fetchall(), use_container_width=True)
        conn.close()

st.write("---")
st.caption("🌟 منصة نوفا التعليمية © 2026")
