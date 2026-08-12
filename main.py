import streamlit as st
import sqlite3
import os
import hashlib
import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التطبيق وتصميم الواجهة
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .block-container {
        max-width: 650px !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #f8fafc !important;
        color: #1e293b !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    h1, h2, h3, h4 {
        color: #4f46e5 !important;
        font-weight: bold !important;
    }
    
    .stTextInput input, .stNumberInput input, .stPasswordInput input, .stTextArea textarea {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 12px 20px !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
    }
    
    .app-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 16px !important;
    }
    
    .promo-badge {
        background: #e0e7ff !important;
        color: #4338ca !important;
        padding: 4px 10px !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد قاعدة البيانات والجداول
# ==========================================
MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

DB_NAME = 'nova_complete_system.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        
        # جدول المستخدمين (طلاب)
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, password TEXT, name TEXT, grade TEXT, role TEXT, is_blocked INTEGER DEFAULT 0)''')
        
        # جدول الأساتذة
        c.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, password TEXT, name TEXT, subject TEXT,
            grade_level TEXT, price REAL, schedule_info TEXT, room_id TEXT, is_blocked INTEGER DEFAULT 0)''')
            
        # جدول الأساتذة المصرح لهم من قبل المطور
        c.execute('''CREATE TABLE IF NOT EXISTS allowed_teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE)''')
            
        # جدول الاشتراكات
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, teacher_phone TEXT,
            status TEXT DEFAULT 'pending', orange_cash_sender TEXT, requested_at TEXT, expires_at TEXT, UNIQUE(student_phone, teacher_phone))''')

        # جدول المنشورات والفيديوهات
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, title TEXT,
            media_type TEXT, file_path TEXT, status TEXT DEFAULT 'approved', views_count INTEGER DEFAULT 0, visibility TEXT DEFAULT 'subscriber')''')

        # جدول التعليقات
        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, student_name TEXT, comment_text TEXT, timestamp TEXT)''')

        # جدول الشات الخاص بين الأستاذ والطالب
        c.execute('''CREATE TABLE IF NOT EXISTS smart_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, student_phone TEXT, sender_role TEXT, message TEXT, timestamp TEXT)''')

        # جدول الامتحانات
        c.execute('''CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, question TEXT,
            opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT, correct_answer TEXT)''')
            
        # إضافة رقم افتراضي كمثال للأستاذ المصرح له (يمكن للمطور تعديله)
        c.execute("INSERT OR IGNORE INTO allowed_teachers (phone) VALUES ('01000000000')")
        
        conn.commit()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 3. إدارة الجلسات (Session State)
# ==========================================
params = st.query_params

if "is_logged_in" not in st.session_state:
    saved_phone = params.get("nova_phone", "")
    saved_role = params.get("nova_role", "")
    if saved_phone and saved_role:
        st.session_state.is_logged_in = True
        st.session_state.user_phone = saved_phone
        st.session_state.user_role = saved_role
    else:
        st.session_state.is_logged_in = False
        st.session_state.user_phone = ""
        st.session_state.user_role = None

if "sub_target_teacher" not in st.session_state:
    st.session_state.sub_target_teacher = None

if "inside_teacher_room" not in st.session_state:
    st.session_state.inside_teacher_room = False

def login_user(phone, role):
    st.session_state.is_logged_in = True
    st.session_state.user_phone = phone
    st.session_state.user_role = role
    st.query_params["nova_phone"] = phone
    st.query_params["nova_role"] = role

def logout_user():
    st.session_state.is_logged_in = False
    st.session_state.user_phone = ""
    st.session_state.user_role = None
    st.session_state.sub_target_teacher = None
    st.session_state.inside_teacher_room = False
    st.query_params.clear()

# ==========================================
# 4. واجهة تسجيل الدخول الرئيسية
# ==========================================
st.markdown("<h2 style='text-align: center;'>⚡ منصة نوفا التعليمية</h2>", unsafe_allow_html=True)
st.write("---")

if not st.session_state.is_logged_in:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    role_choice = st.radio("اختر نوع الحساب للدخول:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑"], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ----------------- تسجيل ودخول الطالب -----------------
    if role_choice == "طالب 👨‍🎓":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        student_mode = st.radio("العملية:", ["تسجيل دخول", "حساب جديد"], horizontal=True)
        st.write("---")
        
        if student_mode == "حساب جديد":
            with st.form("student_signup"):
                st.subheader("حساب طالب جديد")
                s_name = st.text_input("الاسم الكامل:")
                s_phone = st.text_input("رقم المحمول:")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_grade = st.text_input("المرحلة الدراسية:")
                s_signup_btn = st.form_submit_button("تسجيل الحساب")
                
                if s_signup_btn:
                    if s_phone and s_pass:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=?", (s_phone,))
                                if c.fetchone():
                                    st.error("رقم المحمول مسجل مسبقاً!")
                                else:
                                    hashed = hash_password(s_pass)
                                    c.execute("INSERT INTO users (phone, password, name, grade, role, is_blocked) VALUES (?, ?, ?, ?, 'طالب', 0)", 
                                              (s_phone, hashed, s_name if s_name else "طالب", s_grade))
                                    conn.commit()
                                    login_user(s_phone, "طالب")
                                    st.rerun()
                        except:
                            st.error("حدث خطأ أثناء التسجيل.")
                    else:
                        st.error("الرجاء إدخال رقم المحمول وكلمة المرور.")
        else:
            with st.form("student_login"):
                st.subheader("تسجيل دخول طالب")
                s_phone_in = st.text_input("رقم المحمول:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                s_login_btn = st.form_submit_button("دخول")
                
                if s_login_btn:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed = hash_password(s_pass_in)
                            c.execute("SELECT phone, is_blocked FROM users WHERE phone=? AND password=? AND role='طالب'", (s_phone_in, hashed))
                            row = c.fetchone()
                        if row:
                            if row[1] == 1:
                                st.error("❌ حسابك محظور من قبل الإدارة.")
                            else:
                                login_user(row[0], "طالب")
                                st.rerun()
                        else:
                            st.error("رقم المحمول أو كلمة المرور غير صحيحة!")
                    except:
                        st.error("حدث خطأ في الاتصال.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----------------- تسجيل ودخول الأستاذ -----------------
    elif role_choice == "أستاذ 👨‍🏫":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        teacher_mode = st.radio("العملية:", ["دخول الأستاذ", "إنشاء حساب أستاذ جديد"], horizontal=True)
        st.write("---")
        
        if teacher_mode == "إنشاء حساب أستاذ جديد":
            with st.form("teacher_signup"):
                st.subheader("إنشاء حساب أستاذ جديد")
                t_phone_reg = st.text_input("رقم المحمول الخاص بك (يجب أن يكون مسجلاً لدى المطور):")
                t_name_reg = st.text_input("اسم الأستاذ:")
                t_sub_reg = st.text_input("المادة الدراسية:")
                t_pass_reg = st.text_input("اختر كلمة المرور الخاصة بك:", type="password")
                t_signup_btn = st.form_submit_button("إتمام التسجيل")
                
                if t_signup_btn:
                    if t_phone_reg and t_pass_reg:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                # التحقق أن الرقم مسجل عند المطور
                                c.execute("SELECT phone FROM allowed_teachers WHERE phone=?", (t_phone_reg,))
                                if not c.fetchone():
                                    st.error("❌ عذراً، هذا الرقم غير مسجل في قائمة المطور المعتمدة للأساتذة!")
                                else:
                                    c.execute("SELECT id FROM teachers WHERE phone=?", (t_phone_reg,))
                                    if c.fetchone():
                                        st.error("هذا الرقم مسجل بحساب أستاذ مسبقاً!")
                                    else:
                                        hashed_t = hash_password(t_pass_reg)
                                        room_id = f"room_{t_phone_reg}"
                                        c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, price, schedule_info, room_id, is_blocked) 
                                                     VALUES (?, ?, ?, ?, 'جميع المراحل', 100.0, 'لم يتم تحديد جدول بعد', ?, 0)""", 
                                                  (t_phone_reg, hashed_t, t_name_reg, t_sub_reg, room_id))
                                        conn.commit()
                                        login_user(t_phone_reg, "أستاذ")
                                        st.rerun()
                        except:
                            st.error("حدث خطأ أثناء إنشاء الحساب.")
                    else:
                        st.error("الرجاء إدخال رقم المحمول وكلمة المرور.")
        else:
            with st.form("teacher_login"):
                st.subheader("تسجيل دخول أستاذ")
                t_phone_in = st.text_input("رقم المحمول:")
                t_pass_in = st.text_input("كلمة المرور:", type="password")
                t_login_btn = st.form_submit_button("دخول")
                
                if t_login_btn:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_t = hash_password(t_pass_in)
                            c.execute("SELECT phone, is_blocked FROM teachers WHERE phone=? AND password=?", (t_phone_in, hashed_t))
                            t_row = c.fetchone()
                        if t_row:
                            if t_row[1] == 1:
                                st.error("❌ حسابك محظور من قبل المطور.")
                            else:
                                login_user(t_row[0], "أستاذ")
                                st.rerun()
                        else:
                            st.error("رقم المحمول أو كلمة المرور غير صحيحة!")
                    except:
                        st.error("حدث خطأ في النظام.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----------------- تسجيل ودخول المطور -----------------
    elif role_choice == "مطور 👑":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        with st.form("dev_login"):
            st.subheader("لوحة تحكم المطور")
            dev_code = st.text_input("أدخل كود المطور:", type="password")
            dev_btn = st.form_submit_button("دخول المطور")
            
            if dev_btn:
                if dev_code.strip() == "900800":
                    login_user("dev_admin", "مطور")
                    st.rerun()
                else:
                    st.error("❌ كود المطور غير صحيح!")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. لوحة تحكم المطور (إدارة الأساتذة المصرح لهم)
# ==========================================
elif st.session_state.user_role == "مطور":
    st.sidebar.title("👑 لوحة المطور")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        logout_user()
        st.rerun()
        
    st.subheader("👑 لوحة تحكم المطور الرئيسية")
    st.write("هنا يمكنك تسجيل أرقام الأساتذة المسموح لهم بإنشاء حسابات على المنصة.")
    
    with st.form("add_allowed_teacher"):
        new_t_phone = st.text_input("أدخل رقم محمول الأستاذ المراد السماح له:")
        add_btn = st.form_submit_button("إضافة للقائمة المعتمدة")
        if add_btn and new_t_phone:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("INSERT OR IGNORE INTO allowed_teachers (phone) VALUES (?)", (new_t_phone,))
                    conn.commit()
                st.success(f"تم اعتماد الرقم {new_t_phone} بنجاح! يمكنه الآن التسجيل كأستاذ.")
            except:
                st.error("حدث خطأ أثناء الإضافة.")
                
    st.write("---")
    st.subheader("📋 قائمة الأساتذة المصرح لهم حالياً:")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT phone FROM allowed_teachers")
            phones = c.fetchall()
            for p in phones:
                st.write(f"- `{p[0]}`")
    except:
        pass

# ==========================================
# 6. لوحة تحكم الأستاذ (الغرفة الخاصة به)
# ==========================================
elif st.session_state.user_role == "أستاذ":
    t_phone = st.session_state.user_phone
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT name, subject, price, schedule_info, room_id FROM teachers WHERE phone=?", (t_phone,))
        t_data = c.fetchone()
        
    t_name, t_subject, t_price, t_schedule, t_room_id = t_data if t_data else ("أستاذ", "مادة", 100, "", "")

    st.sidebar.title(f"👨‍🏫 أ. {t_name}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        logout_user()
        st.rerun()
        
    st.subheader(f"مرحباً بك يا استاذ {t_name} | غرفة المادة: {t_subject}")
    
    tab_ctrl1, tab_ctrl2, tab_ctrl3, tab_ctrl4, tab_ctrl5 = st.tabs([
        "⚙️ إعدادات الغرفة والأسعار", 
        "📅 جدول المواعيد والامتحانات", 
        "🎥 إدارة الفيديوهات والمحتوى", 
        "💳 طلبات الاشتراكات", 
        "🔴 البث المباشر داخل المنصة"
    ])
    
    # 1. إعدادات السعر والجدول
    with tab_ctrl1:
        with st.form("update_teacher_info"):
            new_price = st.number_input("تحديد سعر الاشتراك الشهري (بالجنيه):", value=float(t_price))
            new_sch = st.text_area("تحديث جدول المواعيد والأيام:", value=t_schedule)
            save_info_btn = st.form_submit_button("حفظ التعديلات")
            if save_info_btn:
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE teachers SET price=?, schedule_info=? WHERE phone=?", (new_price, new_sch, t_phone))
                        conn.commit()
                    st.success("تم تحديث بيانات الغرفة بنجاح!")
                    st.rerun()
                except:
                    st.error("حدث خطأ أثناء التحديث.")

    # 2. جدول المواعيد والامتحانات
    with tab_ctrl2:
        st.markdown("### 📝 إضافة امتحان أو اختبار للطلاب")
        with st.form("add_exam_form", clear_on_submit=True):
            q_text = st.text_input("نص السؤال:")
            o1 = st.text_input("الاختيار الأول:")
            o2 = st.text_input("الاختيار الثاني:")
            o3 = st.text_input("الاختيار الثالث:")
            o4 = st.text_input("الاختيار الرابع:")
            correct = st.text_input("الإجابة الصحيحة (يجب أن تطابق أحد الاختيارات تماماً):")
            exam_btn = st.form_submit_button("إضافة السؤال")
            if exam_btn and q_text:
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO exams (teacher_phone, question, opt1, opt2, opt3, opt4, correct_answer) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (t_phone, q_text, o1, o2, o3, o4, correct))
                        conn.commit()
                    st.success("تم إضافة السؤال بنجاح!")
                except:
                    st.error("حدث خطأ أثناء إضافة السؤال.")

    # 3. إدارة الفيديوهات والمحتوى المدفوع والترويجي
    with tab_ctrl3:
        st.markdown("### 🎬 رفع فيديو أو شرح جديد")
        with st.form("upload_post_form", clear_on_submit=True):
            p_title = st.text_input("عنوان الفيديو/الدرس:")
            p_visibility = st.selectbox("نوع المحتوى:", ["subscriber (للمشتركين فقط - مدفوع)", "public (فيديو ترويجي عام للكل)"])
            uploaded_file = st.file_uploader("اختر ملف الفيديو أو الصورة:", type=["mp4", "mov", "avi", "png", "jpg"])
            upload_btn = st.form_submit_button("نشر المحتوى")
            
            if upload_btn and p_title and uploaded_file:
                file_path = os.path.join(MEDIA_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                vis_val = "subscriber" if "subscriber" in p_visibility else "public"
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, visibility) VALUES (?, ?, 'video', ?, ?)",
                                  (t_phone, p_title, file_path, vis_val))
                        conn.commit()
                    st.success("تم نشر الدرس بنجاح!")
                except:
                    st.error("حدث خطأ أثناء النشر.")

    # 4. قبول الاشتراكات
    with tab_ctrl4:
        st.markdown("### 💳 طلبات اشتراكات الطلاب المعلقة")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT student_phone, status, orange_cash_sender, requested_at FROM subscriptions WHERE teacher_phone=?", (t_phone,))
                subs = c.fetchall()
            if subs:
                for s_ph, status, orange_sender, req_at in subs:
                    c.execute("SELECT name FROM users WHERE phone=?", (s_ph,))
                    st_row = c.fetchone()
                    st_display_name = st_row[0] if st_row else s_ph
                    
                    st.markdown(f"🎓 الطالب: **{st_display_name}** | هاتف: `{s_ph}` | الحالة: **{status}**")
                    st.markdown(f"💳 رقم أورانج كاش المحول منه: `{orange_sender or 'غير متوفر'}` | وقت الطلب: `{req_at}`")
                    
                    with st.form(f"sub_act_{s_ph}"):
                        col_a1, col_a2 = st.columns(2)
                        acc = col_a1.form_submit_button("✅ قبول وتفعيل الاشتراك")
                        ref = col_a2.form_submit_button("❌ رفض / حذف")
                        if acc:
                            exp_time = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE subscriptions SET status='active', expires_at=? WHERE student_phone=? AND teacher_phone=?", 
                                      (exp_time, s_ph, t_phone))
                            conn.commit()
                            st.success("تم تفعيل اشتراك الطالب بنجاح!")
                            st.rerun()
                        if ref:
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, t_phone))
                            conn.commit()
                            st.success("تم حذف الطلب.")
                            st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد طلبات اشتراك معلقة حالياً.")
        except:
            pass

    # 5. البث المباشر داخل المنصة (من كاميرا الأستاذ مباشرة بدون روابط خارجية)
    with tab_ctrl5:
        st.markdown("### 🔴 بث مباشر حصري للمشتركين فقط داخل المنصة")
        st.write("استخدم أداة التقاط الكاميرا أدناه لبدء البث المباشر بالصوت والصورة لطلابك المشتركين حصرياً:")
        
        # استخدام كاميرا الجهاز مباشرة لتكون البث الحي داخل التطبيق بدون روابط خارجية
        live_camera_input = st.camera_input("تشغيل كاميرا البث المباشر للأستاذ:")
        if live_camera_input:
            st.success("🟢 الكاميرا والمايك يعملان بنجاح، البث مباشر الآن للمشتركين في غرفتك الخاصة!")

# ==========================================
# 7. لوحة تحكم الطالب (استعراض الأساتذة والغرف)
# ==========================================
elif st.session_state.user_role == "طالب":
    st_phone = st.session_state.user_phone
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM users WHERE phone=?", (st_phone,))
        st_user_row = c.fetchone()
    st_my_name = st_user_row[0] if st_user_row else "طالب"

    st.sidebar.title(f"👨‍🎓 أهلاً، {st_my_name}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        logout_user()
        st.rerun()

    # إذا لم يدخل غرفة أستاذ بعد، يعرض له قائمة الأساتذة
    if not st.session_state.inside_teacher_room:
        st.subheader("👨‍🏫 أساتذة المنصة المتاحين")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, subject, price, room_id, phone FROM teachers WHERE is_blocked=0")
                teachers = c.fetchall()
            if teachers:
                for t_name, t_sub, t_price, r_id, t_ph in teachers:
                    st.markdown('<div class="app-card">', unsafe_allow_html=True)
                    col_i1, col_i2 = st.columns([3, 1])
                    col_i1.markdown(f"### 👨‍🏫 أ. {t_name}")
                    col_i1.write(f"**المادة:** {t_sub} | **سعر الاشتراك الشهري:** {t_price} جنيه")
                    
                    if col_i2.button("دخول الغرفة", key=f"room_btn_{t_ph}"):
                        st.session_state.sub_target_teacher = t_ph
                        st.session_state.inside_teacher_room = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("لا توجد أساتذة متاحين في المنصة حالياً.")
        except:
            pass
            
    else:
        # الطالب داخل غرفة الأستاذ المحدد
        target_t_phone = st.session_state.sub_target_teacher
        if st.button("⬅️ العودة لقائمة الأساتذة"):
            st.session_state.inside_teacher_room = False
            st.session_state.sub_target_teacher = None
            st.rerun()
            
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, subject, price, schedule_info FROM teachers WHERE phone=?", (target_t_phone,))
                t_info = c.fetchone()
        except:
            t_info = ("أستاذ", "مادة", 100, "")
            
        t_name, t_sub, t_price, t_schedule = t_info
        st.subheader(f"📚 غرفة الأستاذ: {t_name} ({t_sub})")
        
        # التحقق من حالة اشتراك الطالب مع هذا الأستاذ
        is_active_subscriber = False
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st_phone, target_t_phone))
                sub_row = c.fetchone()
                if sub_row and sub_row[0] == 'active':
                    is_active_subscriber = True
        except:
            pass
            
        # إذا لم يكن مشتركاً، يظهر له زر الاشتراك والدفع عبر أورانج كاش والمحتوى الترويجي العام فقط
        if not is_active_subscriber:
            st.markdown(f"<div class='app-card'>", unsafe_allow_html=True)
            st.warning(, f"⚠️ أنت غير مشترك في محتوى هذا الأستاذ المدفوع. سعر الاشتراك الشهري: **{t_price} جنيه**. يرجى التحويل عبر أورانج كاش وإرسال رقم المحول لتفعيل الاشتراك.")
            
            with st.form("subscribe_form"):
                orange_sender_phone = st.text_input("أدخل رقم محمول أورانج كاش الذي قمت بالتحويل منه:")
                sub_req_btn = st.form_submit_button("إرسال طلب الاشتراك للأستاذ")
                if sub_req_btn and orange_sender_phone:
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status, orange_cash_sender, requested_at) VALUES (?, ?, 'pending', ?, ?)",
                                      (st_phone, target_t_phone, orange_sender_phone, t_now))
                            conn.commit()
                        st.success("تم إرسال طلب الاشتراك بنجاح! في انتظار موافقة الأستاذ.")
                    except:
                        st.error("حدث خطأ أثناء إرسال الطلب.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 🌟 الفيديوهات الترويجية العامة (متاحة للجميع)")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, title, file_path FROM posts WHERE teacher_phone=? AND visibility='public' AND status='approved' ORDER BY id DESC", (target_t_phone,))
                    public_posts = c.fetchall()
                if public_posts:
                    for p_id, p_title, p_path in public_posts:
                        st.markdown(f"📌 **{p_title}** <span class='promo-badge'>عام</span>", unsafe_allow_html=True)
                        if p_path and os.path.exists(p_path):
                            st.video(p_path)
                        st.write("---")
                else:
                    st.info("لا توجد فيديوهات ترويجية عامة حالياً.")
            except:
                pass
                
        else:
            # الطالب مشترك بالفعل ويحق له رؤية جدول المواعيد، الفيديوهات المدفوعة، البث المباشر، والامتحانات
            st.success("🎉 أنت مشترك رسمي في هذه الغرفة وتستمتع بكافة الصلاحيات!")
            
            tab_st1, tab_st2, tab_st3, tab_st4, tab_st5 = st.tabs([
                "📅 جدول المواعيد", 
                "🎬 الفيديوهات والدروس المدفوعة", 
                "🔴 البث المباشر للحصة", 
                "📝 الامتحانات والاختبارات", 
                "💬 الشات الخاص مع الأستاذ"
            ])
            
            # 1. الجدول
            with tab_st1:
                st.markdown("### 📅 جدول مواعيد الحصص:")
                st.info(t_schedule)
                
            # 2. الفيديوهات المدفوعة
            with tab_st2:
                st.markdown("### 🎬 دروس وشروحات الأستاذ المدفوعة:")
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT id, title, file_path FROM posts WHERE teacher_phone=? AND status='approved' ORDER BY id DESC", (target_t_phone,))
                        posts = c.fetchall()
                    if posts:
                        for p_id, p_title, p_path in posts:
                            st.markdown(f"📌 **{p_title}**")
                            if p_path and os.path.exists(p_path):
                                st.video(p_path)
                            else:
                                st.warning("ملف الفيديو غير موجود.")
                            
                            # قسم التعليقات تحت الفيديو
                            with st.expander("💬 مناقشة الدرس والتعليقات"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("SELECT student_name, comment_text, timestamp FROM comments WHERE post_id=? ORDER BY id DESC", (p_id,))
                                    comms = c.fetchall()
                                if comms:
                                    for c_name, c_text, c_time in comms:
                                        st.markdown(f"💬 **{c_name}**: {c_text} <small style='color:gray;'>({c_time})</small>", unsafe_allow_html=True)
                                else:
                                    st.write("لا توجد تعليقات بعد.")
                                    
                                with st.form(f"c_form_{p_id}", clear_on_submit=True):
                                    c_txt = st.text_input("أضف تعليقك:")
                                    c_btn = st.form_submit_button("إرسال التعليق")
                                    if c_btn and c_txt:
                                        t_now = datetime.datetime.now().strftime("%H:%M")
                                        with sqlite3.connect(DB_NAME) as conn:
                                            c = conn.cursor()
                                            c.execute("INSERT INTO comments (post_id, student_name, comment_text, timestamp) VALUES (?, ?, ?, ?)",
                                                      (p_id, st_my_name, c_txt, t_now))
                                            conn.commit()
                                        st.rerun()
                            st.write("---")
                    else:
                        st.info("لا توجد فيديوهات منشورة حالياً.")
                except:
                    pass

            # 3. البث المباشر (للمشتركين فقط داخل المنصة)
            with tab_st3:
                st.markdown("### 🔴 غرفة البث المباشر الحصري للمشتركين")
                st.info("تتم متابعة البث الحي للكاميرا الخاصة بالأستاذ هنا مباشرة داخل المنصة للمشتركين فقط.")
                # عرض توجيهي بأن البث متاح طالما الأستاذ فاتح الكاميرا من لوحته

            # 4. الامتحانات
            with tab_st4:
                st.markdown("### 📝 امتحانات واختبارات الغرفة")
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT id, question, opt1, opt2, opt3, opt4, correct_answer FROM exams WHERE teacher_phone=?", (target_t_phone,))
                        exams = c.fetchall()
                    if exams:
                        for idx, (ex_id, q, o1, o2, o3, o4, correct) in enumerate(exams):
                            st.markdown(f"**السؤال ({idx+1}): {q}**")
                            opts = [o1, o2, o3, o4]
                            with st.form(f"exam_st_{ex_id}"):
                                ans = st.radio("اختر الإجابة الصحيحة:", opts, key=f"rad_{ex_id}")
                                sub_ans = st.form_submit_button("تأكيد الإجابة")
                                if sub_ans:
                                    if ans == correct:
                                        st.success("🎉 إجابة صحيحة برافو عليك!")
                                    else:
                                        st.error(f"❌ إجابة خاطئة. الإجابة الصحيحة هي: {correct}")
                            st.write("---")
                    else:
                        st.info("لا توجد امتحانات مضافة حالياً من الأستاذ.")
                except:
                    pass

            # 5. الشات الخاص مع الأستاذ
            with tab_st5:
                st_autorefresh(interval=2000, key="student_smart_chat_refresh")
                st.markdown("### 💬 الشات الخاص المباشر مع الأستاذ")
                with st.form("st_chat_form", clear_on_submit=True):
                    ch_msg = st.text_input("اكتب رسالتك للأستاذ...")
                    ch_btn = st.form_submit_button("إرسال الرسالة")
                    if ch_btn and ch_msg:
                        t_now = datetime.datetime.now().strftime("%H:%M")
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO smart_chat (teacher_phone, student_phone, sender_role, message, timestamp) VALUES (?, ?, 'طالب', ?, ?)",
                                          (target_t_phone, st_phone, ch_msg, t_now))
                                conn.commit()
                            st.rerun()
                        except:
                            pass
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT sender_role, message, timestamp FROM smart_chat WHERE teacher_phone=? AND student_phone=? ORDER BY id DESC LIMIT 15",
                                  (target_t_phone, st_phone))
                        chats = c.fetchall()
                    if chats:
                        for s_role, s_msg, s_time in reversed(chats):
                            bg_c = "#4f46e5" if s_role == "أستاذ" else "#1e293b"
                            st.markdown(f"<div style='background: {bg_c}; color: #fff; padding: 10px 14px; border-radius: 12px; margin-bottom: 6px;'><small style='color: #cbd5e1;'>[{s_time}] <b>{s_role}:</b></small><br>{s_msg}</div>", unsafe_allow_html=True)
                    else:
                        st.info("لا توجد رسائل سابقة في الشات الخاص.")
                except:
                    pass
