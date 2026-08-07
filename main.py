import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import os

MEDIA_DIR = "uploaded_media"
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

DB_NAME = 'nova_persistent_v15.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            name TEXT,
            role TEXT,
            grade TEXT,
            is_blocked INTEGER DEFAULT 0
        )
    ''')
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_phone TEXT,
            teacher_phone TEXT,
            status TEXT DEFAULT 'pending',
            UNIQUE(student_phone, teacher_phone)
        )
    ''')
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

st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
        color: #0f172a !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    label, p, span, h1, h2, h3, h4, div {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    .stTextInput input, .stNumberInput input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
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
    }
    .card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08) !important;
        margin-bottom: 20px !important;
    }
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

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.user_role = None
    st.session_state.user_phone = ""

auto_login_js = """
<script>
    const savedPhone = localStorage.getItem("nova_phone");
    const savedRole = localStorage.getItem("nova_role");
    if (savedPhone && savedRole && !window.location.search.includes("autologin=1")) {
        window.location.href = window.location.pathname + "?autologin=1&phone=" + encodeURIComponent(savedPhone) + "&role=" + encodeURIComponent(savedRole);
    }
</script>
"""
components.html(auto_login_js, height=0)

q_params = st.query_params
if not st.session_state.is_logged_in and q_params.get("autologin") == "1":
    p_phone = q_params.get("phone")
    p_role = q_params.get("role")
    if p_phone and p_role:
        st.session_state.is_logged_in = True
        st.session_state.user_phone = p_phone
        st.session_state.user_role = p_role

st.title("⚡ منصة نوفا التعليمية")
st.write("---")

if not st.session_state.is_logged_in:
    role_choice = st.radio("اختر صففتك في المنصة:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "مطور 👑"], horizontal=True)
    st.write("---")

    if role_choice == "طالب 👨‍🎓":
        st.subheader("👨‍🎓 تسجيل دخول الطالب (مرة واحدة)")
        with st.form("student_reg"):
            s_phone = st.text_input("رقم التليفون:")
            s_name = st.text_input("الاسم الكامل:")
            s_grade = st.text_input("سنتك كام (المرحلة الدراسية):")
            s_btn = st.form_submit_button("دخول المنصة")
            
            if s_btn:
                if s_phone and s_name:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    try:
                        c.execute("INSERT OR REPLACE INTO users (phone, name, role, grade) VALUES (?, ?, 'طالب', ?)", (s_phone, s_name, s_grade))
                        conn.commit()
                    except:
                        pass
                    conn.close()

                    st.session_state.is_logged_in = True
                    st.session_state.user_phone = s_phone
                    st.session_state.user_role = "طالب"

                    set_js = f"""
                    <script>
                        localStorage.setItem("nova_phone", "{s_phone}");
                        localStorage.setItem("nova_role", "طالب");
                        window.location.href = window.location.pathname + "?autologin=1&phone=" + encodeURIComponent("{s_phone}") + "&role=طالب";
                    </script>
                    """
                    components.html(set_js, height=0)
                    st.rerun()
                else:
                    st.error("يرجى إدخال رقم التليفون والاسم على الأقل!")

    elif role_choice == "أستاذ 👨‍🏫":
        st.subheader("👨‍🏫 دخول الأستاذ (بالكود السري)")
        with st.form("teacher_reg"):
            t_phone = st.text_input("رقم التليفون:")
            t_name = st.text_input("الاسم:")
            t_code = st.text_input("الكود السري (90100):", type="password")
            t_btn = st.form_submit_button("دخول الأستاذ")
            
            if t_btn:
                if t_code.strip() == "90100" and t_phone:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    try:
                        c.execute("INSERT OR REPLACE INTO users (phone, name, role) VALUES (?, ?, 'أستاذ')", (t_phone, t_name))
                        c.execute("INSERT OR IGNORE INTO teachers (phone, name, subject, grade_level, age, price, image_url, room_id) VALUES (?, ?, 'غير محدد', 'جميع المراحل', 30, 100, '', ?)", 
                                  (t_phone, t_name if t_name else "أستاذ", f"room_{t_phone}"))
                        conn.commit()
                    except:
                        pass
                    conn.close()

                    st.session_state.is_logged_in = True
                    st.session_state.user_phone = t_phone
                    st.session_state.user_role = "أستاذ"

                    set_js = f"""
                    <script>
                        localStorage.setItem("nova_phone", "{t_phone}");
                        localStorage.setItem("nova_role", "أستاذ");
                        window.location.href = window.location.pathname + "?autologin=1&phone=" + encodeURIComponent("{t_phone}") + "&role=أستاذ";
                    </script>
                    """
                    components.html(set_js, height=0)
                    st.rerun()
                else:
                    st.error("الكود السري غير صحيح (الكود هو 90100) أو رقم التليفون فارغ!")

    elif role_choice == "مطور 👑":
        st.subheader("👑 دخول المطور (بالكود السري)")
        with st.form("dev_reg"):
            dev_code = st.text_input("الكود السري للمطور (900800):", type="password")
            dev_btn = st.form_submit_button("دخول لوحة المطور")
            
            if dev_btn:
                if dev_code.strip() == "900800":
                    st.session_state.is_logged_in = True
                    st.session_state.user_phone = "01000000000"
                    st.session_state.user_role = "مطور"

                    set_js = f"""
                    <script>
                        localStorage.setItem("nova_phone", "01000000000");
                        localStorage.setItem("nova_role", "مطور");
                        window.location.href = window.location.pathname + "?autologin=1&phone=01000000000&role=مطور";
                    </script>
                    """
                    components.html(set_js, height=0)
                    st.rerun()
                else:
                    st.error("الكود السري للمطور غير صحيح (الكود هو 900800)!")

else:
    top_col, logout_col = st.columns([3, 1])
    top_col.success(f"مرحباً بك: **{st.session_state.user_role}** (رقم: {st.session_state.user_phone})")
    if logout_col.button("🚪 خروج وتغيير الحساب"):
        clear_js = """
        <script>
            localStorage.removeItem("nova_phone");
            localStorage.removeItem("nova_role");
            window.location.href = window.location.pathname;
        </script>
        """
        components.html(clear_js, height=0)
        st.session_state.is_logged_in = False
        st.rerun()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if st.session_state.user_role == "طالب":
        st.subheader("🎓 قائمة الأساتذة والمواد الدراسية")
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id, phone FROM teachers")
        teachers = c.fetchall()

        if teachers:
            for t in teachers:
                t_name, t_sub, t_grade, t_age, t_price, t_img, room_id, t_phone = t
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
                
                c.execute("SELECT status FROM subscriptions WHERE student_phone=? AND teacher_phone=?", 
                          (st.session_state.user_phone, t_phone))
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
                        c.execute("SELECT title, media_type, file_path FROM posts WHERE teacher_phone=? AND status='approved'", (t_phone,))
                        posts = c.fetchall()
                        if posts:
                            for p_title, p_type, p_path in posts:
                                st.write(f"📌 **{p_title}**")
                                if os.path.exists(p_path):
                                    if p_type == "image":
                                        st.image(p_path)
                                    elif p_type == "video":
                                        st.video(p_path)
                        else:
                            st.info("لا توجد منشورات أو فيديوهات معتمدة ومتاحة حالياً.")
                elif sub_status and sub_status[0] == 'pending':
                    st.warning("⏳ طلب اشتراكك قيد المراجعة والموافقة من الأستاذ.")
                else:
                    st.markdown(f"""
                    <div class="cash-box">
                        💸 للاشتراك ومشاهدة البث والفيديوهات: قم بتحويل المبلغ ({t_price} جنيه) على رقم فودافون كاش: <b>01213783090</b>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🚀 طلب الاشتراك مع الأستاذ {t_name}", key=f"btn_{t_phone}"):
                        c.execute("INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status) VALUES (?, ?, 'pending')",
                                  (st.session_state.user_phone, t_phone))
                        conn.commit()
                        st.success("تم إرسال طلب الاشتراك! في انتظار موافقة الأستاذ.")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("لا يوجد أساتذة مسجلون حالياً.")

    elif st.session_state.user_role == "أستاذ":
        st.subheader("👨‍🏫 استوديو إدارة الدروس والبث")
        c.execute("SELECT name, subject, grade_level, age, price, image_url, room_id FROM teachers WHERE phone=?", (st.session_state.user_phone,))
        t_info = c.fetchone()
        room_id = t_info[6] if t_info else f"room_{st.session_state.user_phone}"

        tab_stream, tab_post, tab_subs, tab_prof = st.tabs(["🔴 البث المباشر", "📤 نشر محتوى", "👥 طلبات الطلاب", "⚙️ بياناتي الشخصية"])

        with tab_stream:
            st.write("📹 **استوديو تشغيل الكاميرا والمايك لبدء البث للطلاب:**")
            t_stream_html = f"""
            <iframe src="https://vdo.ninja/?push={room_id}&webcam=1&autostart=1" 
                    style="width: 100%; height: 450px; border: 2px solid #2563eb; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(t_stream_html, height=470)

        with tab_post:
            p_title = st.text_input("عنوان الفيديو أو الشرح:")
            up_file = st.file_uploader("اختر فيديو أو صورة من جهازك:", type=["png", "jpg", "jpeg", "mp4"])
            if st.button("🚀 إرسال للمطور للمراجعة والنشر"):
                if up_file and p_title:
                    file_path = os.path.join(MEDIA_DIR, up_file.name)
                    with open(file_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    f_type = "video" if up_file.type.startswith("video") else "image"
                    c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, status) VALUES (?, ?, ?, ?, 'pending')",
                              (st.session_state.user_phone, p_title, f_type, file_path))
                    conn.commit()
                    st.success("✔️ تم رفع الفيديو وإرساله بنجاح!")
                    st.rerun()

            st.write("---")
            c.execute("SELECT title, status FROM posts WHERE teacher_phone=?", (st.session_state.user_phone,))
            my_posts = c.fetchall()
            if my_posts:
                for p_t, p_s in my_posts:
                    if p_s == 'approved':
                        st.write(f"✔️ **{p_t}** — (تمت الموافقة والنشر للطلاب ✅)")
                    else:
                        st.write(f"✔️ **{p_t}** — (قيد المراجعة لدى المطور ⏳)")
            else:
                st.info("لم تقم بنشر أي منشورات بعد.")

        with tab_subs:
            st.write("📋 **الطلاب المتقدمين للاشتراك بعد التحويل:**")
            c.execute("SELECT student_phone, status FROM subscriptions WHERE teacher_phone=?", (st.session_state.user_phone,))
            subs = c.fetchall()
            if subs:
                for s_ph, status in subs:
                    c.execute("SELECT name, grade FROM users WHERE phone=?", (s_ph,))
                    st_data = c.fetchone()
                    st_display_name = st_data[0] if st_data else s_ph
                    st_display_grade = st_data[1] if st_data else "غير محدد"

                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    col_a.write(f"🎓 الطالب: **{st_display_name}** (رقم: {s_ph} - سنة: {st_display_grade}) [الحالة: {status}]")
                    if status == 'pending':
                        if col_b.button("✅ قبول وتفعيل", key=f"acc_{s_ph}"):
                            c.execute("UPDATE subscriptions SET status='active' WHERE student_phone=? AND teacher_phone=?", (s_ph, st.session_state.user_phone))
                            conn.commit()
                            st.rerun()
                        if col_c.button("❌ رفض", key=f"ref_{s_ph}"):
                            c.execute("DELETE FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (s_ph, st.session_state.user_phone))
                            conn.commit()
                            st.rerun()
            else:
                st.info("لا توجد طلبات اشتراك حالياً.")

        with tab_prof:
            with st.form("prof_form"):
                name_in = st.text_input("الاسم الكامل:", value=t_info[0] if t_info else "")
                sub_in = st.text_input("المادة الدراسية:", value=t_info[1] if t_info else "")
                grade_in = st.text_input("المرحلة الدراسية:", value=t_info[2] if t_info else "")
                age_in = st.number_input("العمر:", value=int(t_info[3]) if t_info and t_info[3] else 30)
                price_in = st.number_input("سعر الاشتراك (جنيه):", value=float(t_info[4]) if t_info and t_info[4] else 100.0)
                img_in = st.text_input("رابط صورتك الشخصية (URL):", value=t_info[5] if t_info else "")
                if st.form_submit_button("حفظ وتحديث البيانات"):
                    c.execute("UPDATE teachers SET name=?, subject=?, grade_level=?, age=?, price=?, image_url=? WHERE phone=?",
                              (name_in, sub_in, grade_in, age_in, price_in, img_in, st.session_state.user_phone))
                    conn.commit()
                    st.success("تم حفظ البيانات بنجاح!")
                    st.rerun()

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
        
        dev_tab1, dev_tab2 = st.tabs(["🎥 مراجعة الفيديوهات والمنشورات", "🚫 إدارة المستخدمين والحظر"])
        with dev_tab1:
            c.execute("SELECT id, teacher_phone, title, media_type, file_path FROM posts WHERE status='pending'")
            pending_posts = c.fetchall()
            if pending_posts:
                for p_id, p_teacher, p_title, p_type, p_path in pending_posts:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.write(f"📱 **رقم الأستاذ:** {p_teacher}")
                    st.write(f"📌 **العنوان:** {p_title}")
                    if os.path.exists(p_path):
                        if p_type == "image":
                            st.image(p_path, width=300)
                        elif p_type == "video":
                            st.video(p_path)
                    col_ok, col_no = st.columns(2)
                    if col_ok.button(f"✅ موافقة ونشر", key=f"app_{p_id}"):
                        c.execute("UPDATE posts SET status='approved' WHERE id=?", (p_id,))
                        conn.commit()
                        st.rerun()
                    if col_no.button(f"❌ رفض وحذف", key=f"rej_{p_id}"):
                        c.execute("DELETE FROM posts WHERE id=?", (p_id,))
                        conn.commit()
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("لا توجد فيديوهات أو منشورات جديدة تنتظر المراجعة.")

        with dev_tab2:
            c.execute("SELECT id, phone, name, role, is_blocked FROM users WHERE role != 'مطور'")
            users = c.fetchall()
            if users:
                for u_id, u_phone, u_name, u_role, is_blocked in users:
                    u_col1, u_col2, u_col3 = st.columns([2, 1, 1])
                    u_col1.write(f"👤 **{u_name}** (رقم: {u_phone} - {u_role})")
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
