import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# 1. إعدادات الصفحة والتصميم
# =========================================================
st.set_page_config(
    page_title="منصة نوفا - البث المباشر", page_icon="🌟", layout="wide"
)

st.markdown(
    """
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-baseweb="input"] { text-align: right; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; background-color: #2e7d32; color: white; }
    .profile-card { background-color: #0f172a; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    .schedule-card { background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    </style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 2. إدارة قاعدة البيانات
# =========================================================
DB_NAME = "nova_platform.db"


def init_all_tables():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # جدول الطلبات والطلاب
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                governorate TEXT NOT NULL,
                course_name TEXT NOT NULL,
                status TEXT DEFAULT 'approved',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول حالة البث المباشر
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_room (
                id INTEGER PRIMARY KEY DEFAULT 1,
                is_live TEXT DEFAULT 'false',
                room_name TEXT DEFAULT 'nova_main_room'
            )
        """)
        cursor.execute(
            "INSERT OR IGNORE INTO live_room (id, is_live, room_name) VALUES (1, 'false', 'nova_main_room')"
        )

        # جدول التقييمات والرسائل
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

        # جدول جدول المحاضرات والمواد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT,
                subject TEXT,
                time_slot TEXT,
                instructor TEXT
            )
        """)
        conn.commit()


def get_student_info(code):
    code_clean = code.strip()
    init_all_tables()
    with sqlite3.connect(DB_NAME) as conn:
        try:
            df = pd.read_sql_query(
                "SELECT * FROM requests WHERE request_code = ?",
                conn,
                params=(code_clean,),
            )
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            pass
    return None


def get_live_status():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_live, room_name FROM live_room WHERE id = 1")
        res = cursor.fetchone()
        return (res[0] == "true", res[1]) if res else (False, "nova_main_room")


def set_live_status(is_live, room_name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE live_room SET is_live = ?, room_name = ? WHERE id = 1",
            ("true" if is_live else "false", room_name),
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


def add_schedule_item(day, subject, time_slot, instructor):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO schedule (day, subject, time_slot, instructor)
            VALUES (?, ?, ?, ?)
        """,
            (day, subject, time_slot, instructor),
        )
        conn.commit()


def get_schedule():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("SELECT * FROM schedule", conn)


# =========================================================
# 3. الواجهة الرئيسية
# =========================================================
init_all_tables()

page = st.sidebar.radio(
    "القائمة الرئيسية:", ["دخول البث المباشر (للطالب)", "لوحة تحكم المطور"]
)

# ---------------------------------------------------------
# 1. صفحة الطالب
# ---------------------------------------------------------
if page == "دخول البث المباشر (للطالب)":
    st.title("🌟 منصة نوفا التعليمية - القاعة التفاعلية")

    if "student_data" not in st.session_state:
        st.session_state.student_data = None

    if st.session_state.student_data is None:
        st.subheader("🔑 تسجيل الدخول بالرقم الكودي")
        input_code = st.text_input(
            "أدخل كود الطالب الخاص بك:", placeholder="مثال: NOVA-4KFU39"
        )

        if st.button("انضمام للقاعة 🚀"):
            student = get_student_info(input_code)
            if student:
                st.session_state.student_data = student
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("❌ الكود غير صحيح أو لم يتم تفعيله بعد.")
    else:
        student = st.session_state.student_data

        # عرض بيانات الطالب
        st.markdown(
            f"""
            <div class="profile-card">
                <h3>👤 الطالب: {student.get('full_name')}</h3>
                <p>📚 <b>الكورس:</b> {student.get('course_name')} | 🔑 <b>الكود:</b> {student.get('request_code')}</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button("تسجيل الخروج"):
            st.session_state.student_data = None
            st.rerun()

        st.divider()

        is_live, room_name = get_live_status()

        # حالة وجود بث مباشر
        if is_live:
            st.subheader("🔴 البث المباشر شغال الآن - انضمام فوري")
            student_display_name = student.get("full_name").replace(" ", "_")

            # شاشة البث المباشر والتفاعل المدمجة بالكامل بدون مغادرة المنصة
            jitsi_html = f"""
                <iframe src="https://meet.jit.si/{room_name}#userInfo.displayName=%22{student_display_name}%22"
                        style="height: 600px; width: 100%; border: 0px; border-radius: 12px;">
                </iframe>
            """
            components.html(jitsi_html, height=620)

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("⭐ تقييم المحاضرة")
                rating = st.slider("تقييمك للشرح (%):", 0, 100, 95, step=5)

            with col2:
                st.subheader("💬 إرسال ملاحظة للمطور")
                msg = st.text_area("أكتب سؤالك أو ملاحظتك هنا:")
                if st.button("إرسال التقييم 📤"):
                    if msg.strip():
                        save_feedback(
                            student.get("request_code"),
                            student.get("full_name"),
                            rating,
                            msg,
                        )
                        st.success("تم إرسال تقييمك ورسالتك بنجاح!")
                    else:
                        st.warning("يرجى كتابة الرسالة أولاً.")

        # حالة عدم وجود بث مباشر -> عرض الجدول الدراسي
        else:
            st.info("⌛ لا يوجد بث مباشر شغال حالياً في القاعة.")
            st.subheader("📅 جدول المحاضرات والمواد الدراسي")

            df_sched = get_schedule()
            if df_sched.empty:
                st.write("لم يتم إضافة جدول المحاضرات بعد من المطور.")
            else:
                st.dataframe(
                    df_sched[
                        [
                            "day",
                            "subject",
                            "time_slot",
                            "instructor",
                        ]
                    ].rename(
                        columns={
                            "day": "اليوم",
                            "subject": "المادة / الكورس",
                            "time_slot": "الموعد",
                            "instructor": "المحاضر",
                        }
                    ),
                    use_container_width=True,
                )

# ---------------------------------------------------------
# 2. صفحة المطور
# ---------------------------------------------------------
else:
    st.title("⚙️ لوحة تحكم المطور والتحكم بالبث")
    admin_pass = st.text_input("كلمة سر المطور:", type="password")

    if admin_pass == st.secrets.get("ADMIN_PASSWORD", "2010"):
        st.success("مرحباً بك يا مطور المنصة 👋")

        tab1, tab2, tab3 = st.tabs(
            ["🎥 إدارة البث المباشر", "📅 إدارة جدول المواد", "📊 التقييمات والرسائل"]
        )

        # Tab 1: التحكم في البث المباشر
        with tab1:
            is_live_active, current_room = get_live_status()

            st.subheader("🔴 تشغيل وإيقاف البث المباشر")
            room_input = st.text_input(
                "اسم القاعة المباشرة:", value=current_room
            )

            if not is_live_active:
                if st.button("🚀 فتح البث المباشر الآن للطلاب"):
                    set_live_status(True, room_input)
                    st.success("تم تشغيل البث المباشر ودخول الطلاب للقاعة الآن!")
                    st.rerun()
            else:
                st.warning("الثر المباشر يعمل حالياً داخل المنصة.")

                # شاشة المطور للشرح ومشاركة الشاشة
                st.subheader("🖥️ شاشة الشرح الخاصة بك (قم بمشاركة الشاشة)")
                dev_jitsi_html = f"""
                    <iframe src="https://meet.jit.si/{room_input}#userInfo.displayName=%22المطور_المحاضر%22"
                            style="height: 500px; width: 100%; border: 0px; border-radius: 12px;">
                    </iframe>
                """
                components.html(dev_jitsi_html, height=520)

                if st.button("🛑 إغلاق البث المباشر وإعادة الطلاب للجدول"):
                    set_live_status(False, room_input)
                    st.success("تم إغلاق البث المباشر بنجاح.")
                    st.rerun()

        # Tab 2: إضافة وتعديل جدول المواد
        with tab2:
            st.subheader("➕ إضافة مادة/محاضرة لجدول الطلاب")
            with st.form("add_schedule"):
                c1, c2 = st.columns(2)
                with c1:
                    day = st.selectbox(
                        "اليوم:",
                        [
                            "السبت",
                            "الأحد",
                            "الإثنين",
                            "الثلاثاء",
                            "الأربعاء",
                            "الخميس",
                            "الجمعة",
                        ],
                    )
                    subject = st.text_input("اسم المادة / المحاضرة:")
                with c2:
                    time_slot = st.text_input(
                        "الوقت:", placeholder="مثال: 08:00 مساءً"
                    )
                    instructor = st.text_input("اسم المحاضر:")

                btn_add = st.form_submit_button("إضافة للجدول 💾")

            if btn_add:
                if subject and time_slot:
                    add_schedule_item(day, subject, time_slot, instructor)
                    st.success("تمت إضافة المحاضرة للجدول بنجاح!")
                    st.rerun()
                else:
                    st.error("يرجى ملء كافة البيانات.")

            st.divider()
            st.subheader("📋 الجدول الحالي")
            st.dataframe(get_schedule(), use_container_width=True)

        # Tab 3: التقييمات والرسائل
        with tab3:
            st.subheader("📊 رسائل وتقييمات الطلاب")
            with sqlite3.connect(DB_NAME) as conn:
                df_fb = pd.read_sql_query(
                    "SELECT student_code AS 'الكود', student_name AS 'الاسم', rating AS 'التقييم %', message AS 'الرسالة', created_at AS 'التاريخ' FROM live_feedback ORDER BY id DESC",
                    conn,
                )
                st.dataframe(df_fb, use_container_width=True)
