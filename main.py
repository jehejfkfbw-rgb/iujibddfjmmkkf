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
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO live_chat (room_id, sender_name, message, timestamp) VALUES (?, ?, ?, ?)",
                              (room_id, user_name, msg, t_now))
                    conn.commit()
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في الإرسال: {e}")

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
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            # استخدام الاستعلام الآمن لتجنب أي أخطاء في الجدول
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (cash_phone_used, t_phone))
                            c.execute("INSERT INTO subscriptions (student_phone, teacher_phone, status, requested_at) VALUES (?, ?, 'pending', ?)",
                                      (cash_phone_used, t_phone, t_now_str))
                            conn.commit()
                        st.success("✔️ تم إرسال الطلب وبدء العد التنازلي لمدة ساعتين بانتظار قبول الأستاذ!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"🚫 حدث خطأ أثناء إرسال الطلب: {e}")
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
