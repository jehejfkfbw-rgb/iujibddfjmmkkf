import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components

# إعداد المجلدات والملفات لضمان استقرار البيانات
MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

# قاعدة بيانات واحدة مركزية لحفظ كل شيء
DB_NAME = 'nova_core_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # جدول المستخدمين الشامل
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            name TEXT,
            age TEXT,
            grade TEXT,
            role TEXT,
            is_blocked INTEGER DEFAULT 0
        )
    ''')
    # جدول الأساتذة وتفاصيلهم
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            name TEXT,
            subject TEXT,
            grade_level TEXT,
            age INTEGER,
            price REAL,
            image_url TEXT,
            room_id TEXT
        )
    ''')
    # جدول الاشتراكات (علاقة الطلاب بالأساتذة)
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_phone TEXT,
            teacher_phone TEXT,
            status TEXT DEFAULT 'pending',
            UNIQUE(student_phone, teacher_phone)
        )
    ''')
    # جدول المحتوى والمنشورات
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_phone TEXT,
            title TEXT,
            media_type TEXT,
            file_path TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# إخفاء كامل لواجهة ستريملت وتصميم تطبيق احترافي
st.set_page_config(page_title="نوفا التعليمية", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
    #MainMenu, footer, header, .stDeployButton {display: none !important;}
    .stApp {direction: rtl; text-align: right; background-color: #f1f5f9 !important;}
    .card {background: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px;}
    .stButton>button {width: 100%; border-radius: 10px; background: #2563eb !important; color: white !important;}
</style>
""", unsafe_allow_html=True)

# استرجاع حالة الجلسة
if "user_phone" not in st.session_state:
    st.session_state.user_phone = None

st.title("⚡ منصة نوفا التعليمية")

# منطق تسجيل الدخول المستمر (بدون تكرار)
if not st.session_state.user_phone:
    choice = st.radio("دخول إلى:", ["طالب", "أستاذ", "مطور"])
    
    if choice == "طالب":
        with st.form("st_form"):
            ph = st.text_input("رقم التليفون:")
            nm = st.text_input("الاسم:")
            if st.form_submit_button("دخول"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO users (phone, name, role) VALUES (?, ?, 'طالب')", (ph, nm))
                conn.commit()
                conn.close()
                st.session_state.user_phone = ph
                st.rerun()

    elif choice == "أستاذ":
        with st.form("t_form"):
            ph = st.text_input("رقم التليفون:")
            code = st.text_input("الكود السري:", type="password")
            if st.form_submit_button("دخول"):
                # الكود المخزن في البيئة الآمنة
                if code == st.secrets.get("TEACHER_SECRET", "90100"):
                    st.session_state.user_phone = ph
                    st.session_state.user_role = "أستاذ"
                    st.rerun()

else:
    # المنطقة المحمية (بمجرد الدخول، البيانات محفوظة)
    st.write(f"أهلاً بك: {st.session_state.user_phone}")
    if st.button("خروج"):
        st.session_state.user_phone = None
        st.rerun()
    
    # هنا يتم عرض المحتوى بناءً على البيانات المحفوظة في قاعدة البيانات
    # أي إضافة أو تعديل هنا سيتم حفظه مباشرة في nova_core_database.db

st.caption("نظام حفظ البيانات دائم - منصة نوفا")
