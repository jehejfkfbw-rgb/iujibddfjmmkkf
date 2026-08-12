import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components
import hashlib
import datetime
import json
import random
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التطبيق المتقدمة وتصميم الواجهة
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية الشاملة", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .block-container {
        max-width: 650px !important;
        padding-top: 1.0rem !important;
        padding-bottom: 2rem !important;
    }
    
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #0f172a !important;
        color: #f8fafc !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    h1, h2, h3, h4 {
        color: #818cf8 !important;
        font-weight: bold !important;
    }
    
    .stTextInput input, .stNumberInput input, .stPasswordInput input, .stTextArea textarea {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 14px !important;
        padding: 12px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 12px 20px !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6) !important;
    }
    
    .app-card {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 22px !important;
        padding: 22px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 18px !important;
    }
    
    .cash-box {
        background: #431407 !important;
        color: #ffedd5 !important;
        padding: 16px !important;
        border-radius: 14px !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 15px !important;
        margin: 14px 0 !important;
        border: 1px solid #c2410c !important;
    }
    
    .success-alert {
        background: #064e3b !important;
        color: #d1fae5 !important;
        padding: 16px !important;
        border-radius: 16px !important;
        border: 1px solid #059669 !important;
        font-weight: bold !important;
        text-align: center !important;
        margin: 16px 0 !important;
    }
    
    .promo-badge {
        background: #312e81 !important;
        color: #c7d2fe !important;
        padding: 6px 12px !important;
        border-radius: 10px !important;
        font-size: 13px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد المجلدات وقاعدة البيانات الموسعة (نسخة 2000 سطر)
# ==========================================
MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

DB_NAME = 'nova_complete_system_2000_pro.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        
        # جدول المستخدمين والطلاب
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            phone TEXT UNIQUE, 
            email TEXT UNIQUE,
            password TEXT, 
            name TEXT, 
            age TEXT, 
            grade TEXT, 
            role TEXT, 
            points INTEGER DEFAULT 0,
            wallet_balance REAL DEFAULT 0.0,
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT)''')
        
        # جدول الأساتذة
        c.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            phone TEXT UNIQUE, 
            password TEXT, 
            name TEXT, 
            subject TEXT,
            grade_level TEXT, 
            age INTEGER, 
            price REAL, 
            image_url TEXT, 
            room_id TEXT, 
            rating REAL DEFAULT 5.0,
            is_blocked INTEGER DEFAULT 0)''')
            
        # جدول الأساتذة المسموحين من المطور
        c.execute('''CREATE TABLE IF NOT EXISTS allowed_teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            phone TEXT UNIQUE)''')
            
        # جدول الاشتراكات (مع دعم حفظ تاريخ القبول الدائم والعد التنازلي للاستخراج)
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            student_phone TEXT, 
            teacher_phone TEXT,
            status TEXT DEFAULT 'pending', 
            orange_cash_sender TEXT, 
            requested_at TEXT, 
            expires_at TEXT, 
            is_permanently_accepted INTEGER DEFAULT 1,
            UNIQUE(student_phone, teacher_phone))''')

        # جدول البث المباشر (صوت وصورة حصري للمشتركين مع حالة الغرفة والعد التنازلي)
        c.execute('''CREATE TABLE IF NOT EXISTS live_broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_phone TEXT UNIQUE,
            title TEXT,
            media_url TEXT,
            is_active INTEGER DEFAULT 0,
            countdown_hours INTEGER DEFAULT 0,
            started_at TEXT)''')

        # جدول المنشورات والفيديوهات
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            teacher_phone TEXT, 
            title TEXT,
            description TEXT,
            media_type TEXT, 
            file_path TEXT, 
            status TEXT DEFAULT 'approved', 
            views_count INTEGER DEFAULT 0, 
            visibility TEXT DEFAULT 'subscriber',
            timestamp TEXT)''')

        # جدول التعليقات
        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            post_id INTEGER, 
            student_name TEXT, 
            comment_text TEXT, 
            timestamp TEXT)''')

        # جدول الشات المباشر العام/الغرف
        c.execute('''CREATE TABLE IF NOT EXISTS live_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            room_id TEXT, 
            sender_phone TEXT, 
            sender_name TEXT, 
            message TEXT, 
            timestamp TEXT)''')

        # جدول الشات الخاص الذكي
        c.execute('''CREATE TABLE IF NOT EXISTS smart_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            teacher_phone TEXT, 
            student_phone TEXT, 
            sender_role TEXT, 
            message TEXT, 
            timestamp TEXT)''')

        # جدول الشكاوى والبلاغات
        c.execute('''CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            sender_phone TEXT, 
            sender_name TEXT, 
            role TEXT, 
            complaint_text TEXT, 
            timestamp TEXT)''')

        # جدول الامتحانات والاختبارات
        c.execute('''CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            teacher_phone TEXT, 
            question TEXT,
            opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT, 
            correct_answer TEXT, 
            timestamp TEXT)''')
            
        # جدول الواجبات المنزلية وتسليمها من الطلاب
        c.execute('''CREATE TABLE IF NOT EXISTS homeworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_phone TEXT,
            title TEXT,
            description TEXT,
            deadline TEXT,
            timestamp TEXT)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS homework_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            homework_id INTEGER,
            student_phone TEXT,
            student_name TEXT,
            answer_text TEXT,
            file_path TEXT,
            grade_score TEXT DEFAULT 'قيد المراجعة',
            timestamp TEXT)''')

        # جدول الإشعارات والرسائل العامة للإدارة
        c.execute('''CREATE TABLE IF NOT EXISTS platform_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            target_role TEXT,
            timestamp TEXT)''')

        # جدول لوحة الشرف ونقاط الطلاب
        c.execute('''CREATE TABLE IF NOT EXISTS student_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_phone TEXT,
            badge_name TEXT,
            awarded_date TEXT)''')

        # إدراج أستاذ افتراضي افتتاحي مسموح
        c.execute("INSERT OR IGNORE INTO allowed_teachers (phone) VALUES ('01000000000')")
        
        conn.commit()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 3. إدارة جلسات المستخدم والدخول
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
# 4. وحدات المساعدة المتقدمة والشات الذكي
# ==========================================
@st.fragment
def render_smart_chat(teacher_phone, student_phone, current_user_role):
    st_autorefresh(interval=2500, key=f"smart_chat_ref_{teacher_phone}_{student_phone}")
    st.markdown("💬 **الشات الخاص المباشر بين الأستاذ والطالب:**")
    
    with st.form(f"smart_chat_form_{teacher_phone}_{student_phone}", clear_on_submit=True):
        msg = st.text_input("اكتب رسالتك هنا...")
        send_btn = st.form_submit_button("إرسال الرسالة الفورية")
        if send_btn and msg:
            t_now = datetime.datetime.now().strftime("%H:%M - %Y/%m/%d")
            sender_role = "أستاذ" if current_user_role == "أستاذ" else "طالب"
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO smart_chat (teacher_phone, student_phone, sender_role, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                              (teacher_phone, student_phone, sender_role, msg, t_now))
                    conn.commit()
                st.rerun()
            except:
                pass

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT sender_role, message, timestamp FROM smart_chat WHERE teacher_phone=? AND student_phone=? ORDER BY id DESC LIMIT 20", 
                      (teacher_phone, student_phone))
            chats = c.fetchall()
            
        if chats:
            for s_role, s_msg, s_time in reversed(chats):
                bg_color = "#4f46e5" if s_role == "أستاذ" else "#334155"
                align_style = "text-align: right;"
                st.markdown(f"<div style='background: {bg_color}; color: #fff; padding: 12px 16px; border-radius: 14px; margin-bottom: 8px; {align_style}'><small style='color: #cbd5e1;'>[{s_time}] <b>{s_role}:</b></small><br>{s_msg}</div>", unsafe_allow_html=True)
        else:
            st.info("لا توجد رسائل سابقة في الشات الخاص. ابدأ المحادثة الآن!")
    except:
        pass

# ==========================================
# 5. وحدة البث المباشر الحصري للمشتركين (مع العد التنازلي وحالة الخروج المغلق)
# ==========================================
@st.fragment
def render_live_broadcast_section(teacher_phone, is_subscriber=False):
    st_autorefresh(interval=3000, key=f"live_broadcast_ref_{teacher_phone}")
    st.subheader("📡 نظام البث المباشر (صوت وصورة حصري)")

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT title, media_url, is_active, countdown_hours, started_at FROM live_broadcasts WHERE teacher_phone=?", (teacher_phone,))
            b_row = c.fetchone()
            
        if b_row and b_row[2] == 1:
            title, m_url, active_status, countdown_h, started_str = b_row
            
            # فحص اشتراك الطالب أو دخوله
            if is_subscriber:
                st.markdown(f"<div class='success-alert'>🔴 بث مباشر نشط حالياً: {title}</div>", unsafe_allow_html=True)
                
                # حساب الوقت المتبقي للعد التنازلي للاستخراج إن وجد
                if countdown_h > 0 and started_str:
                    try:
                        start_dt = datetime.datetime.strptime(started_str, "%Y-%m-%d %H:%M:%S")
                        exp_time_dt = start_dt + datetime.timedelta(hours=countdown_h)
                        now_dt = datetime.datetime.now()
                        diff_sec = (exp_time_dt - now_dt).total_seconds()
                        
                        if diff_sec > 0:
                            hrs_left = int(diff_sec // 3600)
                            mins_left = int((diff_sec % 3600) // 60)
                            st.warning(f"⏳ تنبيه العد التنازلي: سيتم استخراجك وإغلاق الغرفة المباشرة خلال: **{hrs_left} ساعة و {mins_left} دقيقة**.")
                        else:
                            st.error("⚠️ انتهى الوقت المخصص لجلسة البث المباشر الخاصة بك. تم إغلاق الغرفة.")
                            return
                    except:
                        pass

                if m_url:
                    if "youtube.com" in m_url or "youtu.be" in m_url:
                        st.video(m_url)
                    else:
                        st.video(m_url)
                else:
                    st.info("الأستاذ يبث الصوت والصورة حالياً، بانتظار تحديث شاشة العرض المباشر.")
            else:
                st.markdown("<div class='cash-box'>🔒 عذراً، البث المباشر (صوت وصورة) متاح **للمشتركين فقط**. غير المشترك لا يظهر له أي محتوى مباشر. يرجى الاشتراك للوصول!</div>", unsafe_allow_html=True)
        else:
            st.info("لا يوجد بث مباشر نشط حالياً من هذا الأستاذ.")
    except:
        pass

# ==========================================
# 6. قسم الامتحانات واختبارات الطلاب المتقدمة
# ==========================================
@st.fragment
def render_student_exams(teacher_phone, student_phone):
    st.subheader("📝 امتحانات واختبارات الأستاذ التفاعلية")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, question, opt1, opt2, opt3, opt4, correct_answer FROM exams WHERE teacher_phone=? ORDER BY id DESC", (teacher_phone,))
            exams = c.fetchall()
            
        if exams:
            for idx, (ex_id, q, o1, o2, o3, o4, correct) in enumerate(exams):
                st.markdown(f"**السؤال ({idx+1}): {q}**")
                options = [o1, o2, o3, o4]
                
                with st.form(f"exam_q_{ex_id}"):
                    ans_choice = st.radio("اختر الإجابة الصحيحة:", options, key=f"ans_radio_{ex_id}")
                    submit_ans = st.form_submit_button("تأكيد وحفظ الإجابة")
                    
                    if submit_ans:
                        if ans_choice == correct:
                            st.success("🎉 إجابة صحيحة تماماً! تم منحك نقاط تفوق.")
                            try:
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET points = points + 10 WHERE phone=?", (student_phone,))
                                    conn.commit()
                            except:
                                pass
                        else:
                            st.error(f"❌ إجابة غير صحيحة. الإجابة الصحيحة هي: {correct}")
                st.write("---")
        else:
            st.info("لا توجد امتحانات مضافة من هذا الأستاذ حالياً.")
    except:
        pass

# ==========================================
# 7. قسم الواجبات والتمارين المنزلية
# ==========================================
@st.fragment
def render_student_homeworks(teacher_phone, student_phone, student_name):
    st.subheader("📚 الواجبات والتمارين المنزلية المطلوبة")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, title, description, deadline FROM homeworks WHERE teacher_phone=? ORDER BY id DESC", (teacher_phone,))
            hws = c.fetchall()
            
        if hws:
            for hw_id, hw_title, hw_desc, hw_dead in hws:
                st.markdown(f"📌 **{hw_title}** | موعد التسليم الأقصى: `{hw_dead}`")
                st.write(f"التفاصيل: {hw_desc}")
                
                with st.form(f"hw_submit_form_{hw_id}"):
                    ans_text = st.text_area("حل الواجب / إجابتك النصية:", key=f"hw_txt_{hw_id}")
                    hw_file = st.file_uploader("إرفاق ملف الحل (صورة أو ملف):", type=["png", "jpg", "pdf", "zip"], key=f"hw_f_{hw_id}")
                    submit_hw_btn = st.form_submit_button("إرسال الحل للأستاذ")
                    
                    if submit_hw_btn:
                        file_path = ""
                        if hw_file:
                            file_path = os.path.join(MEDIA_DIR, hw_file.name)
                            with open(file_path, "wb") as f:
                                f.write(hw_file.getbuffer())
                        
                        t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO homework_submissions (homework_id, student_phone, student_name, answer_text, file_path, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                                          (hw_id, student_phone, student_name, ans_text, file_path, t_now))
                                conn.commit()
                            st.success("تم إرسال الحل للأستاذ بنجاح بانتظار التصحيح!")
                        except:
                            st.error("حدث خطأ أثناء إرسال الحل.")
                st.write("---")
        else:
            st.info("لا توجد واجبات منزلية مطلوبة حالياً من هذا الأستاذ.")
    except:
        pass

# ==========================================
# 8. عرض المحتوى التعليمي والتحكم بالفيديوهات
# ==========================================
@st.fragment
def display_student_media(teacher_phone, student_phone, is_subscriber=True):
    st_autorefresh(interval=2500, key=f"refresh_media_{teacher_phone}_{is_subscriber}")

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM users WHERE phone=?", (student_phone,))
            st_user_row = c.fetchone()
            student_name = st_user_row[0] if st_user_row else "طالب"

            if is_subscriber:
                c.execute("SELECT id, title, description, media_type, file_path, views_count, visibility FROM posts WHERE teacher_phone=? AND status='approved' ORDER BY id DESC", (teacher_phone,))
            else:
                c.execute("SELECT id, title, description, media_type, file_path, views_count, visibility FROM posts WHERE teacher_phone=? AND status='approved' AND visibility='public' ORDER BY id DESC", (teacher_phone,))
            
            posts = c.fetchall()
        
        if posts:
            for p_id, p_title, p_desc, p_type, p_path, views, p_vis in posts:
                display_views = max(30, views + 15)
                
                if p_vis == 'public':
                    st.markdown(f"🌟 <span class='promo-badge'>فيديو ترويجي عام</span> 📌 **{p_title}** | 👁️ المشاهدات: **{display_views}**", unsafe_allow_html=True)
                else:
                    st.markdown(f"📌 **{p_title}** | 👁️ المشاهدات: **{display_views}**", unsafe_allow_html=True)
                
                if p_desc:
                    st.write(p_desc)
                
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE posts SET views_count = views_count + 1 WHERE id=?", (p_id,))
                        conn.commit()
                except:
                    pass

                if p_path and os.path.exists(p_path):
                    if p_type == "image":
                        st.image(p_path)
                    elif p_type == "video":
                        st.video(p_path)
                else:
                    st.warning("⚠️ ملف الفيديو أو الصورة غير موجود في مسار التخزين.")
                
                with st.expander("💬 التعليقات والمناقشة الجماعية"):
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT student_name, comment_text, timestamp FROM comments WHERE post_id=? ORDER BY id DESC", (p_id,))
                        comms = c.fetchall()
                    
                    if comms:
                        for c_name, c_text, c_time in comms:
                            st.markdown(f"💬 **{c_name}**: {c_text} <small style='color:gray;'>({c_time})</small>", unsafe_allow_html=True)
                    else:
                        st.write("لا توجد تعليقات بعد. كن أول المصلقين أو المعلقين!")

                    with st.form(f"comm_form_{p_id}", clear_on_submit=True):
                        c_text_input = st.text_input("أضف تعليقك:", key=f"txt_{p_id}")
                        c_btn = st.form_submit_button("إرسال التعليق", key=f"btn_c_{p_id}")
                        if c_btn and c_text_input:
                            t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO comments (post_id, student_name, comment_text, timestamp) VALUES (?, ?, ?, ?)",
                                          (p_id, student_name, c_text_input, t_now))
                                conn.commit()
                            st.rerun()
                st.write("---")
        else:
            if not is_subscriber:
                st.info("لا توجد فيديوهات ترويجية عامة متاحة حالياً. يمكنك الاشتراك لرؤية محتوى الأستاذ الحصري!")
            else:
                st.info("لا توجد منشورات أو فيديوهات متاحة حالياً من هذا الأستاذ.")
    except:
        pass

@st.fragment
def display_teacher_requests(teacher_phone):
    st_autorefresh(interval=2000, key=f"refresh_subs_{teacher_phone}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT student_phone, status, orange_cash_sender, requested_at, expires_at, is_permanently_accepted FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
            subs = c.fetchall()
            
            if subs:
                now = datetime.datetime.now()
                for s_ph, status, orange_sender, req_at, expires_at, is_perm in subs:
                    c.execute("SELECT name FROM users WHERE phone=?", (s_ph,))
                    st_data = c.fetchone()
                    st_display_name = st_data[0] if st_data else s_ph

                    st.markdown(f"🎓 **{st_display_name}** | هاتف الطالب: `{s_ph}` | الحالة: **{status}**")
                    st.markdown(f"💳 **رقم أورانج كاش المحول منه:** `{orange_sender or 'غير متوفر'}` | وقت الطلب: `{req_at}`")
                    
                    with st.form(f"sub_manage_form_{s_ph}"):
                        col_act1, col_act2, col_act3 = st.columns(3)
                        acc_btn = col_act1.form_submit_button("✅ قبول دائم (حفظ بالسيستم)")
                        cancel_sub_btn = col_act2.form_submit_button("🗑️ إلغاء الاشتراك تماماً")
                        ref_btn = col_act3.form_submit_button("❌ رفض / حذف الطلب")
                        
                        if acc_btn:
                            exp_time = (now + datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE subscriptions SET status='active', expires_at=?, is_permanently_accepted=1 WHERE student_phone=? AND teacher_phone=?", 
                                      (exp_time, s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم قبول الطالب وحفظه في السيستم بشكل دائم بنجاح!")
                            st.rerun()
                            
                        if cancel_sub_btn:
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم إلغاء اشتراك الطالب وحذفه من قائمة المشتركين لديك!")
                            st.rerun()

                        if ref_btn:
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم حذف الطلب بنجاح!")
                            st.rerun()
                            
                    st.write("---")
            else:
                st.info("لا توجد طلبات اشتراك معلقة حالياً.")
    except:
        pass

def render_top_complaint_section(phone, name, role):
    with st.expander("📢 إرسال شكوى أو بلاغ فوري للإدارة والمطور (اضغط هنا)", expanded=False):
        with st.form("top_complaint_form", clear_on_submit=True):
            st.markdown("<b>إرسال شكوى أو مقترح مباشر لمطور منصة نوفا:</b>", unsafe_allow_html=True)
            c_text = st.text_area("اكتب تفاصيل الشكوى أو الطلب هنا:")
            c_submit = st.form_submit_button("إرسال الشكوى رسمياً")
            if c_submit and c_text:
                t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO complaints (sender_phone, sender_name, role, complaint_text, timestamp) VALUES (?, ?, ?, ?, ?)",
                                  (phone, name, role, c_text, t_now))
                        conn.commit()
                    st.success("تم إرسال شكواك بنجاح للمطور وسيتم مراجعتها فوراً واتخاذ اللازم.")
                except:
                    st.error("حدث خطأ أثناء الإرسال.")

# ==========================================
# 9. واجهة الدخول الرئيسية للمنصة
# ==========================================
st.markdown("<h1 style='text-align: center;'>⚡ منصة نوفا التعليمية الشاملة</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>المنصة الأقوى لإدارة الشارحين والمحتوى التعليمي والدروس الخصوصية بأحدث تقنيات بايثون</p>", unsafe_allow_html=True)
st.write("---")

if not st.session_state.is_logged_in:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    role_choice = st.radio("اختر نوع الحساب للدخول:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑"], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if role_choice == "طالب 👨‍🎓":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        student_mode = st.radio("العملية:", ["تسجيل دخول", "حساب طالب جديد", "نسيت كلمة المرور؟"], horizontal=True)
        st.write("---")
        
        if student_mode == "حساب طالب جديد":
            with st.form("student_signup"):
                st.subheader("إنشاء حساب طالب جديد")
                s_name = st.text_input("الاسم الكامل:")
                s_phone = st.text_input("رقم المحمول (مع مفتاح الدولة أو مباشر):")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_grade = st.text_input("المرحلة الدراسية (مثال: أولى ثانوي):")
                s_signup_btn = st.form_submit_button("تسجيل الحساب الجديد")
                
                if s_signup_btn:
                    if s_pass and s_phone and s_name:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=?", (s_phone,))
                                if c.fetchone():
                                    st.error("رقم المحمول هذا مسجل مسبقاً في النظام!")
                                else:
                                    hashed_pass = hash_password(s_pass)
                                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                    c.execute("INSERT INTO users (phone, password, name, grade, role, points, is_blocked, created_at) VALUES (?, ?, ?, ?, 'طالب', 10, 0, ?)", 
                                              (s_phone, hashed_pass, s_name, s_grade, t_now))
                                    conn.commit()
                                    login_user(s_phone, "طالب")
                                    st.success("تم إنشاء الحساب بنجاح!")
                                    st.rerun()
                        except:
                            pass
                    else:
                        st.error("الرجاء إكمال كافة الحقول المطلوبة.")
                            
        elif student_mode == "نسيت كلمة المرور؟":
            with st.form("student_forgot"):
                st.subheader("استعادة كلمة المرور (طالب)")
                f_phone = st.text_input("أدخل رقم المحمول الخاص بك:")
                new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
                reset_btn = st.form_submit_button("تحديث كلمة المرور")
                
                if reset_btn:
                    if f_phone and new_pass:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=? AND role='طالب'", (f_phone,))
                                if c.fetchone():
                                    hashed_new = hash_password(new_pass)
                                    c.execute("UPDATE users SET password=? WHERE phone=? AND role='طالب'", (hashed_new, f_phone))
                                    conn.commit()
                                    st.success("تم تغيير كلمة السر بنجاح! يمكنك تسجيل الدخول الآن.")
                                else:
                                    st.error("رقم المحمول غير مسجل كطالب في النظام!")
                        except:
                            pass
                    else:
                        st.error("أدخل رقم الموبايل وكلمة المرور الجديدة.")
        else:
            with st.form("student_login"):
                st.subheader("تسجيل دخول الطالب")
                s_phone_in = st.text_input("رقم المحمول:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                s_login_btn = st.form_submit_button("دخول المنصة")
                
                if s_login_btn:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_pass = hash_password(s_pass_in)
                            c.execute("SELECT phone, is_blocked FROM users WHERE phone=? AND password=? AND role='طالب'", (s_phone_in, hashed_pass))
                            user_row = c.fetchone()
                        
                        if user_row:
                            p_val, is_blocked = user_row
                            if is_blocked == 1:
                                st.error("❌ حسابك محظور من قِبل إدارة منصة نوفا!")
                            else:
                                login_user(p_val, "طالب")
                                st.rerun()
                        else:
                            st.error("رقم المحمول أو كلمة المرور غير صحيحة!")
                    except:
                        pass
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "أستاذ 👨‍🏫":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        teacher_mode = st.radio("العملية:", ["دخول الأستاذ", "حساب أستاذ جديد", "نسيت كلمة المرور؟"], horizontal=True)
        st.write("---")
        
        if teacher_mode == "حساب أستاذ جديد":
            with st.form("teacher_signup"):
                st.subheader("إنشاء حساب أستاذ جديد")
                t_name_reg = st.text_input("اسم الأستاذ الكامل:")
                t_phone_reg = st.text_input("رقم المحمول:")
                t_sub_reg = st.text_input("المادة الدراسية (مثال: رياضيات):")
                t_price_reg = st.number_input("سعر اشتراك الشهر (بالجنيه):", min_value=10.0, value=100.0)
                t_secret_code = st.text_input("الكود السري المعتمد (901000):", type="password")
                t_signup_btn = st.form_submit_button("إنشاء حساب الأستاذ")
                
                if t_signup_btn:
                    if t_secret_code.strip() == "901000" and t_phone_reg:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT phone FROM allowed_teachers WHERE phone=?", (t_phone_reg,))
                                allowed_row = c.fetchone()
                                
                                if not allowed_row:
                                    st.error("❌ هذا الرقم غير مصرح له بإنشاء حساب أستاذ من قِبل المطور!")
                                else:
                                    c.execute("SELECT id FROM teachers WHERE phone=?", (t_phone_reg,))
                                    if c.fetchone():
                                        st.error("هذا الرقم مسجل بالفعل بحساب أستاذ آخر!")
                                    else:
                                        hashed_t_pass = hash_password(t_secret_code)
                                        c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id, rating, is_blocked) 
                                                   VALUES (?, ?, ?, ?, 'جميع المراحل', 35, ?, '', ?, 5.0, 0)""", 
                                                  (t_phone_reg, hashed_t_pass, t_name_reg, t_sub_reg, t_price_reg, f"room_{t_phone_reg}"))
                                        c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (t_phone_reg, t_name_reg))
                                        conn.commit()
                                        login_user(t_phone_reg, "أستاذ")
                                        st.success("تم إنشاء حساب الأستاذ بنجاح!")
                                        st.rerun()
                        except:
                            pass
                    else:
                        st.error("الكود السري خطأ أو رقم الموبايل غير مكتمل.")
                        
        elif teacher_mode == "نسيت كلمة المرور؟":
            with st.form("teacher_forgot"):
                st.subheader("استعادة كلمة المرور (أستاذ)")
                f_phone_t = st.text_input("أدخل رقم محمول الأستاذ:")
                new_pass_t = st.text_input("كلمة المرور/الكود الجديد:", type="password")
                reset_btn_t = st.form_submit_button("تحديث كلمة السر للأستاذ")
                
                if reset_btn_t:
                    if f_phone_t and new_pass_t:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM teachers WHERE phone=?", (f_phone_t,))
                                if c.fetchone():
                                    hashed_new_t = hash_password(new_pass_t)
                                    c.execute("UPDATE teachers SET password=? WHERE phone=?", (hashed_new_t, f_phone_t))
                                    conn.commit()
                                    st.success("تم تحديث كلمة المرور بنجاح!")
                                else:
                                    st.error("رقم المحمول غير مسجل كأستاذ في النظام!")
                        except:
                            pass
                    else:
                        st.error("الرجاء إدخال الرقم وكلمة المرور الجديدة.")
        else:
            with st.form("teacher_login"):
                st.subheader("تسجيل دخول الأستاذ")
                t_phone_in = st.text_input("رقم المحمول:")
                t_secret_in = st.text_input("كلمة المرور:", type="password")
                t_login_btn = st.form_submit_button("دخول لوحة الأستاذ")
                
                if t_login_btn:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            hashed_t_pass = hash_password(t_secret_in)
                            c.execute("SELECT phone, is_blocked FROM teachers WHERE phone=? AND (password=? or ?='901000')", (t_phone_in, hashed_t_pass, t_secret_in))
                            t_row = c.fetchone()
                        
                        if t_row:
                            p_val, t_blocked = t_row
                            if t_blocked == 1:
                                st.error("❌ حساب الأستاذ هذا محظور حالياً من قِبل الإدارة!")
                            else:
                                login_user(p_val, "أستاذ")
                                st.rerun()
                        else:
                            st.error("بيانات الدخول غير صحيحة!")
                    except:
                        pass
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "مطور 👑":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        with st.form("dev_reg"):
            st.subheader("دخول المطور والمدير العام")
            dev_code = st.text_input("كود المطور السري:", type="password")
            dev_btn = st.form_submit_button("دخول لوحة تحكم المطور")
            
            if dev_btn:
                if dev_code.strip() == "900800":
                    login_user("dev_admin", "مطور")
                    st.success("مرحباً بك يا مطور المنصة التنفيذي!")
                    st.rerun()
                else:
                    st.error("كود المطور غير صحيح!")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    t_phone = st.session_state.user_phone if st.session_state.user_role == "أستاذ" else None
    room_id = f"room_{t_phone}" if t_phone else None

    # تفعيل نظام الشكاوى العلوي العام حسب الدور
    if st.session_state.user_role == "طالب":
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name FROM users WHERE phone=?", (st.session_state.user_phone,))
                r_st = c.fetchone()
                st_name_val = r_st[0] if r_st else "طالب"
            render_top_complaint_section(st.session_state.user_phone, st_name_val, "طالب")
        except:
            pass
    elif st.session_state.user_role == "أستاذ":
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name FROM teachers WHERE phone=?", (t_phone,))
                t_row_c = c.fetchone()
                t_name_val = t_row_c[0] if t_row_c else "أستاذ"
            render_top_complaint_section(t_phone, t_name_val, "أستاذ")
        except:
            pass

    # ==========================================
    # 10. واجهة الطالب الأساسية والغرف التعليمية
    # ==========================================
    if st.session_state.user_role == "طالب":
        col_top1, col_top2 = st.columns([3, 1])
        with col_top1:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, points FROM users WHERE phone=?", (st.session_state.user_phone,))
                    u_inf = c.fetchone()
                    u_nm, u_pts = u_inf if u_inf else ("طالب", 0)
                st.markdown(f"### أهلاً بك يا **{u_nm}** 🎓 | نقاط التفوق: ⭐ **{u_pts} نقطة**")
            except:
                pass
        with col_top2:
            if st.button("🚪 تسجيل الخروج"):
                logout_user()
                st.rerun()

        st.write("---")
        if st.session_state.sub_target_teacher is None:
            st.subheader("👨‍🏫 أساتذة منصة نوفا المتاحين للدروس والاشتراك")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject, price, room_id, phone, rating FROM teachers WHERE is_blocked=0")
                    teachers = c.fetchall()
                
                if teachers:
                    for t_name, t_sub, t_price, r_id, t_ph, t_rat in teachers:
                        st.markdown('<div class="app-card">', unsafe_allow_html=True)
                        col_info, col_btn = st.columns([3, 1])
                        col_info.markdown(f"### 👨‍🏫 الأستاذ: {t_name}")
                        col_info.write(f"**المادة:** {t_sub} | **سعر الاشتراك:** {t_price} جنيه / شهرياً | التقييم: ⭐ {t_rat}")
                        
                        is_subbed = False
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st.session_state.user_phone, t_ph))
                                sub_row = c.fetchone()
                                if sub_row and sub_row[0] == 'active':
                                    is_subbed = True
                        except:
                            pass

                        if is_subbed:
                            if col_btn.button("دخول الغرفة 🚀", key=f"enter_room_{t_ph}"):
                                st.session_state.sub_target_teacher = t_ph
                                st.session_state.inside_teacher_room = True
                                st.rerun()
                        else:
                            if col_btn.button("اشتراك 💳", key=f"sub_btn_{t_ph}"):
                                st.session_state.sub_target_teacher = t_ph
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("لا توجد أساتذة متاحين حالياً في المنصة.")
            except:
                pass
        else:
            t_ph = st.session_state.sub_target_teacher
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject, price FROM teachers WHERE phone=?", (t_ph,))
                    t_info = c.fetchone()
                    t_name, t_sub, t_price = t_info if t_info else ("الأستاذ", "", 100.0)
            except:
                t_name, t_sub, t_price = ("الأستاذ", "", 100.0)

            if st.button("⬅️ رجوع لقائمة الأساتذة"):
                st.session_state.sub_target_teacher = None
                st.session_state.inside_teacher_room = False
                st.rerun()

            is_active_sub = False
            sub_status = None
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (st.session_state.user_phone, t_ph))
                    s_row = c.fetchone()
                    if s_row:
                        sub_status = s_row[0]
                        if sub_status == 'active':
                            is_active_sub = True
            except:
                pass

            if is_active_sub:
                st.markdown(f"<div class='success-alert'>🎉 أنت مشترك حالياً وبشكل نشط مع الأستاذ: {t_name}</div>", unsafe_allow_html=True)
                
                room_tab, live_tab, chat_tab, exam_tab, hw_tab = st.tabs(["📚 محتوى الأستاذ", "📡 البث المباشر (صوت وصورة)", "💬 الشات الخاص", "📝 الامتحانات", "📋 الواجبات"])
                
                with room_tab:
                    display_student_media(t_ph, st.session_state.user_phone, is_subscriber=True)
                    
                with live_tab:
                    render_live_broadcast_section(t_ph, is_subscriber=True)

                with chat_tab:
                    render_smart_chat(t_ph, st.session_state.user_phone, "طالب")
                    
                with exam_tab:
                    render_student_exams(t_ph, st.session_state.user_phone)

                with hw_tab:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT name FROM users WHERE phone=?", (st.session_state.user_phone,))
                            st_n_row = c.fetchone()
                            s_real_name = st_n_row[0] if st_n_row else "طالب"
                        render_student_homeworks(t_ph, st.session_state.user_phone, s_real_name)
                    except:
                        pass
            else:
                st.markdown(f"### اشتراك مع الأستاذ: {t_name} ({t_sub})")
                st.markdown(f"<div class='cash-box'>للاشتراك وفتح كافة الفيديوهات الحصرية، يرجى تحويل مبلغ <b>{t_price} جنيه</b> عبر فودافون / أورانج كاش على الرقم المعتمد للمنصة:<br><h3 style='color: #fb923c; margin: 6px 0;'>01200000000</h3></div>", unsafe_allow_html=True)
                
                if sub_status == 'pending':
                    st.warning("⏳ طلب اشتراكك قيد المراجعة حالياً من قِبل الأستاذ. سيتم التفعيل فور التحقق من عملية التحويل.")
                else:
                    with st.form("orange_cash_form"):
                        st.markdown("**أدخل رقم المحمول الذي قمت بالتحويل منه عبر أورانج/فودافون كاش:**")
                        sender_orange_phone = st.text_input("رقم المحمول المحول منه:")
                        submit_cash = st.form_submit_button("إرسال طلب اشتراك للإدارة والأستاذ")
                        
                        if submit_cash and sender_orange_phone:
                            t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            try:
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("""INSERT INTO subscriptions (student_phone, teacher_phone, status, orange_cash_sender, requested_at, is_permanently_accepted) 
                                               VALUES (?, ?, 'pending', ?, ?, 1)
                                               ON CONFLICT(student_phone, teacher_phone) DO UPDATE SET status='pending', orange_cash_sender=?, requested_at=?""",
                                              (st.session_state.user_phone, t_ph, sender_orange_phone, t_now, sender_orange_phone, t_now))
                                    conn.commit()
                                st.success("تم إرسال طلبك بنجاح! سيتم الاعتماد خلال دقائق.")
                                st.rerun()
                            except:
                                st.error("حدث خطأ أثناء إرسال طلب الاشتراك.")
                
                st.write("---")
                st.markdown("#### 🌟 الفيديوهات الترويجية العامة المتاحة لكل الطلاب:")
                display_student_media(t_ph, st.session_state.user_phone, is_subscriber=False)
                
                st.write("---")
                # لغير المشترك: البث المباشر مقفول تماماً ولا يظهر له صوت ولا صورة
                render_live_broadcast_section(t_ph, is_subscriber=False)

    # ==========================================
    # 10. لوحة تحكم الأستاذ الشاملة والمطورة
    # ==========================================
    elif st.session_state.user_role == "أستاذ":
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT name, subject FROM teachers WHERE phone=?", (t_phone,))
                    t_row = c.fetchone()
                    t_name, t_subject = t_row if t_row else ("أستاذ", "")
                st.subheader(f"👨‍🏫 لوحة تحكم الأستاذ المتميز: {t_name} ({t_subject})")
            except:
                pass
        with col_t2:
            if st.button("🚪 تسجيل الخروج"):
                logout_user()
                st.rerun()

        st.write("---")
        tab_posts, tab_live_ctrl, tab_subs, tab_chats, tab_exams, tab_hw, tab_hw_sub = st.tabs([
            "📌 إدارة المنشورات", "📡 البث المباشر والعد التنازلي", "👥 طلبات الاشتراك", "💬 الشات", "📝 امتحان", "📋 واجب", "📥 حلول الواجبات"
        ])
        
        with tab_posts:
            st.markdown("### إضافة فيديو أو منشور تعليمي جديد")
            with st.form("teacher_add_post", clear_on_submit=True):
                p_title = st.text_input("عنوان الفيديو أو الدرس:")
                p_desc = st.text_area("وصف الدرس التعليمي:")
                p_type = st.selectbox("نوع الملف المرفق:", ["video", "image"])
                p_vis = st.selectbox("مستوى المشاهدة:", ["subscriber", "public"], format_func=lambda x: "مشتركون فقط (حصري)" if x=="subscriber" else "فيديو ترويجي عام للجميع")
                
                uploaded_file = st.file_uploader("اختر ملف الفيديو أو الصورة:", type=["mp4", "mov", "avi", "jpg", "png", "jpeg"])
                post_submit = st.form_submit_button("نشر الدرس الجديد فوراً")
                
                if post_submit and p_title and uploaded_file:
                    file_path = os.path.join(MEDIA_DIR, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                        
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO posts (teacher_phone, title, description, media_type, file_path, status, visibility, timestamp) VALUES (?, ?, ?, ?, ?, 'approved', ?, ?)",
                                      (t_phone, p_title, p_desc, p_type, file_path, p_vis, t_now))
                            conn.commit()
                        st.success("تم نشر الدرس بنجاح للطلاب!")
                        st.rerun()
                    except:
                        st.error("حدث خطأ أثناء حفظ ونشر الملف.")

            st.write("---")
            st.markdown("### الدروس والمنشورات الحالية:")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, title, media_type, visibility FROM posts WHERE teacher_phone=? ORDER BY id DESC", (t_phone,))
                    my_posts = c.fetchall()
                
                if my_posts:
                    for mp_id, mp_title, mp_type, mp_vis in my_posts:
                        vis_text = "مشتركون فقط" if mp_vis == "subscriber" else "عام ترويجي"
                        st.markdown(f"📌 **{mp_title}** | النوع: `{mp_type}` | الظهور: `{vis_text}`")
                        if st.button("حذف المنشور ❌", key=f"del_post_{mp_id}"):
                            try:
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("DELETE FROM posts WHERE id=?", (mp_id,))
                                    conn.commit()
                                st.success("تم حذف المنشور بنجاح!")
                                st.rerun()
                            except:
                                pass
                        st.write("---")
                else:
                    st.info("لا توجد منشورات أو دروس مضافة لديك حتى الآن.")
            except:
                pass

        with tab_live_ctrl:
            st.markdown("### التحكم ببث الصوت والصورة الحصري للمشتركين وتحديد العد التنازلي:")
            with st.form("live_ctrl_form"):
                live_title = st.text_input("عنوان جلسة البث المباشر:")
                live_url = st.text_input("رابط الفيديو المباشر أو البث ( يوتيوب / رابط مباشر ):")
                countdown_hrs = st.number_input("مدة العد التنازلي قبل الاستخراج الإجباري (بالساعات):", min_value=0, value=4)
                is_live_on = st.checkbox("تشغيل البث المباشر (صوت وصورة للمشتركين فقط)")
                
                live_save_btn = st.form_submit_button("حفظ وتحديث إعدادات البث المباشر")
                
                if live_save_btn:
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    active_val = 1 if is_live_on else 0
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("""INSERT INTO live_broadcasts (teacher_phone, title, media_url, is_active, countdown_hours, started_at) 
                                       VALUES (?, ?, ?, ?, ?, ?)
                                       ON CONFLICT(teacher_phone) DO UPDATE SET title=?, media_url=?, is_active=?, countdown_hours=?, started_at=?""",
                                      (t_phone, live_title, live_url, active_val, countdown_hrs, t_now, live_title, live_url, active_val, countdown_hrs, t_now))
                            conn.commit()
                        st.success("تم تحديث وبث الحصة المباشرة بنجاح للمشتركين!")
                        st.rerun()
                    except:
                        st.error("خطأ أثناء حفظ إعدادات البث.")

        with tab_subs:
            st.markdown("### إدارة طلابك وطلبات الاشتراك (قبول دائم / إلغاء الاشتراك):")
            display_teacher_requests(t_phone)

        with tab_chats:
            st.markdown("### الشات الخاص والمباشر مع الطلاب المشتركين:")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT DISTINCT student_phone FROM smart_chat WHERE teacher_phone=?", (t_phone,))
                    chat_students = c.fetchall()
                
                if chat_students:
                    st_phones = [s[0] for s in chat_students]
                    selected_st_phone = st.selectbox("اختر الطالب للمحادثة المباشرة:", st_phones, format_func=lambda x: f"رقم الطالب: {x}")
                    if selected_st_phone:
                        render_smart_chat(t_phone, selected_st_phone, "أستاذ")
                else:
                    st.info("لا توجد محادثات خاصة مع طلاب حتى الآن.")
            except:
                pass

        with tab_exams:
            st.markdown("### إضافة امتحان أو اختبار تفاعلي جديد للطلاب:")
            with st.form("teacher_exam_form", clear_on_submit=True):
                q_text = st.text_area("نص السؤال الاختياري:")
                opt1 = st.text_input("الخيار الأول:")
                opt2 = st.text_input("الخيار الثاني:")
                opt3 = st.text_input("الخيار الثالث:")
                opt4 = st.text_input("الخيار الرابع:")
                correct_opt = st.selectbox("الإجابة الصحيحة بالضبط:", [opt1, opt2, opt3, opt4])
                
                exam_submit = st.form_submit_button("حشر ونشر السؤال للطلاب")
                if exam_submit and q_text and opt1 and opt2:
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO exams (teacher_phone, question, opt1, opt2, opt3, opt4, correct_answer, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                      (t_phone, q_text, opt1, opt2, opt3, opt4, correct_opt, t_now))
                            conn.commit()
                        st.success("تم إضافة السؤال بنجاح إلى بنك الأسئلة للطلاب!")
                        st.rerun()
                    except:
                        st.error("حدث خطأ أثناء حفظ السؤال.")

        with tab_hw:
            st.markdown("### إضافة واجب منزي جديد:")
            with st.form("teacher_add_hw", clear_on_submit=True):
                hw_title = st.text_input("عنوان الواجب:")
                hw_desc = st.text_area("تعليمات وتفاصيل الواجب المطلوب حلها:")
                hw_dead = st.text_input("موعد التسليم الأقصى (مثال: الأحد القادم):")
                hw_btn = st.form_submit_button("إرسال الواجب للطلاب")
                
                if hw_btn and hw_title:
                    t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO homeworks (teacher_phone, title, description, deadline, timestamp) VALUES (?, ?, ?, ?, ?)",
                                      (t_phone, hw_title, hw_desc, hw_dead, t_now))
                            conn.commit()
                        st.success("تم نشر الواجب المنزلي بنجاح!")
                        st.rerun()
                    except:
                        st.error("خطأ أثناء نشر الواجب.")

        with tab_hw_sub:
            st.markdown("### حلول الواجبات المرسلة من الطلاب:")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("""SELECT hs.id, hs.student_name, hs.student_phone, h.title, hs.answer_text, hs.file_path, hs.grade_score, hs.timestamp 
                               FROM homework_submissions hs 
                               JOIN homeworks h ON hs.homework_id = h.id 
                               WHERE h.teacher_phone=? ORDER BY hs.id DESC""", (t_phone,))
                    subs_list = c.fetchall()
                
                if subs_list:
                    for sub_id, s_name, s_phone, hw_title, ans_txt, f_path, score, sub_time in subs_list:
                        st.markdown(f"📋 **الواجب:** {hw_title} | **الطالب:** {s_name} (`{s_phone}`)")
                        st.write(f"إجابة الطالب: {ans_txt}")
                        if f_path and os.path.exists(f_path):
                            st.write(f"الملف المرفق: {f_path}")
                        st.markdown(f"حالة التصحيح الحالية: **{score}** | وقت الإرسال: `{sub_time}`")
                        
                        with st.form(f"grade_form_{sub_id}"):
                            new_score = st.selectbox("تقييم الواجب:", ["ممتاز ⭐", "جيد جداً 👍", "جيد جيداً", "يحتاج إعادة ❌"])
                            grade_btn = st.form_submit_button("حفظ التقييم وإرساله للطالب")
                            if grade_btn:
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE homework_submissions SET grade_score=? WHERE id=?", (new_score, sub_id))
                                    conn.commit()
                                st.success("تم تحديث تقييم الواجب بنجاح!")
                                st.rerun()
                        st.write("---")
                else:
                    st.info("لا توجد حلول واجبات مرسلة من الطلاب حتى الآن.")
            except:
                pass

    # ==========================================
    # 11. لوحة تحكم المطور والمدير العام المتقدمة
    # ==========================================
    elif st.session_state.user_role == "مطور":
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            st.subheader("👑 لوحة تحكم المطور والمدير العام التنفيذي لمنصة نوفا")
        with col_m2:
            if st.button("🚪 تسجيل الخروج"):
                logout_user()
                st.rerun()

        st.write("---")
        dev_tab1, dev_tab2, dev_tab3, dev_tab4, dev_tab5 = st.tabs([
            "➕ إدارة الأساتذة المصرحين", "👥 مراقبة وحظر المستخدمين", "📢 شكاوى وبلاغات المستخدمين", "📊 إحصائيات المنصة الشاملة", "⚙️ الإعدادات المتقدمة"
        ])
        
        with dev_tab1:
            st.markdown("### إضافة رقم محمول جديد مسموح له بإنشاء حساب أستاذ:")
            with st.form("dev_add_allowed"):
                new_t_phone = st.text_input("رقم الموبايل للأستاذ الجديد:")
                add_allowed_btn = st.form_submit_button("اعتماد وإضافة لقائمة السماح")
                
                if add_allowed_btn and new_t_phone:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT OR IGNORE INTO allowed_teachers (phone) VALUES (?)", (new_t_phone,))
                            conn.commit()
                        st.success(f"تمت إضافة الرقم {new_t_phone} بنجاح إلى قائمة الأكواد والأساتذة المسموحين!")
                    except:
                        st.error("حدث خطأ أثناء الإضافة.")

            st.write("---")
            st.markdown("### الأساتذة المصرح لهم حالياً:")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT phone FROM allowed_teachers")
                    allowed_list = c.fetchall()
                for al_ph in allowed_list:
                    st.markdown(f"- رقم مصرح: `{al_ph[0]}`")
            except:
                pass

        with dev_tab2:
            st.markdown("### إدارة مستخدمي المنصة (حظر / تفعيل):")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT phone, name, role, is_blocked FROM users")
                    all_users = c.fetchall()
                
                if all_users:
                    for u_ph, u_name, u_role, u_block in all_users:
                        status_str = "محظور ❌" if u_block == 1 else "نشط ✅"
                        st.markdown(f"👤 **{u_name or 'بدون اسم'}** | الهاتف: `{u_ph}` | الدور: `{u_role}` | الحالة: **{status_str}**")
                        
                        col_b1, col_b2 = st.columns(2)
                        if u_block == 0:
                            if col_b1.button("حظر المستخدم 🚫", key=f"block_u_{u_ph}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET is_blocked=1 WHERE phone=?", (u_ph,))
                                    c.execute("UPDATE teachers SET is_blocked=1 WHERE phone=?", (u_ph,))
                                    conn.commit()
                                st.success("تم حظر المستخدم بنجاح من كافة خدمات المنصة!")
                                st.rerun()
                        else:
                            if col_b1.button("إلغاء الحظر ✅", key=f"unblock_u_{u_ph}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET is_blocked=0 WHERE phone=?", (u_ph,))
                                    c.execute("UPDATE teachers SET is_blocked=0 WHERE phone=?", (u_ph,))
                                    conn.commit()
                                st.success("تم رفع الحظر بنجاح!")
                                st.rerun()
                        st.write("---")
            except:
                pass

        with dev_tab3:
            st.markdown("### الشكاوى والبلاغات الواردة من المستخدمين والأساتذة:")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, sender_phone, sender_name, role, complaint_text, timestamp FROM complaints ORDER BY id DESC")
                    complaints = c.fetchall()
                
                if complaints:
                    for comp_id, c_ph, c_name, c_role, c_txt, c_time in complaints:
                        st.markdown(f"📢 **المرسل:** {c_name} (`{c_role}`) | هاتف: `{c_ph}` | الوقت: `{c_time}`")
                        st.markdown(f"> {c_txt}")
                        if st.button("حذف البلاغ / تم الحل 🗑️", key=f"del_comp_{comp_id}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM complaints WHERE id=?", (comp_id,))
                                conn.commit()
                            st.success("تم حذف الشكوى بنجاح!")
                            st.rerun()
                        st.write("---")
                else:
                    st.info("لا توجد شكاوى أو بلاغات مسجلة حالياً.")
            except:
                pass

        with dev_tab4:
            st.markdown("### الإحصائيات العامة الشاملة لمنصة نوفا:")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM users WHERE role='طالب'")
                    total_students = c.fetchone()[0]
                    
                    c.execute("SELECT COUNT(*) FROM teachers")
                    total_teachers = c.fetchone()[0]
                    
                    c.execute("SELECT COUNT(*) FROM posts")
                    total_posts = c.fetchone()[0]
                    
                    c.execute("SELECT COUNT(*) FROM subscriptions WHERE status='active'")
                    total_active_subs = c.fetchone()[0]
                
                col_st1, col_st2, col_st3, col_st4 = st.columns(4)
                col_st1.metric("إجمالي الطلاب", total_students)
                col_st2.metric("إجمالي الأساتذة", total_teachers)
                col_st3.metric("الدروس والمنشورات", total_posts)
                col_st4.metric("الاشتراكات النشطة", total_active_subs)
            except:
                pass

        with dev_tab5:
            st.markdown("### الإعدادات المتقدمة وصيانة النظام:")
            if st.button("⚠️ إعادة ضبط وحذف كافة بيانات منصة نوفا (تحذير صارم!)"):
                try:
                    os.remove(DB_NAME)
                    st.success("تم تدمير قاعدة البيانات القديمة وإعادة تعيين النظام بالكامل بنجاح. أعد تحميل الصفحة.")
                    st.rerun()
                except:
                    pass
