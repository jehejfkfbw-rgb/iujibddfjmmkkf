import sqlite3
import pandas as pd
import streamlit as st

# =========================================================
# 1. إعدادات الصفحة والتصميم
# =========================================================
st.set_page_config(
    page_title="منصة نوفا - البث المباشر", page_icon="📺", layout="wide"
)

st.markdown(
    """
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-baseweb="input"] { text-align: right; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; }
    .profile-card { background-color: #1e293b; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    </style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 2. إدارة قاعدة البيانات
# =========================================================
DB_NAME = "nova_platform.db"


def init_live_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # جدول رسائل الشات والتقييمات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT,
                student_name TEXT,
                rating INTEGER,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول إعدادات البث الحالي
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                is_live TEXT DEFAULT 'false',
                stream_url TEXT DEFAULT ''
            )
        """)
        cursor.execute(
            "INSERT OR IGNORE INTO live_settings (id, is_live, stream_url) VALUES (1, 'false', '')"
        )
        conn.commit()


def get_student_info(code):
    """التحقق من كود الطالب أو كود الطلب المفعل"""
    with sqlite3.connect(DB_NAME) as conn:
        # البحث في جدول الطلبات المقبولة
        df = pd.read_sql_query(
            "SELECT * FROM requests WHERE request_code = ? AND status = 'approved'",
            conn,
            params=(code.strip(),),
        )
        if not df.empty:
            return df.iloc[0].to_dict()

        # البحث في جدول الطلاب إن وجد
        try:
            df_stu = pd.read_sql_query(
                "SELECT * FROM pending_students WHERE student_code = ? AND status = 'approved'",
                conn,
                params=(code.strip(),),
            )
            if not df_stu.empty:
                return df_stu.iloc[0].to_dict()
        except Exception:
            pass

    return None


def get_live_status():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_live, stream_url FROM live_settings WHERE id = 1"
        )
        res = cursor.fetchone()
        return (res[0] == "true", res[1]) if res else (False, "")


def update_live_status(is_live, url):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE live_settings SET is_live = ?, stream_url = ? WHERE id = 1",
            ("true" if is_live else "false", url),
        )
        conn.commit()


def save_feedback(code, name, rating, message):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO live_feedback (student_code, student_name, rating, message)
            VALUES (?, ?, ?, ?)
        """,
            (code, name, rating, message),
        )
        conn.commit()


# =========================================================
# 3. واجهة الاستخدام
# =========================================================
init_live_db()

page = st.sidebar.radio("القائمة:", ["تسجيل دخول الطالب للبث", "لوحة المطور (إدارة البث)"])

# ---------------------------------------------------------
# صفحة الطالب
# ---------------------------------------------------------
if page == "تسجيل دخول الطالب للبث":
    st.title("📺 بوابة البث المباشر - منصة نوفا")

    # جلسة الحفظ
    if "student_data" not in st.session_state:
        st.session_state.student_data = None

    if st.session_state.student_data is None:
        st.subheader("🔑 تسجيل الدخول بكود الطالب")
        input_code = st.text_input(
            "أدخل كود الطالب أو كود الطلب الخاص بك:",
            placeholder="مثال: REQ-4KFU39 أو NOVA-4KFU39",
        )

        if st.button("دخول البث المباشر 🚀"):
            if not input_code.strip():
                st.error("⚠️ يرجى كتابة الكود أولاً.")
            else:
                student = get_student_info(input_code)
                if student:
                    st.session_state.student_data = student
                    st.success("تم التحقق من الكود بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ هذا الكود غير موجود أو لم يتم تفعيله بعد من المطور.")
    else:
        student = st.session_state.student_data

        # كارت بيانات الطالب
        st.markdown(
            f"""
            <div class="profile-card">
                <h3>👤 مرحباً بك: {student.get('full_name')}</h3>
                <p>📚 <b>الكورس المسجل:</b> {student.get('course_name')} | 🔑 <b>الكود:</b> {student.get('request_code', student.get('student_code'))}</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button("خروج"):
            st.session_state.student_data = None
            st.rerun()

        st.divider()

        # عرض البث المباشر
        is_live, stream_url = get_live_status()

        if is_live and stream_url:
            st.subheader("🔴 البث المباشر شغال الآن")

            # عرض فيديو البث المباشر (دعم YouTube/Twitch أو روابط سحابية)
            st.video(stream_url)

            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("⭐ تقييم المحاضرة البث")
                rating = st.slider("تقييمك للشرح (%):", 0, 100, 90, step=5)

            with col2:
                st.subheader("💬 إرسال سؤال / رسالة للمحاضر")
                msg = st.text_area("أكتب سؤالك أو استفسارك هنا:")
                if st.button("إرسال للمطور 📤"):
                    if msg.strip():
                        code_val = student.get(
                            "request_code", student.get("student_code")
                        )
                        save_feedback(
                            code_val, student.get("full_name"), rating, msg
                        )
                        st.success("تم إرسال تقييمك ورسالتك بنجاح!")
                    else:
                        st.warning("يرجى كتابة رسالة قبل الإرسال.")
        else:
            st.info("⌛ لا يوجد بث مباشر شغال حالياً. انتظر موعد المحاضرة القادمة.")

# ---------------------------------------------------------
# صفحة المطور
# ---------------------------------------------------------
else:
    st.title("⚙️ لوحة المطور - إعدادات البث والأسئلة")
    admin_pass = st.text_input("كلمة السر:", type="password")

    if admin_pass == st.secrets.get("ADMIN_PASSWORD", "2010"):
        st.success("أهلاً بك يا مطور المنصة 👋")

        is_live_active, current_url = get_live_status()

        st.subheader("🖥️ بدء مشاركة شاشة اللابتوب والبث")
        st.markdown("""
        **كيف تبدأ بث شاشة اللابتوب؟**
        1. افتح برنامج **OBS Studio** (مجاني) أو بث مباشر على **YouTube Live Unlisted** واختر مشاركة الشاشة (Display Capture).
        2. انسخ رابط البث أو رابط الفيديو وضع الكود أسفله لتفعيله للطلاب فوراً.
        """)

        with st.form("live_config"):
            new_url = st.text_input(
                "رابط فيديو البث المباشر (YouTube / Twitch / Stream):",
                value=current_url,
            )
            enable_live = st.checkbox("تفعيل البث المباشر الآن 🔴", value=is_live_active)
            save_btn = st.form_submit_button("حفظ وتحديث حالة البث 💾")

        if save_btn:
            update_live_status(enable_live, new_url)
            st.success("تم تحديث إعدادات البث بنجاح!")

        st.divider()
        st.subheader("📊 أسئلة وتقييمات الطلاب أثناء البث")

        with sqlite3.connect(DB_NAME) as conn:
            df_fb = pd.read_sql_query(
                "SELECT student_code AS 'كود الطالب', student_name AS 'اسم الطالب', rating AS 'التقييم %', message AS 'الرسالة', created_at AS 'التوقيت' FROM live_feedback ORDER BY id DESC",
                conn,
            )
            st.dataframe(df_fb, use_container_width=True)
