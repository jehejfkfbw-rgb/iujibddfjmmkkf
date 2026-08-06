import streamlit as st
import streamlit.components.v1 as components
import sqlite3

# ==================== 1. إعداد قاعدة البيانات الجديدة (SQLite) ====================
DB_NAME = 'nova_v2.db'  # تغيير الاسم يجبر السيرفر يكريه داتا بيز جديدة بالنظام الجديد

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
    
    # جدول المدرسين والغرف
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            subject TEXT,
            price REAL,
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

    # حساب المطور التنفيذي الافتراضي
    cursor.execute("SELECT * FROM users WHERE role = 'المطور التنفيذي 👑'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password, role) VALUES ('admin@nova.com', '20101999', 'المطور التنفيذي 👑')")
    
    conn.commit()
    conn.close()

init_db()

# ==================== 2. إعدادات الصفحة والتصميم ====================
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
        padding: 24px;
        text-align: center;
        margin-bottom: 20px;
    }
    .card-icon { font-size: 42px; margin-bottom: 10px; }
    .card-title { font-size: 20px; font-weight: bold; color: #38bdf8; margin-bottom: 8px; }
    .card-desc { color: #94a3b8; font-size: 13px; }
    .teacher-card { background-color: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 20px; margin-bottom: 20px; }
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
st.caption("المنصة المترابطة للتعليم الإلكتروني - البث المباشر والحصص المسجلة")
st.write("---")

# ==================== 4. شاشة تسجيل الدخول ====================
if not st.session_state.is_logged_in:
    st.write("### ⚙️ اختر نوع الحساب للبدء:")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card-box"><div class="card-icon">👨‍🎓</div><div class="card-title">حساب طالب</div><div class="card-desc">حضور البث المباشر والمواد مجاناً</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card-box"><div class="card-icon">👨‍🏫</div><div class="card-title">حساب أستاذ</div><div class="card-desc">إدارة استوديو البث الحي والجداول</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card-box"><div class="card-icon">👑</div><div class="card-title">المطور التنفيذي</div><div class="card-desc">إدارة قاعدة البيانات الشاملة</div></div>', unsafe_allow_html=True)

    selected_role = st.radio("تأكيد صفة الدخول:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "المطور التنفيذي 👑"], horizontal=True)
    st.write("---")

    if selected_role == "طالب 👨‍🎓":
        st.subheader("👨‍🎓 دخول / تسجيل الطالب")
        with st.form("student_login_form"):
            s_email = st.text_input("البريد الإلكتروني:")
            s_pass = st.text_input("كلمة السر:", type="password")
            s_btn = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if s_btn:
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
                    st.success("تم الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("يرجى إدخال البريد الإلكتروني وكلمة السر!")

    elif selected_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 دخول الأستاذ")
        with st.form("teacher_login_form"):
            t_secret = st.text_input("كود السر الخاص بالأساتذة:", type="password")
            t_email = st.text_input("البريد الإلكتروني:")
            t_pass = st.text_input("كلمة السر:", type="password")
            login_btn = st.form_submit_button("تسجيل الدخول كـ أستاذ", use_container_width=True)
            
            if login_btn:
                if t_secret.strip() == "90100" and t_email and t_pass:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (t_email, t_pass, "أستاذ 👨‍🏫"))
                        c.execute("INSERT INTO teachers (name, subject, price, room_name) VALUES (?, ?, ?, ?)", 
                                  (t_email.split('@')[0], "مادة عامة", 0.0, f"nova_room_{t_email.split('@')[0]}"))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        pass
                    conn.close()

                    st.session_state.is_logged_in = True
                    st.session_state.user_role = "أستاذ 👨‍🏫"
                    st.session_state.user_email = t_email
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("كود السر أو البيانات غير صحيحة!")

    elif selected_role == "المطور التنفيذي 👑":
        st.subheader("👑 لوحة تحكم المطور التنفيذي")
        secret_code = st.text_input("أدخل الرقم السري للمطور التنفيذي:", type="password")
        if st.button("دخول لوحة التحكم", use_container_width=True):
            if secret_code.strip() == "20101999":
                st.session_state.is_logged_in = True
                st.session_state.user_role = "المطور التنفيذي 👑"
                st.session_state.user_email = "admin@nova.com"
                st.success("تم التحقق بنجاح!")
                st.rerun()
            else:
                st.error("الرقم السري غير صحيح!")

# ==================== 5. المحتوى الداخلي ====================
else:
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.info(f"مرحباً بك! نوع الحساب: **{st.session_state.user_role}** | البريد: ({st.session_state.user_email})")
    with top_col2:
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.is_logged_in = False
            st.session_state.user_role = None
            st.session_state.user_email = ""
            st.rerun()

    if st.session_state.user_role == "طالب 👨‍🎓":
        st.subheader("📚 قائمة المدرسين والبث المباشر (مجاناً)")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, subject, room_name FROM teachers")
        teachers = c.fetchall()
        
        if teachers:
            cols = st.columns(min(len(teachers), 2))
            for idx, teacher in enumerate(teachers):
                t_id, t_name, t_sub, room_name = teacher
                with cols[idx % 2]:
                    st.markdown('<div class="teacher-card">', unsafe_allow_html=True)
                    st.markdown(f"### 👨‍🏫 الأستاذ: {t_name}")
                    st.markdown(f"📖 **المادة:** {t_sub} | 💰 **الاشتراك:** مجاني 🎉")
                    st.write("---")
                    st.write("🗓️ **جدول المواعيد:**")
                    c.execute("SELECT day, time, topic FROM schedules WHERE teacher_id=?", (t_id,))
                    schedules = c.fetchall()
                    if schedules:
                        for s in schedules:
                            st.write(f"- **{s[0]}** الساعة **{s[1]}**: {s[2]}")
                    else:
                        st.caption("لا توجد مواعيد مضافة حالياً.")

                    st.write("🔴 **شاشة البث المباشر:**")
                    jitsi_html = f"""
                    <iframe src="https://meet.jit.si/{room_name}#config.prejoinPageEnabled=false" 
                            style="height: 380px; width: 100%; border: 1px solid #3b82f6; border-radius: 10px;"
                            allow="camera; microphone; display-capture; autoplay" allowfullscreen>
                    </iframe>
                    """
                    components.html(jitsi_html, height=390)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("لا يوجد مدرسين مسجلين في المنصة حتى الآن.")
        conn.close()

    elif st.session_state.user_role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 استوديو الأستاذ وإدارة الحصص")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        teacher_username = st.session_state.user_email.split('@')[0]
        c.execute("SELECT id, name, subject, room_name FROM teachers WHERE name=?", (teacher_username,))
        t_data = c.fetchone()
        
        tab_live, tab_schedule = st.tabs(["🎙️ استوديو البث المباشر", "📅 تنظيم المواعيد"])
        
        with tab_live:
            st.write("🔴 **شاشة البث المباشر للطلاب:**")
            room_code = t_data[3] if t_data else f"nova_room_{teacher_username}"
            jitsi_teacher_html = f"""
            <iframe src="https://meet.jit.si/{room_code}#config.prejoinPageEnabled=false" 
                    style="height: 520px; width: 100%; border: 0px; border-radius: 10px;"
                    allow="camera; microphone; display-capture; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(jitsi_teacher_html, height=540)

        with tab_schedule:
            st.write("📅 **إضافة موعد حصة جديد:**")
            if t_data:
                with st.form("add_schedule_form"):
                    day = st.selectbox("اليوم:", ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"])
                    time_val = st.text_input("الوقت (مثال: 07:00 مساءً):")
                    topic = st.text_input("موضوع الحصة:")
                    submit_sch = st.form_submit_button("حفظ الموعد في قاعدة البيانات")
                    
                    if submit_sch and time_val and topic:
                        c.execute("INSERT INTO schedules (teacher_id, day, time, topic) VALUES (?, ?, ?, ?)",
                                  (t_data[0], day, time_val, topic))
                        conn.commit()
                        st.success("تم إضافة الموعد بنجاح وسيظهر لجميع الطلاب!")
                        st.rerun()
        conn.close()

    elif st.session_state.user_role == "المطور التنفيذي 👑":
        st.subheader("👑 لوحة تحكم المطور وقواعد البيانات")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        m1, m2 = st.columns(2)
        c.execute("SELECT COUNT(*) FROM users")
        m1.metric("إجمالي الحسابات بالداتا بيز", c.fetchone()[0])
        c.execute("SELECT COUNT(*) FROM teachers")
        m2.metric("عدد المعلمين المسجلين", c.fetchone()[0])

        st.write("---")
        st.write("📋 **جدول الحسابات المسجلة (Users Database):**")
        c.execute("SELECT id, email, role FROM users")
        st.dataframe(c.fetchall(), use_container_width=True)

        st.write("📋 **جدول المدرسين والغرف (Teachers Database):**")
        c.execute("SELECT id, name, subject, room_name FROM teachers")
        st.dataframe(c.fetchall(), use_container_width=True)
        
        conn.close()

st.write("---")
st.caption("🌟 منصة نوفا التعليمية © 2026 - جميع الحقوق محفوظة")
