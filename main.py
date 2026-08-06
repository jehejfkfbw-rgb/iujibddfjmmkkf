import streamlit as st
import streamlit.components.v1 as components
import sqlite3

# ==================== 1. إعداد قاعدة البيانات ====================
DB_NAME = 'nova_final_v2.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            is_blocked INTEGER DEFAULT 0
        )
    ''')
    
    # جدول الأساتذة (يشمل العمر والمرحلة الدراسية)
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            subject TEXT,
            grade_level TEXT,
            age INTEGER,
            price REAL,
            image_url TEXT,
            room_id TEXT
        )
    ''')
    
    # جدول الاشتراكات
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT,
            teacher_email TEXT,
            status TEXT DEFAULT 'pending',
            UNIQUE(student_email, teacher_email)
        )
    ''')
    
    # جدول المنشورات والفيديوهات
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_email TEXT,
            title TEXT,
            media_type TEXT,
            media_data BLOB
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ==================== 2. التصميم والواجهة الفاتحة الحديثة ====================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* خلفية التطبيق العامة بالكامل */
    .stApp {
        direction: rtl;
        text-align: right;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
        color: #0f172a !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* ألوان النصوص والعناوين */
    label, p, span, h1, h2, h3, h4, div {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* شكل حقول الإدخال (الكود، الإيميل، الباسورد) */
    .stTextInput input, .stNumberInput input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05) !important;
    }

    /* أزرار التشغيل والتسجيل */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px);
    }

    /* الكروت الحاوية */
    .card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08) !important;
        margin-bottom: 20px !important;
    }

    /* صندوق فودافون كاش */
    .cash-box {
        background: #16a34a !important;
        color: #ffffff !important;
        padding: 14px !important;
        border-radius: 12px !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 16px !important;
        margin: 12px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. حفظ الجلسة (تسجيل دخول دائم مرة واحدة) ====================
params = st.query_params

if "user_email" in params and "user_role" in params:
    st.session_state.is_logged_in = True
    st.session_state.user_email = params["user_email"]
    st.session_state.user_role = params["user_role"]
else:
    if "is_logged_in" not in st.session_state:
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

st.title("⚡ منصة نوفا التعليمية")
st.write("---")

# ==================== 4. شاشات تسجيل الدخول ====================
if not st.session_state.is_logged_in:
    role = st.radio("اختر نوع الدخول:", ["أستاذ 👨‍🏫", "طالب 👨‍🎓", "المطور التنفيذي 👑"], horizontal=True)
    st.write("---")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. الأستاذ (كود 90100 + إيميل + باسورد)
    if role == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 تسجيل دخول الأستاذ")
        with st.form("teacher_login"):
            t_code = st.text_input("الكود السري للأستاذ:", type="password")
            t_email = st.text_input("البريد الإلكتروني:")
            t_pass = st.text_input("كلمة السر:", type="password")
            if st.form_submit_button("دخول الأستاذ"):
                c.execute("SELECT is_blocked FROM users WHERE email=?", (t_email,))
                user_status = c.fetchone()
                if user_status and user_status[0] == 1:
                    st.error("🚫 هذا الحساب محظور من قبل المطور!")
                elif t_code.strip() == "90100" and t_email and t_pass:
                    try:
                        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, 'أستاذ')", (t_email, t_pass))
                        c.execute("INSERT INTO teachers (email, name, subject, grade_level, age, price, image_url, room_id) VALUES (?, ?, 'غير محدد', 'جميع المراحل', 30, 100, '', ?)", 
                                  (t_email, t_email.split('@')[0], f"room_{t_email.split('@')[0]}"))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        pass
                    save_login(t_email, "أستاذ")
                    st.rerun()
                else:
                    st.error("الكود السري (90100) أو البيانات غير صحيحة!")

    # 2. الطالب (إيميل + باسورد)
    elif role == "طالب 👨‍🎓":
        st.subheader("👨‍🎓 تسجيل دخول الطالب")
        with st.form("student_login"):
            s_email = st.text_input("البريد الإلكتروني:")
            s_pass = st.text_input("كلمة السر:", type="password")
            if st.form_submit_button("دخول الطالب"):
                c.execute("SELECT is_blocked FROM users WHERE email=?", (s_email,))
                user_status = c.fetchone()
                if user_status and user_status[0] == 1:
                    st.error("🚫 حسابك محظور من استخدام المنصة!")
                elif s_email and s_pass:
                    try:
                        c.execute("INSERT INTO users (email, password, role) VALUES (?, ?, 'طالب')", (s_email, s_pass))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        pass
                    save_login(s_email, "طالب")
                    st.rerun()
                else:
                    st.error("يرجى إدخال البريد الإلكتروني وكلمة السر!")

    # 3. المطور (كود 900800 فقط)
    elif role == "المطور التنفيذي 👑":
        st.subheader("👑 دخول المطور")
        with st.form("dev_login"):
            dev_code = st.text_input("الكود السري للمطور:", type="password")
            if st.form_submit_button("دخول لوحة التحكم"):
                if dev_code.strip() == "900800":
                    save_login("admin@nova.com", "مطور")
                    st.rerun()
                else:
                    st.error("الكود السري للمطور غير صحيح!")
    conn.close()

# ==================== 5. اللوحات والواجهات الداخلية ====================
else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"مرحباً بك: **{st.session_state.user_role}** ({st.session_state.user_email})")
    if logout_col.button("🚪 تسجيل الخروج"):
        logout()
        st.rerun()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ---------------- A. واجهة الطالب ----------------
    if st.session_state.user_role == "طالب":
        st.subheader("🎓 قائمة الأساتذة والمواد الدراسية")
        
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id, email FROM teachers")
        teachers = c.fetchall()

        if teachers:
            for t in teachers:
                t_name, t_sub, t_grade, t_age, t_price, t_img, room_id, t_email = t
                
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if t_img:
                        st.image(t_img, width=130)
                    else:
                        st.title("👨‍🏫")
                
                with col2:
                    st.markdown(f"### الأستاذ: {t_name}")
                    st.markdown(f"📖 **المادة:** {t_sub} | 🏫 **المرحلة:** {t_grade}")
                    st.markdown(f"🎂 **العمر:** {t_age} سنة | 💰 **سعر الاشتراك:** {t_price} جنيه")
                
                # فحص حالة الاشتراك
                c.execute("SELECT status FROM subscriptions WHERE student_email=? AND teacher_email=?", 
                          (st.session_state.user_email, t_email))
                sub_status = c.fetchone()

                if sub_status and sub_status[0] == 'active':
                    st.success("✅ أنت مشترك في مادة هذا الأستاذ - يمكنك مشاهدة البث والفيديوهات")
                    
                    tab_live, tab_media = st.tabs(["🔴 البث المباشر", "🎬 الفيديوهات والمنشورات"])
                    
                    with tab_live:
                        st.write("🎙️ **شاشة البث المباشر للأستاذ:**")
                        stream_html = f"""
                        <iframe src="https://vdo.ninja/?view={room_id}&autostart=1" 
                                style="width: 100%; height: 430px; border: 2px solid #2563eb; border-radius: 12px; background: #000;"
                                allow="camera; microphone; autoplay" allowfullscreen>
                        </iframe>
                        """
                        components.html(stream_html, height=450)
                        
                    with tab_media:
                        c.execute("SELECT title, media_type, media_data FROM posts WHERE teacher_email=?", (t_email,))
                        posts = c.fetchall()
                        if posts:
                            for p_title, p_type, p_data in posts:
                                st.write(f"📌 **{p_title}**")
                                if p_type == "image":
                                    st.image(p_data)
                                elif p_type == "video":
                                    st.video(p_data)
                        else:
                            st.info("لا توجد منشورات أو فيديوهات نزلها الأستاذ حتى الآن.")
                            
                elif sub_status and sub_status[0] == 'pending':
                    st.warning("⏳ طلب اشتراكك قيد المراجعة والموافقة من الأستاذ.")
                else:
                    st.markdown(f"""
                    <div class="cash-box">
                        💸 للاشتراك ومشاهدة البث والفيديوهات: قم بتحويل المبلغ ({t_price} جنيه) على رقم فودافون كاش: <b>01213783090</b>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🚀 طلب الاشتراك مع الأستاذ {t_name}", key=f"btn_{t_email}"):
                        c.execute("INSERT OR REPLACE INTO subscriptions (student_email, teacher_email, status) VALUES (?, ?, 'pending')",
                                  (st.session_state.user_email, t_email))
                        conn.commit()
                        st.success("تم إرسال طلب الاشتراك! في انتظار موافقة الأستاذ.")
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("لا يوجد أساتذة مسجلون حالياً.")

    # ---------------- B. واجهة الأستاذ ----------------
    elif st.session_state.user_role == "أستاذ":
        st.subheader("👨‍🏫 استوديو إدارة الدروس والبث")
        
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id FROM teachers WHERE email=?", (st.session_state.user_email,))
        t_info = c.fetchone()
        room_id = t_info[6] if t_info else f"room_{st.session_state.user_email.split('@')[0]}"

        tab_stream, tab_post, tab_subs, tab_prof = st.tabs(["🔴 البث المباشر", "📤 نشر محتوى", "👥 طلبات الطلاب", "⚙️ بياناتي الشخصية"])

        # 1. البث المباشر
        with tab_stream:
            st.write("📹 **استوديو تشغيل الكاميرا والمايك لبدء البث للطلاب:**")
            t_stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1" 
                    style="width: 100%; height: 450px; border: 2px solid #2563eb; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(t_stream_html, height=470)

        # 2. نشر فيديو أو صورة
        with tab_post:
            p_title = st.text_input("عنوان الفيديو أو الشرح:")
            up_file = st.file_uploader("اختر فيديو أو صورة من جهازك:", type=["png", "jpg", "jpeg", "mp4"])
            if st.button("🚀 نشر للمشتركين"):
                if up_file and p_title:
                    file_bytes = up_file.read()
                    f_type = "video" if up_file.type.startswith("video") else "image"
                    c.execute("INSERT INTO posts (teacher_email, title, media_type, media_data) VALUES (?, ?, ?, ?)",
                              (st.session_state.user_email, p_title, f_type, file_bytes))
                    conn.commit()
                    st.success("تم النشر بنجاح! سيظهر فوراً للطلاب المشتركين معهم.")
                    st.rerun()

        # 3. إدارة طلبات اشتراك الطلاب
        with tab_subs:
            st.write("📋 **الطلاب المتقدمين للاشتراك بعد التحويل:**")
            c.execute("SELECT student_email, status FROM subscriptions WHERE teacher_email=?", (st.session_state.user_email,))
            subs = c.fetchall()
            if subs:
                for s_email, status in subs:
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    col_a.write(f"🎓 الطالب: **{s_email}** (الحالة: {status})")
                    if status == 'pending':
                        if col_b.button("✅ قبول وتفعيل", key=f"acc_{s_email}"):
                            c.execute("UPDATE subscriptions SET status='active' WHERE student_email=? AND teacher_email=?", (s_email, st.session_state.user_email))
                            conn.commit()
                            st.rerun()
                        if col_c.button("❌ رفض", key=f"ref_{s_email}"):
                            c.execute("DELETE FROM subscriptions WHERE student_email=? AND teacher_email=?", (s_email, st.session_state.user_email))
                            conn.commit()
                            st.rerun()
            else:
                st.info("لا توجد طلبات اشتراك حالياً.")

        # 4. تعديل البيانات الشخصية
        with tab_prof:
            with st.form("prof_form"):
                name_in = st.text_input("الاسم الكامل:", value=t_info[0] if t_info else "")
                sub_in = st.text_input("المادة الدراسية:", value=t_info[1] if t_info else "")
                grade_in = st.text_input("المرحلة الدراسية (مثلاً: الثانوية العامة):", value=t_info[2] if t_info else "")
                age_in = st.number_input("العمر:", value=int(t_info[3]) if t_info and t_info[3] else 30)
                price_in = st.number_input("سعر الاشتراك (جنيه):", value=float(t_info[4]) if t_info and t_info[4] else 100.0)
                img_in = st.text_input("رابط صورتك الشخصية (URL):", value=t_info[5] if t_info else "")
                
                if st.form_submit_button("حفظ وتحديث البيانات"):
                    c.execute("UPDATE teachers SET name=?, subject=?, grade_level=?, age=?, price=?, image_url=? WHERE email=?",
                              (name_in, sub_in, grade_in, age_in, price_in, img_in, st.session_state.user_email))
                    conn.commit()
                    st.success("تم تحديث البيانات وصورتك بنجاح!")
                    st.rerun()

    # ---------------- C. لوحة تحكم المطور ----------------
    elif st.session_state.user_role == "مطور":
        st.subheader("👑 لوحة التحكم المركزية للمطور")
        
        c.execute("SELECT COUNT(*) FROM users WHERE role='طالب'")
        st_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE role='أستاذ'")
        tc_count = c.fetchone()[0]
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("إجمالي الطلاب", st_count)
        col_m2.metric("إجمالي الأساتذة", tc_count)
        
        st.write("---")
        st.write("🚫 **إدارة المستخدمين والحظر:**")
        
        c.execute("SELECT id, email, role, is_blocked FROM users WHERE role != 'مطور'")
        users = c.fetchall()
        
        if users:
            for u_id, u_email, u_role, is_blocked in users:
                u_col1, u_col2, u_col3 = st.columns([2, 1, 1])
                u_col1.write(f"👤 **{u_email}** ({u_role})")
                
                if is_blocked == 1:
                    u_col2.error("محظور 🚫")
                    if u_col3.button("فك الحظر", key=f"unblock_{u_id}"):
                        c.execute("UPDATE users SET is_blocked=0 WHERE id=?", (u_id,))
                        conn.commit()
                        st.rerun()
                else:
                    u_col2.success("نشط ✅")
                    if u_col3.button("حظر المستخدم", key=f"block_{u_id}"):
                        c.execute("UPDATE users SET is_blocked=1 WHERE id=?", (u_id,))
                        conn.commit()
                        st.rerun()
        
    conn.close()

st.write("---")
st.caption("⚡ منصة نوفا التعليمية © 2026")
