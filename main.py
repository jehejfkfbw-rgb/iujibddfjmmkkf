import streamlit as st
import sqlite3
import os
import streamlit.components.v1 as components
import hashlib
import random
import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. إعدادات التطبيق وتصميم الواجهة النظيفة
# ==========================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    .block-container {
        max-width: 600px !important;
        padding-top: 1.5rem !important;
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
    
    .cash-box {
        background: #ecfdf5 !important;
        color: #065f46 !important;
        padding: 14px !important;
        border-radius: 12px !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 15px !important;
        margin: 12px 0 !important;
        border: 1px solid #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد قاعدة البيانات والجداول (محدثة بالكامل)
# ==========================================
MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

DB_NAME = 'nova_complete_system.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, email TEXT UNIQUE,
            password TEXT, name TEXT, age TEXT, grade TEXT, role TEXT, is_blocked INTEGER DEFAULT 0)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, password TEXT, name TEXT, subject TEXT,
            grade_level TEXT, age INTEGER, price REAL, image_url TEXT, room_id TEXT, is_blocked INTEGER DEFAULT 0)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, teacher_phone TEXT,
            status TEXT DEFAULT 'pending', requested_at TEXT, expires_at TEXT, UNIQUE(student_phone, teacher_phone))''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_phone TEXT, title TEXT,
            media_type TEXT, file_path TEXT, status TEXT DEFAULT 'approved', views_count INTEGER DEFAULT 0)''')

        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, student_name TEXT, comment_text TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS live_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT, sender_name TEXT, message TEXT, timestamp TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_phone TEXT, student_name TEXT, message TEXT, timestamp TEXT, status TEXT DEFAULT 'pending')''')

        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT)''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
            phone TEXT PRIMARY KEY, code TEXT)''')

        conn.commit()

init_db()

def get_setting(key, default=""):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = c.fetchone()
            return row[0] if row else default
    except:
        return default

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 3. إدارة الجلسات وتثبيت الدخول عبر Query Params
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
    st.query_params.clear()

# ==========================================
# 4. دوال العرض والتشغيل الحي (Fragments)
# ==========================================
@st.fragment
def render_live_chat(room_id, user_name):
    st_autorefresh(interval=2000, key=f"chat_refresh_{room_id}")
    st.markdown("💬 **محادثة البث المباشر (الشات التفاعلي):**")
    
    with st.form(f"chat_form_{room_id}", clear_on_submit=True):
        msg = st.text_input("اكتب رسالة...")
        send_btn = st.form_submit_button("إرسال")
        if send_btn and msg:
            t_now = datetime.datetime.now().strftime("%H:%M:%S")
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO live_chat (room_id, sender_name, message, timestamp) VALUES (?, ?, ?, ?)",
                          (room_id, user_name, msg, t_now))
                conn.commit()
            st.rerun()

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT sender_name, message, timestamp FROM live_chat WHERE room_id=? ORDER BY id DESC LIMIT 15", (room_id,))
            messages = c.fetchall()
            
        if messages:
            chat_box_html = "<div style='background: #1e293b; color: #fff; padding: 12px; border-radius: 12px; height: 220px; overflow-y: auto; direction: rtl;'>"
            for s_name, s_msg, s_time in reversed(messages):
                chat_box_html += f"<div style='margin-bottom: 8px;'><small style='color: #94a3b8;'>[{s_time}]</small> <b>{s_name}:</b> {s_msg}</div>"
            chat_box_html += "</div>"
            st.markdown(chat_box_html, unsafe_allow_html=True)
        else:
            st.info("لا توجد رسائل بعد، كن أول من يتحدث!")
    except:
        pass

@st.fragment
def display_student_media(teacher_phone, student_phone):
    st_autorefresh(interval=2000, key=f"refresh_media_{teacher_phone}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM users WHERE phone=?", (student_phone,))
            st_user_row = c.fetchone()
            student_name = st_user_row[0] if st_user_row else "طالب"

            c.execute("SELECT id, title, media_type, file_path, views_count FROM posts WHERE teacher_phone=? AND status='approved' ORDER BY id DESC", (teacher_phone,))
            posts = c.fetchall()
        
        if posts:
            for p_id, p_title, p_type, p_path, views in posts:
                st.markdown(f"📌 **{p_title}** | 👁️ المشاهدات: **{views}**")
                
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("UPDATE posts SET views_count = views_count + 1 WHERE id=?", (p_id,))
                    conn.commit()

                if os.path.exists(p_path):
                    if p_type == "image":
                        st.image(p_path)
                    elif p_type == "video":
                        st.video(p_path)
                
                with st.expander("💬 التعليقات والمناقشة"):
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT student_name, comment_text, timestamp FROM comments WHERE post_id=? ORDER BY id DESC", (p_id,))
                        comms = c.fetchall()
                    
                    if comms:
                        for c_name, c_text, c_time in comms:
                            st.markdown(f"💬 **{c_name}**: {c_text} <small style='color:gray;'>({c_time})</small>", unsafe_allow_html=True)
                    else:
                        st.write("لا توجد تعليقات بعد. كن أول من يعلق!")

                    with st.form(f"comm_form_{p_id}", clear_on_submit=True):
                        c_text_input = st.text_input("أضف تعليقك:", key=f"txt_{p_id}")
                        c_btn = st.form_submit_button("تعليق", key=f"btn_c_{p_id}")
                        if c_btn and c_text_input:
                            t_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO comments (post_id, student_name, comment_text, timestamp) VALUES (?, ?, ?, ?)",
                                          (p_id, student_name, c_text_input, t_now))
                                conn.commit()
                            st.success("تم إضافة التعليق!")
                            st.rerun()

                st.write("---")
        else:
            st.info("لا توجد منشورات أو فيديوهات متاحة حالياً.")
    except Exception as e:
        st.info(f"جارٍ تحميل المحتوى... ({e})")

@st.fragment
def display_teacher_requests(teacher_phone):
    st_autorefresh(interval=2000, key=f"refresh_subs_{teacher_phone}")
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT student_phone, status, requested_at, expires_at FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
            subs = c.fetchall()
            
            if subs:
                now = datetime.datetime.now()
                for s_ph, status, req_at, expires_at in subs:
                    c.execute("SELECT name, age, grade FROM users WHERE phone=?", (s_ph,))
                    st_data = c.fetchone()
                    st_display_name = st_data[0] if st_data else s_ph
                    st_display_age = st_data[1] if st_data else "غير محدد"
                    st_display_grade = st_data[2] if st_data else "غير محدد"

                    time_left_str = "انتهى الوقت"
                    if req_at and status == 'pending':
                        try:
                            req_time = datetime.datetime.strptime(req_at, "%Y-%m-%d %H:%M:%S")
                            deadline = req_time + datetime.timedelta(hours=2)
                            diff = deadline - now
                            if diff.total_seconds() > 0:
                                hours, remainder = divmod(int(diff.total_seconds()), 3600)
                                minutes, seconds = divmod(remainder, 60)
                                time_left_str = f"⏳ باقي على القبول: {hours:02d}:{minutes:02d}:{seconds:02d}"
                            else:
                                time_left_str = "⌛ انتهت مهلة الساعتين"
                        except:
                            pass

                    status_text = "نشط ✅" if status == 'active' else f"قيد المراجعة ⏳ ({time_left_str})"
                    st.markdown(f"🎓 **{st_display_name}** | السن: {st_display_age} | المرحلة: {st_display_grade}")
                    st.markdown(f"📱 هاتف المحفظة المحول منها: `{s_ph}` | الحالة: **{status_text}**")
                    
                    col_act1, col_act2 = st.columns(2)
                    if status != 'active':
                        if col_act1.button(f"✅ قبول وتفعيل الاشتراك", key=f"acc_{s_ph}"):
                            exp_time = (now + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE subscriptions SET status='active', expires_at=? WHERE student_phone=? AND teacher_phone=?", (exp_time, s_ph, teacher_phone))
                            conn.commit()
                            st.success("تم قبول وتفعيل اشتراك الطالب بنجاح!")
                            st.rerun()
                    else:
                        if col_act1.button(f"⏳ تحويل لقيد المراجعة", key=f"pend_{s_ph}"):
                            c.execute("UPDATE subscriptions SET status='pending' WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                            st.warning("تم تحويل الاشتراك لقيد المراجعة.")
                            st.rerun()

                    if col_act2.button(f"❌ إلغاء / حذف", key=f"ref_{s_ph}"):
                        c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                        conn.commit()
                        st.warning("تم حذف طلب الطالب.")
                        st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد طلبات اشتراك حالياً.")
    except Exception as e:
        st.info(f"جارٍ تحديث الاشتراكات... ({e})")

@st.fragment
def render_student_teacher_card(t_name, t_sub, t_price, room_id, t_phone, student_phone):
    st_autorefresh(interval=2000, key=f"student_card_refresh_{t_phone}")
    
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown(f"### 👨‍🏫 الأستاذ: {t_name}")
    st.markdown(f"📖 **المادة:** {t_sub} | 💰 **السعر:** {t_price} جـ")
    
    sub_info = None
    st_current_name = "طالب"
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT status, requested_at, expires_at FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                      (student_phone, t_phone))
            sub_info = c.fetchone()
            
            c.execute("SELECT name FROM users WHERE phone=?", (student_phone,))
            st_u_row = c.fetchone()
            if st_u_row:
                st_current_name = st_u_row[0]
    except Exception as e:
        # معالجة آمنة لضمان عدم توقف التطبيق أو ظهور الخطأ
        pass

    sub_status = sub_info[0] if sub_info else None
    req_at = sub_info[1] if sub_info else None
    expires_at = sub_info[2] if sub_info else None

    is_expired = False
    if expires_at and sub_status == 'active':
        try:
            exp_dt = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > exp_dt:
                is_expired = True
        except:
            pass

    if sub_status == 'active' and not is_expired:
        st.success("✅ تم قبولك من الأستاذ! يمكنك مشاهدة الفيديوهات والبث المباشر والشات الآن.")
        
        if st.button("❌ إلغاء الاشتراك مع هذا الأستاذ", key=f"cancel_sub_{t_phone}"):
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (student_phone, t_phone))
                conn.commit()
            st.warning("تم إلغاء اشتراكك بنجاح.")
            st.rerun()

        tab_live, tab_media = st.tabs(["🔴 البث المباشر والشات", "🎬 الفيديوهات والتعليقات"])
        with tab_live:
            stream_html = f"""
            <iframe src="https://vdo.ninja/?view={room_id}&autostart=1" 
                    style="width: 100%; height: 320px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(stream_html, height=340)
            render_live_chat(room_id, st_current_name)
            
        with tab_media:
            display_student_media(t_phone, student_phone)
            
    elif sub_status == 'pending':
        now = datetime.datetime.now()
        time_left_display = "جاري الحساب..."
        if req_at:
            try:
                req_time = datetime.datetime.strptime(req_at, "%Y-%m-%d %H:%M:%S")
                deadline = req_time + datetime.timedelta(hours=2)
                diff = deadline - now
                if diff.total_seconds() > 0:
                    hours, remainder = divmod(int(diff.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_left_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    time_left_display = "انتهت مهلة الساعتين، بانتظار موافقة الأستاذ"
            except:
                pass

        st.warning(f"⏳ طلبك قيد المراجعة عند الأستاذ. العد التنازلي للمراجعة: **{time_left_display}**")
        
        col_p1, col_p2 = st.columns(2)
        if col_p1.button("🔄 تحديث الحالة", key=f"check_st_{t_phone}"):
            st.rerun()
            
        if col_p2.button("❌ إلغاء الطلب", key=f"del_pending_{t_phone}"):
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (student_phone, t_phone))
                conn.commit()
            st.warning("تم إلغاء الطلب بنجاح.")
            st.rerun()
    else:
        if is_expired:
            st.error("⏳ انتهى اشتراكك الشهري، يرجى إعادة إرسال رقم التحويل للتجديد.")
        else:
            st.info("⚠️ غير مشترك مع هذا الأستاذ. قم بتحويل المصاريف وأدخل رقم التحويل أدناه:")
            
        st.markdown(f"""
        <div class="cash-box">
            تحويل ({t_price} جـ) على محفظة (فودافون كاش / أورنج كاش): <b>01213783090</b>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form(f"cash_pay_form_{t_phone}"):
            cash_phone_used = st.text_input("أدخل رقم التليفون المحول منه الفلوس بدقة:", value=student_phone)
            pay_btn = st.form_submit_button("🚀 إرسال طلب الانضمام وبدء العد التنازلي (ساعتان)")
            
            if pay_btn:
                if cash_phone_used:
                    t_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status, requested_at) VALUES (?, ?, 'pending', ?)",
                                  (cash_phone_used, t_phone, t_now_str))
                        conn.commit()
                    st.success("✔️ تم إرسال الطلب وبدء العد التنازلي لمدة ساعتين بانتظار قبول الأستاذ!")
                    st.rerun()
                else:
                    st.error("يرجى إدخال رقم التليفون المحول منه!")
                    
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. الواجهة الرئيسية
# ==========================================
st.markdown("<h2 style='text-align: center;'>⚡ منصة نوفا التعليمية</h2>", unsafe_allow_html=True)
st.write("---")

if not st.session_state.is_logged_in:
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    role_choice = st.radio("حدد نوع الحساب:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑", "نسيت كلمة السر 🔑"], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("")

    if role_choice == "طالب 👨‍🎓":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        student_mode = st.radio("اختر العملية:", ["تسجيل دخول", "حساب جديد"], horizontal=True)
        st.write("---")
        
        if student_mode == "حساب جديد":
            with st.form("student_signup"):
                st.subheader("إنشاء حساب طالب جديد")
                s_name = st.text_input("الاسم الكامل:")
                s_email = st.text_input("البريد الإلكتروني:")
                s_pass = st.text_input("كلمة المرور:", type="password")
                s_phone = st.text_input("رقم المحمول:")
                s_age = st.text_input("السن:")
                s_grade = st.text_input("المرحلة الدراسية:")
                s_signup_btn = st.form_submit_button("تسجيل الحساب")
                
                if s_signup_btn:
                    if s_pass and s_phone:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM users WHERE phone=?", (s_phone,))
                                if c.fetchone():
                                    st.error("🚫 رقم المحمول مسجل مسبقاً في السيستم!")
                                else:
                                    hashed_pass = hash_password(s_pass)
                                    c.execute("INSERT INTO users (phone, email, password, name, age, grade, role, is_blocked) VALUES (?, ?, ?, ?, ?, ?, 'طالب', 0)", 
                                              (s_phone, s_email, hashed_pass, s_name if s_name else "طالب", s_age, s_grade))
                                    conn.commit()
                                    login_user(s_phone, "طالب")
                                    st.success("تم حفظ الطالب وتسجيل الدخول بنجاح!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"🚫 حدث خطأ: {e}")
                    else:
                        st.error("يرجى إدخال رقم المحمول وكلمة المرور!")
        
        else:
            with st.form("student_login"):
                st.subheader("تسجيل دخول الطالب")
                s_phone_in = st.text_input("رقم المحمول:")
                s_pass_in = st.text_input("كلمة المرور:", type="password")
                s_login_btn = st.form_submit_button("دخول")
                
                if s_login_btn:
                    if s_phone_in and s_pass_in:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                hashed_pass = hash_password(s_pass_in)
                                c.execute("SELECT phone, is_blocked FROM users WHERE phone=? AND password=? AND role='طالب'", (s_phone_in, hashed_pass))
                                user_row = c.fetchone()
                            
                            if user_row:
                                p_val, is_blocked = user_row
                                if is_blocked == 1:
                                    st.error("🚫 تم حظر هذا الحساب من قبل الإدارة ولا يمكنك الدخول!")
                                else:
                                    login_user(p_val, "طالب")
                                    st.success("تم الدخول بنجاح!")
                                    st.rerun()
                            else:
                                st.error("🚫 رقم المحمول أو كلمة المرور غير صحيحة!")
                        except Exception as e:
                            st.error(f"🚫 حدث خطأ: {e}")
                    else:
                        st.error("يرجى إدخال البيانات المطلوبة!")
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "أستاذ 👨‍🏫":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        teacher_mode = st.radio("اختر العملية:", ["تسجيل دخول الأستاذ", "حساب جديد للأستاذ"], horizontal=True)
        st.write("---")
        
        if teacher_mode == "حساب جديد للأستاذ":
            with st.form("teacher_signup"):
                st.subheader("إنشاء حساب أستاذ جديد")
                t_name_reg = st.text_input("اسم الأستاذ:")
                t_phone_reg = st.text_input("رقم المحمول:")
                t_sub_reg = st.text_input("المادة الدراسية:")
                t_secret_code = st.text_input("الكود السري:", type="password")
                t_signup_btn = st.form_submit_button("إنشاء الحساب")
                
                if t_signup_btn:
                    correct_teacher_code = get_setting("teacher_secret", "901000")
                    if t_secret_code.strip() != correct_teacher_code:
                        st.error("🚫 الكود السري غير صحيح!")
                    elif t_phone_reg and t_name_reg:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("SELECT id FROM teachers WHERE phone=?", (t_phone_reg,))
                                if c.fetchone():
                                    st.error("🚫 رقم المحمول مسجل مسبقاً!")
                                else:
                                    hashed_t_pass = hash_password(t_secret_code)
                                    c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id, is_blocked) 
                                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""", 
                                              (t_phone_reg, hashed_t_pass, t_name_reg, t_sub_reg if t_sub_reg else "غير محدد", 'جميع المراحل', 30, 100.0, '', f"room_{t_phone_reg}"))
                                    c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (t_phone_reg, t_name_reg))
                                    conn.commit()
                                    login_user(t_phone_reg, "أستاذ")
                                    st.success("تم التسجيل بنجاح!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")
                    else:
                        st.error("أدخل اسم الأستاذ ورقم المحمول والكود السري!")
        
        else:
            with st.form("teacher_login"):
                st.subheader("تسجيل دخول الأستاذ")
                t_phone_in = st.text_input("رقم المحمول:")
                t_secret_in = st.text_input("كلمة المرور أو الكود السري:", type="password")
                t_login_btn = st.form_submit_button("دخول الأستاذ")
                
                if t_login_btn:
                    correct_teacher_code = get_setting("teacher_secret", "901000")
                    if t_phone_in:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                hashed_t_pass = hash_password(t_secret_in)
                                c.execute("SELECT phone, is_blocked FROM teachers WHERE phone=? AND (password=? OR ?=?)", (t_phone_in, hashed_t_pass, t_secret_in, correct_teacher_code))
                                t_row = c.fetchone()
                            
                            if t_row:
                                p_val, t_blocked = t_row
                                if t_blocked == 1:
                                    st.error("🚫 هذا الحساب محظور!")
                                else:
                                    login_user(p_val, "أستاذ")
                                    st.success("تم الدخول بنجاح!")
                                    st.rerun()
                            else:
                                st.error("🚫 رقم المحمول أو كلمة المرور غير صحيحة!")
                        except Exception as e:
                            st.error(f"🚫 حدث خطأ: {e}")
                    else:
                        st.error("يرجى إدخال البيانات!")
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "مطور 👑":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        with st.form("dev_reg"):
            st.subheader("تسجيل دخول المطور الرئيسي")
            dev_code = st.text_input("كود المطور السري:", type="password")
            dev_btn = st.form_submit_button("دخول لوحة التحكم")
            
            if dev_btn:
                correct_dev_code = "900800"
                if dev_code.strip() == correct_dev_code:
                    login_user("dev_admin", "مطور")
                    st.success("أهلاً بك يا مطورنا!")
                    st.rerun()
                else:
                    st.error("🚫 كود المطور غير صحيح!")
        st.markdown("</div>", unsafe_allow_html=True)

    elif role_choice == "نسيت كلمة السر 🔑":
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        st.subheader("استعادة كلمة المرور")
        reset_step = st.radio("الخطوة:", ["1. إرسال كود التأكيد", "2. تعيين كلمة سر جديدة"], horizontal=True)
        reset_phone = st.text_input("أدخل رقم المحمول:")
        
        if reset_step == "1. إرسال كود التأكيد":
            if st.button("إرسال الرمز"):
                if reset_phone:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT phone FROM users WHERE phone=?", (reset_phone,))
                        if c.fetchone():
                            gen_code = str(random.randint(1000, 9999))
                            c.execute("INSERT OR REPLACE INTO password_resets (phone, code) VALUES (?, ?)", (reset_phone, gen_code))
                            conn.commit()
                            st.info(f"كود التأكيد الخاص بك هو: **{gen_code}**")
                        else:
                            st.error("🚫 رقم المحمول غير مسجل!")
                else:
                    st.error("أدخل رقم المحمول.")
        else:
            code_input = st.text_input("كود التأكيد:")
            new_password_input = st.text_input("كلمة السر الجديدة:", type="password")
            if st.button("تحديث كلمة السر"):
                if reset_phone and code_input and new_password_input:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT code FROM password_resets WHERE phone=?", (reset_phone,))
                        row_res = c.fetchone()
                        if row_res and row_res[0] == code_input:
                            hashed_new_pass = hash_password(new_password_input)
                            c.execute("UPDATE users SET password=? WHERE phone=?", (hashed_new_pass, reset_phone))
                            c.execute("DELETE FROM password_resets WHERE phone=?", (reset_phone,))
                            conn.commit()
                            st.success("✔️ تم تغيير كلمة المرور بنجاح!")
                        else:
                            st.error("🚫 كود التأكيد غير صحيح!")
                else:
                    st.error("املأ جميع الحقول.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"مرحباً بك: **{st.session_state.user_role}**")
    if logout_col.button("🚪 خروج"):
        logout_user()
        st.rerun()

    # ------------------------------------------
    # واجهة الطالب (مع زر الإبلاغ وإلغاء الاشتراك)
    # ------------------------------------------
    if st.session_state.user_role == "طالب":
        st.subheader("🎓 الأساتذة المتاحون في السيستم")
        
        with st.expander("🚨 هل تواجه مشكلة؟ أرسل بلاغاً أو رسالة للمطور"):
            with st.form("student_report_form"):
                rep_msg = st.text_area("اكتب تفاصيل المشكلة أو الشكوى:")
                rep_btn = st.form_submit_button("إرسال البلاغ للمطور")
                if rep_btn and rep_msg:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT name FROM users WHERE phone=?", (st.session_state.user_phone,))
                        st_n_row = c.fetchone()
                        s_name_rep = st_n_row[0] if st_n_row else "طالب"
                        t_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO reports (student_phone, student_name, message, timestamp, status) VALUES (?, ?, ?, ?, 'pending')",
                                  (st.session_state.user_phone, s_name_rep, rep_msg, t_now_str))
                        conn.commit()
                    st.success("✔️ تم إرسال رسالتك وبلاغك للمطور بنجاح وسيتم المراجعة!")
                elif rep_btn:
                    st.error("يرجى كتابة نص الرسالة أولاً.")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id, phone FROM teachers WHERE is_blocked=0")
            teachers = c.fetchall()

        if teachers:
            for t in teachers:
                t_name, t_sub, t_grade, t_age, t_price, t_img, room_id, t_phone = t
                render_student_teacher_card(t_name, t_sub, t_price, room_id, t_phone, st.session_state.user_phone)
        else:
            st.info("لا توجد أساتذة متاحين حالياً.")

    # ------------------------------------------
    # واجهة الأستاذ
    # ------------------------------------------
    elif st.session_state.user_role == "أستاذ":
        st.subheader("👨‍🏫 استوديو الأستاذ")
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id FROM teachers WHERE phone=?", (st.session_state.user_phone,))
            t_info = c.fetchone()
        room_id = t_info[6] if t_info else f"room_{st.session_state.user_phone}"

        tab_stream, tab_post, tab_manage_posts, tab_subs, tab_students_ctrl, tab_prof = st.tabs([
            "🔴 البث والشات", "📤 نشر محتوى", "🗑️ إدارة الفيديوهات", "👥 طلبات الاشتراكات والعد التنازلي", "🚫 إدارة وحظر الطلاب", "⚙️ الإعدادات"
        ])

        with tab_stream:
            st.info("بث مباشر مع شات تفاعلي للطلاب:")
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                t_stream_html = f"""
                <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1" 
                        style="width: 100%; height: 350px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                        allow="camera; microphone; autoplay" allowfullscreen>
                </iframe>
                """
                components.html(t_stream_html, height=370)
            with col_s2:
                render_live_chat(room_id, "الأستاذ")

        with tab_post:
            p_title = st.text_input("عنوان الفيديو أو المحتوى:")
            up_file = st.file_uploader("اختر فيديو أو صورة:", type=["png", "jpg", "jpeg", "mp4"])
            if st.button("🚀 رفع المحتوى"):
                if up_file and p_title:
                    file_path = os.path.join(MEDIA_DIR, up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    f_type = "video" if up_file.type.startswith("video") else "image"
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, status, views_count) VALUES (?, ?, ?, ?, 'approved', 0)",
                                  (st.session_state.user_phone, p_title, f_type, file_path))
                        conn.commit()
                    st.success("✔️ تم رفع ونشر المحتوى بنجاح!")
                    st.rerun()

        with tab_manage_posts:
            st.write("🗑️ **قائمة فيديوهاتك ومنشوراتك:**")
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT id, title, media_type, file_path, views_count FROM posts WHERE teacher_phone=?", (st.session_state.user_phone,))
                my_posts = c.fetchall()

            if my_posts:
                for mp_id, mp_title, mp_type, mp_path, mp_views in my_posts:
                    st.markdown(f"📌 **العنوان:** {mp_title} | 👁️ **المشاهدات:** {mp_views}")
                    if os.path.exists(mp_path):
                        if mp_type == "image":
                            st.image(mp_path, width=200)
                        elif mp_type == "video":
                            st.video(mp_path)
                    
                    if st.button(f"🗑️ مسح هذا الفيديو نهائياً", key=f"del_post_{mp_id}"):
                        try:
                            if os.path.exists(mp_path):
                                os.remove(mp_path)
                        except:
                            pass
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM posts WHERE id=?", (mp_id,))
                            c.execute("DELETE FROM comments WHERE post_id=?", (mp_id,))
                            conn.commit()
                        st.success("تم مسح الفيديو نهائياً!")
                        st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد فيديوهات مرفوعة.")

        with tab_subs:
            display_teacher_requests(st.session_state.user_phone)

        with tab_students_ctrl:
            st.write("🚫 **إدارة وحظر الطلاب:**")
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT phone, name, is_blocked FROM users WHERE role='طالب'")
                all_students = c.fetchall()
            
            if all_students:
                for st_ph, st_name, st_bl in all_students:
                    st.markdown(f"👤 **{st_name}** | هاتف: `{st_ph}` | الحظـر: **{'محظور 🚫' if st_bl == 1 else 'نشط ✅'}**")
                    col_b1, col_b2 = st.columns(2)
                    if st_bl == 0:
                        if col_b1.button("🚫 حظر الطالب", key=f"block_st_{st_ph}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE users SET is_blocked=1 WHERE phone=?", (st_ph,))
                                conn.commit()
                            st.warning("تم حظر الطالب ولن يمكنه الدخول مرة أخرى!")
                            st.rerun()
                    else:
                        if col_b1.button("✅ إلغاء الحظر", key=f"unblock_st_{st_ph}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE users SET is_blocked=0 WHERE phone=?", (st_ph,))
                                conn.commit()
                            st.success("تم رفع الحظر عن الطالب!")
                            st.rerun()
                            
                    if col_b2.button("🗑️ حذف الحساب نهائياً", key=f"del_st_{st_ph}"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM users WHERE phone=?", (st_ph,))
                            c.execute("DELETE FROM subscriptions WHERE student_phone=?", (st_ph,))
                            conn.commit()
                        st.error("تم حذف حساب الطالب نهائياً من السيستم!")
                        st.rerun()
                    st.write("---")
            else:
                st.info("لا يوجد طلاب مسجلون حالياً.")

        with tab_prof:
            with st.form("prof_form"):
                name_in = st.text_input("الاسم:", value=t_info[0] if t_info else "")
                sub_in = st.text_input("المادة:", value=t_info[1] if t_info else "")
                price_in = st.number_input("السعر (جـ):", value=float(t_info[4]) if t_info and t_info[4] else 100.0)
                if st.form_submit_button("حفظ التعديلات"):
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE teachers SET name=?, subject=?, price=? WHERE phone=?",
                                  (name_in, sub_in, price_in, st.session_state.user_phone))
                        conn.commit()
                    st.success("تم الحفظ!")
                    st.rerun()

    # ------------------------------------------
    # واجهة المطور
    # ------------------------------------------
    elif st.session_state.user_role == "مطور":
        st.subheader("👑 لوحة تحكم المطور الشاملة")
        dev_tab1, dev_tab2, dev_tab3, dev_tab4 = st.tabs(["🎥 مراجعة المحتوى", "🚨 بلاغات الطلاب وشكاواهم", "👨‍🏫 إضافة وإدارة الأساتذة", "👥 إدارة وحذف كل المستخدمين"])
        
        with dev_tab1:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT id, teacher_phone, title, media_type, file_path FROM posts WHERE status='pending'")
                pending_posts = c.fetchall()
            
            if pending_posts:
                for p_id, p_teacher, p_title, p_type, p_path in pending_posts:
                    st.markdown(f"📱 **أستاذ:** {p_teacher} | 📌 **العنوان:** {p_title}")
                    if os.path.exists(p_path):
                        if p_type == "image":
                            st.image(p_path, width=250)
                        elif p_type == "video":
                            st.video(p_path)
                    col_ok, col_no = st.columns(2)
                    if col_ok.button(f"✅ موافقة", key=f"app_{p_id}"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE posts SET status='approved' WHERE id=?", (p_id,))
                            conn.commit()
                        st.rerun()
                    if col_no.button(f"❌ رفض", key=f"rej_{p_id}"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM posts WHERE id=?", (p_id,))
                            conn.commit()
                        st.rerun()
            else:
                st.info("لا يوجد محتوى معلق للمراجعة.")

        with dev_tab2:
            st.write("🚨 **بلاغات ورسائل الطلاب الواردة للمطور:**")
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT id, student_phone, student_name, message, timestamp, status FROM reports ORDER BY id DESC")
                all_reports = c.fetchall()

            if all_reports:
                for r_id, r_ph, r_name, r_msg, r_time, r_st in all_reports:
                    st.markdown(f"👤 **الطالب:** {r_name} (`{r_ph}`) | ⏰ **الوقت:** {r_time}")
                    st.markdown(f"💬 **محتوى البلاغ أو الرسالة:** {r_msg}")
                    st.markdown(f"حالة البلاغ: **{'تمت معالجته ✅' if r_st == 'resolved' else 'قيد المراجعة ⏳'}**")
                    
                    with st.form(f"report_action_form_{r_id}"):
                        block_reason = st.text_input("سبب الحظر أو الرد على البلاغ (اختياري):", key=f"reason_{r_id}")
                        col_r1, col_r2 = st.columns(2)
                        
                        r_block_btn = col_r1.form_submit_button("🚫 حظر الطالب لهذا السبب")
                        r_resolve_btn = col_r2.form_submit_button("✅ تم حل المشكلة / وضع علامة مقروء")
                        
                        if r_block_btn:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE users SET is_blocked=1 WHERE phone=?", (r_ph,))
                                c.execute("UPDATE reports SET status='resolved' WHERE id=?", (r_id,))
                                conn.commit()
                            st.warning(f"تم حظر الطالب بنجاح. السبب المسجل: {block_reason}")
                            st.rerun()
                            
                        if r_resolve_btn:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE reports SET status='resolved' WHERE id=?", (r_id,))
                                conn.commit()
                            st.success("تم تحديث حالة البلاغ بنجاح.")
                            st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد بلاغات مرسلة من الطلاب حالياً.")

        with dev_tab3:
            st.write("➕ **إضافة أستاذ جديد للسيستم:**")
            with st.form("add_teacher_dev"):
                new_t_name = st.text_input("اسم الأستاذ:")
                new_t_phone = st.text_input("رقم المحمول:")
                new_t_sub = st.text_input("المادة الدراسية:")
                new_t_price = st.number_input("سعر الاشتراك (جـ):", value=100.0)
                add_t_btn = st.form_submit_button("إضافة الأستاذ فوراً")
                
                if add_t_btn:
                    if new_t_phone and new_t_name:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT id FROM teachers WHERE phone=?", (new_t_phone,))
                            if c.fetchone():
                                st.error("رقم المحمول مسجل مسبقاً!")
                            else:
                                hashed_tp = hash_password("901000")
                                c.execute("""INSERT INTO teachers (phone, password, name, subject, grade_level, age, price, image_url, room_id, is_blocked) 
                                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                                          (new_t_phone, hashed_tp, new_t_name, new_t_sub, 'جميع المراحل', 30, new_t_price, '', f"room_{new_t_phone}"))
                                c.execute("INSERT OR IGNORE INTO users (phone, name, role, is_blocked) VALUES (?, ?, 'أستاذ', 0)", (new_t_phone, new_t_name))
                                conn.commit()
                                st.success("✔️ تم إضافة الأستاذ بنجاح!")
                                st.rerun()
                    else:
                        st.error("يرجى ملء الحقول المطلوبة.")

        with dev_tab4:
            st.write("👥 **التحكم في كافة مستخدمي السيستم (حظر أو حذف نهائي):**")
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT phone, name, role, is_blocked FROM users")
                all_users = c.fetchall()

            if all_users:
                for u_ph, u_name, u_role, u_bl in all_users:
                    st.markdown(f"👤 **{u_name}** ({u_role}) | الهاتف: `{u_ph}` | الحالة: **{'محظور 🚫' if u_bl == 1 else 'نشط ✅'}**")
                    col_u1, col_u2 = st.columns(2)
                    if u_bl == 0:
                        if col_u1.button("🚫 حظر المستخدم", key=f"dev_block_{u_ph}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("users SET is_blocked=1 WHERE phone=?", (u_ph,))
                                c.execute("UPDATE teachers SET is_blocked=1 WHERE phone=?", (u_ph,))
                                conn.commit()
                            st.warning("تم حظر المستخدم!")
                            st.rerun()
                    else:
                        if col_u1.button("✅ إلغاء الحظر", key=f"dev_unblock_{u_ph}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE users SET is_blocked=0 WHERE phone=?", (u_ph,))
                                c.execute("UPDATE teachers SET is_blocked=0 WHERE phone=?", (u_ph,))
                                conn.commit()
                            st.success("تم إزالة الحظر!")
                            st.rerun()

                    if col_u2.button("🗑️ حذف المستخدم نهائياً", key=f"dev_del_{u_ph}"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM users WHERE phone=?", (u_ph,))
                            c.execute("DELETE FROM teachers WHERE phone=?", (u_ph,))
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? OR teacher_phone=?", (u_ph, u_ph))
                            conn.commit()
                        st.error("تم حذف المستخدم تماماً من قاعدة البيانات!")
                        st.rerun()
                    st.write("---")
            else:
                st.info("لا يوجد مستخدمون مسجلون.")
