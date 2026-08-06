import streamlit as st
import streamlit.components.v1 as components
import sqlite3
from datetime import datetime

# ==================== 1. إعداد قاعدة البيانات (SQLite) ====================
def init_db():
    conn = sqlite3.connect('nova_platform.db')
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    # جدول المدرسين
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

    # إضافة المطور الافتراضي لو مش موجود
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', '20101999', 'المطور')")
    
    conn.commit()
    conn.close()

init_db()

# ==================== 2. إعدادات الصفحة والتصميم ====================
st.set_page_config(
    page_title="منصة نوفا التعليمية",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; background-color: #0e1117; }
    .card { background-color: #1f2937; border-radius: 12px; padding: 20px; margin-bottom: 15px; border: 1px solid #374151; }
    .main-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ==================== 3. إدارة الجلسة (Session) ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# ==================== 4. شاشة تسجيل الدخول الموحدة ====================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><h1 style='text-align: center; color: #60a5fa;'>🎓 منصة نوفا</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب طالب جديد"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("اسم المستخدم:")
                password = st.text_input("كلمة السر:", type="password")
                submit = st.form_submit_button("دخول", use_container_width=True)
                
                if submit:
                    conn = sqlite3.connect('nova_platform.db')
                    c = conn.cursor()
                    c.execute("SELECT username, role FROM users WHERE username=? AND password=?", (username, password))
                    user = c.fetchone()
                    conn.close()
                    
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_data = {"username": user[0], "role": user[1]}
                        st.success("تم تسجيل الدخول!")
                        st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة!")

        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("اختر اسم مستخدم:")
                new_pass = st.text_input("اختر كلمة السر:", type="password")
                role_choice = st.selectbox("نوع الحساب:", ["طالب", "أستاذ"])
                reg_submit = st.form_submit_button("إنشاء الحساب", use_container_width=True)
                
                if reg_submit and new_user and new_pass:
                    conn = sqlite3.connect('nova_platform.db')
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (new_user, new_pass, role_choice))
                        if role_choice == "أستاذ":
                            c.execute("INSERT INTO teachers (name, subject, price, room_name) VALUES (?, ?, ?, ?)", 
                                      (new_user, "مادة عامة", 0.0, f"nova_room_{new_user}"))
                        conn.commit()
                        st.success("تم إنشاء الحساب بنجاح! يمكنك الدخول الآن.")
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم موجود بالفعل!")
                    finally:
                        conn.close()

# ==================== 5. لوحات التحكم الداخلي ====================
else:
    user = st.session_state.user_data

    # القائمة الجانبية
    with st.sidebar:
        st.write(f"👤 مرحباً بك: **{user['username']}**")
        st.write(f"الرتبة: **{user['role']}**")
        st.markdown("---")
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.rerun()

    st.markdown(f'<div class="main-header"><h2>🚀 لوحة تحكم منصة نوفا ({user["role"]})</h2></div>', unsafe_allow_html=True)

    # ---------------- A. واجهة الطالب ----------------
    if user["role"] == "طالب":
        st.subheader("📚 المدرسون والحصص المتاحة (مجاناً)")
        
        conn = sqlite3.connect('nova_platform.db')
        c = conn.cursor()
        c.execute("SELECT id, name, subject, room_name FROM teachers")
        teachers = c.fetchall()
        
        for t in teachers:
            t_id, t_name, t_sub, room_name = t
            with st.expander(f"👨‍🏫 الأستاذ: {t_name} - مادة: {t_sub} (مجاني 🎉)"):
                st.write("🗓️ **جدول المواعيد:**")
                c.execute("SELECT day, time, topic FROM schedules WHERE teacher_id=?", (t_id,))
                schedules = c.fetchall()
                if schedules:
                    for s in schedules:
                        st.write(f"- **{s[0]}** الساعة **{s[1]}** | الموضوع: {s[2]}")
                else:
                    st.caption("لا توجد مواعيد مجدولة حالياً.")

                st.write("🔴 **البث المباشر:**")
                jitsi_html = f"""
                <iframe src="https://meet.jit.si/{room_name}#config.prejoinPageEnabled=false" 
                        style="height: 380px; width: 100%; border-radius: 10px; border: 1px solid #374151;"
                        allow="camera; microphone; display-capture; autoplay" allowfullscreen>
                </iframe>
                """
                components.html(jitsi_html, height=400)
        conn.close()

    # ---------------- B. واجهة الأستاذ ----------------
    elif user["role"] == "أستاذ":
        conn = sqlite3.connect('nova_platform.db')
        c = conn.cursor()
        c.execute("SELECT id, name, subject, room_name FROM teachers WHERE name=?", (user["username"],))
        t_data = c.fetchone()
        
        if t_data:
            t_id, t_name, t_sub, room_name = t_data
            
            tab_live, tab_schedule = st.tabs(["🔴 استوديو البث المباشر", "📅 إدارة مواعيد الحصص"])
            
            with tab_live:
                st.subheader("🎥 استوديو البث الحي")
                st.info("الاشتراك حالياً مجاني لجميع الطلاب الانضمام للغرفة مباشرة.")
                jitsi_html = f"""
                <iframe src="https://meet.jit.si/{room_name}#config.prejoinPageEnabled=false" 
                        style="height: 500px; width: 100%; border-radius: 10px; border: 0;"
                        allow="camera; microphone; display-capture; autoplay" allowfullscreen>
                </iframe>
                """
                components.html(jitsi_html, height=520)

            with tab_schedule:
                st.subheader("➕ إضافة موعد حصة جديد")
                with st.form("add_schedule"):
                    day = st.selectbox("اليوم:", ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"])
                    time_val = st.text_input("الوقت (مثال: 06:00 مساءً):")
                    topic = st.text_input("عنوان الحصة/الموضوع:")
                    sub_sch = st.form_submit_button("حفظ الموعد")
                    
                    if sub_sch and time_val and topic:
                        c.execute("INSERT INTO schedules (teacher_id, day, time, topic) VALUES (?, ?, ?, ?)",
                                  (t_id, day, time_val, topic))
                        conn.commit()
                        st.success("تم إضافة الموعد للطلاب بنجاح!")
                        st.rerun()
        conn.close()

    # ---------------- C. واجهة المطور (Admin Dashboard) ----------------
    elif user["role"] == "المطور":
        st.subheader("👑 لوحة تحكم المطور وقاعدة البيانات الشاملة")
        
        conn = sqlite3.connect('nova_platform.db')
        c = conn.cursor()
        
        col_m1, col_m2 = st.columns(2)
        c.execute("SELECT COUNT(*) FROM users")
        col_m1.metric("إجمالي الحسابات المسجلة", c.fetchone()[0])
        
        c.execute("SELECT COUNT(*) FROM teachers")
        col_m2.metric("عدد المعلمين", c.fetchone()[0])
        
        st.markdown("---")
        st.write("📋 **جدول الحسابات في الداتا بيز (Users Table):**")
        c.execute("SELECT id, username, role FROM users")
        st.dataframe(c.fetchall(), column_config={"0": "ID", "1": "اسم المستخدم", "2": "الرتبة"}, use_container_width=True)
        
        st.write("📋 **جدول المدرسين الغرف (Teachers Table):**")
        c.execute("SELECT id, name, subject, room_name FROM teachers")
        st.dataframe(c.fetchall(), use_container_width=True)
        
        conn.close()

st.markdown("<br><hr><center style='color:#6b7280;'>🌟 منصة نوفا التعليمية © 2026</center>", unsafe_allow_html=True)
