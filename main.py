from datetime import date, timedelta
import sqlite3
import pandas as pd
import requests
import streamlit as st

# =========================================================
# 1. إدارة قاعدة البيانات (Database Manager)
# =========================================================


class StudentDatabase:

    def __init__(self, db_name="nova_platform.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # جدول الطلاب
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    whatsapp TEXT,
                    email TEXT,
                    governorate TEXT,
                    education_stage TEXT,
                    school_grade TEXT,
                    programming_level TEXT,
                    studied_python TEXT,
                    reason TEXT,
                    parent_name TEXT,
                    parent_phone TEXT,
                    course_name TEXT,
                    course_date TEXT,
                    course_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # جدول إعدادات النظام (البث المباشر)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # جدول جدول التدريب
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    day TEXT NOT NULL,
                    time_str TEXT NOT NULL,
                    instructor TEXT NOT NULL
                )
            """)

            # تعيين القيم الافتراضية للبث لو غير موجودة
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('live_active', 'false')"
            )
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('live_url', 'https://www.youtube.com/watch?v=5qap5aO4i9A')"
            )

            conn.commit()

    def save_student(self, data):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO students (
                        full_name, birth_date, age, phone, whatsapp, email,
                        governorate, education_stage, school_grade, programming_level,
                        studied_python, reason, parent_name, parent_phone,
                        course_name, course_date, course_time
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data["full_name"],
                        data["birth_date"],
                        data["age"],
                        data["phone"],
                        data["whatsapp"],
                        data["email"],
                        data["governorate"],
                        data["education_stage"],
                        data["school_grade"],
                        data["programming_level"],
                        data["studied_python"],
                        data["reason"],
                        data["parent_name"],
                        data["parent_phone"],
                        data["course_name"],
                        data["course_date"],
                        data["course_time"],
                    ),
                )
                conn.commit()
                return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "duplicate"
        except Exception as e:
            return False, str(e)

    def get_setting(self, key):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def update_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
            )
            conn.commit()

    def add_schedule_item(self, title, day, time_str, instructor):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO schedule (title, day, time_str, instructor) VALUES (?, ?, ?, ?)",
                (title, day, time_str, instructor),
            )
            conn.commit()

    def get_schedule(self):
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM schedule", conn)

    def delete_schedule_item(self, item_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedule WHERE id = ?", (item_id,))
            conn.commit()

    def get_all_students(self):
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM students", conn)


# =========================================================
# 2. كلاس الإشعارات (WhatsApp Notifier)
# =========================================================


class WhatsAppNotifier:

    def __init__(self):
        self.phone = st.secrets.get("CALLMEBOT_PHONE", None)
        self.apikey = st.secrets.get("CALLMEBOT_APIKEY", None)

    def send_message(self, message):
        if not self.phone or not self.apikey:
            return False, "بيانات CallMeBot غير موجودة في Secrets"

        url = "https://api.callmebot.com/whatsapp.php"
        params = {"phone": self.phone, "text": message, "apikey": self.apikey}

        try:
            response = requests.get(url, params=params, timeout=20)
            return response.ok, response.text
        except Exception as e:
            return False, str(e)


# =========================================================
# 3. التطبيق الرئيسي ولوحة التحكم (Nova Platform)
# =========================================================


class NovaPlatformApp:

    def __init__(self):
        self.db = StudentDatabase()
        self.notifier = WhatsAppNotifier()
        self.setup_page()

    def setup_page(self):
        st.set_page_config(
            page_title="منصة نوفا التعليمية",
            page_icon="🌟",
            layout="centered",
            initial_sidebar_state="expanded",
        )
        self.apply_styles()

    def apply_styles(self):
        st.markdown(
            """
        <style>
        .stApp { direction: rtl; text-align: right; background: #f5f7fb; }
        .block-container { max-width: 850px; padding: 20px 14px 50px; }
        .nova-header { background: linear-gradient(135deg, #071d49, #12438f); color: white; padding: 28px 20px; border-radius: 24px; text-align: center; margin-bottom: 18px; }
        .nova-logo { font-size: 38px; font-weight: 900; }
        .nova-header h1 { font-size: 28px; margin: 8px 0; }
        .course-card { background: white; border-radius: 22px; padding: 22px; margin-bottom: 18px; border: 1px solid #e7eaf0; }
        .course-title { color: #09245c; font-size: 25px; font-weight: 900; margin-bottom: 12px; }
        .section-title { color: #09245c; font-size: 21px; font-weight: 900; margin: 18px 0 12px; }
        .success-box { background: #eafff1; border: 1px solid #8de0ae; border-radius: 20px; padding: 25px; text-align: center; color: #146b36; font-size: 18px; }
        .footer { text-align: center; color: #777; margin-top: 30px; }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def render_student_view(self):
        st.markdown(
            """
        <div class="nova-header">
            <div class="nova-logo">🌟 نوفا</div>
            <h1>منصة نوفا التعليمية</h1>
            <p>سجّل الآن وابدأ رحلتك في عالم البرمجة 🚀</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # قسم البث المباشر (إذا كان مفعلاً من المطور)
        is_live = self.db.get_setting("live_active") == "true"
        if is_live:
            live_url = self.db.get_setting("live_url")
            st.markdown(
                '<div class="section-title">🔴 البث المباشر الحالي</div>',
                unsafe_allow_html=True,
            )
            st.video(live_url)

        # عرض جدول التدريب
        st.markdown(
            '<div class="section-title">📅 جدول التدريبات المتاحة</div>',
            unsafe_allow_html=True,
        )
        df_schedule = self.db.get_schedule()
        if not df_schedule.empty:
            st.dataframe(
                df_schedule[["title", "day", "time_str", "instructor"]].rename(
                    columns={
                        "title": "الدورة",
                        "day": "اليوم",
                        "time_str": "الوقت",
                        "instructor": "المحاضر",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info("لا يوجد مواعيد تدريب مضافة حالياً.")

        # استمارة التسجيل
        st.markdown(
            '<div class="section-title">📝 استمارة التسجيل</div>',
            unsafe_allow_html=True,
        )
        with st.form("student_form"):
            full_name = st.text_input("الاسم بالكامل *")
            birth_date = st.date_input(
                "تاريخ الميلاد *", value=date(2010, 1, 1)
            )
            phone = st.text_input("رقم الهاتف *")
            whatsapp = st.text_input("رقم الواتساب")
            email = st.text_input("البريد الإلكتروني")
            governorate = st.selectbox(
                "المحافظة *", ["الدقهلية", "القاهرة", "الإسكندرية", "أخرى"]
            )
            education_stage = st.selectbox(
                "المرحلة التعليمية *", ["إعدادي", "ثانوي", "جامعي", "أخرى"]
            )
            programming_level = st.selectbox(
                "مستواك في البرمجة *",
                [
                    "مبتدئ تماماً",
                    "لدي معرفة بسيطة",
                    "سبق لي دراسة البرمجة",
                ],
            )

            agree = st.checkbox("أوافق على التسجيل")
            submitted = st.form_submit_button("🚀 تسجيل الآن")

            if submitted:
                if not full_name or not phone or not agree:
                    st.error("❌ يرجى ملء كافة البيانات المطلوبة.")
                else:
                    today = date.today()
                    age = (
                        today.year
                        - birth_date.year
                        - (
                            (today.month, today.day)
                            < (birth_date.month, birth_date.day)
                        )
                    )
                    student_data = {
                        "full_name": full_name,
                        "birth_date": birth_date.strftime("%Y-%m-%d"),
                        "age": age,
                        "phone": phone,
                        "whatsapp": whatsapp if whatsapp else phone,
                        "email": email,
                        "governorate": governorate,
                        "education_stage": education_stage,
                        "school_grade": "",
                        "programming_level": programming_level,
                        "studied_python": "نعم",
                        "reason": "",
                        "parent_name": "",
                        "parent_phone": "",
                        "course_name": "Python",
                        "course_date": "",
                        "course_time": "",
                    }
                    saved, res = self.db.save_student(student_data)
                    if saved:
                        st.success(f"🎉 تم التسجيل بنجاح! رقم التسجيل: {res}")
                        self.notifier.send_message(
                            f"🚨 طالب جديد: {full_name}\nرقم الهاتف: {phone}"
                        )
                    elif res == "duplicate":
                        st.error("⚠️ الرقم مسجل مسبقاً.")

    def render_admin_dashboard(self):
        st.title("⚙️ لوحة تحكم المطور")

        # كلمة السر لحماية اللوحة (تكون 2010 افتراضياً)
        password = st.text_input("أدخل كلمة سر المطور:", type="password")
        admin_pass = st.secrets.get("ADMIN_PASSWORD", "2010")

        if password != admin_pass:
            st.warning("يرجى إدخال كلمة السر الصحيحة للوصول للوحة التحكم.")
            return

        st.success("تم تسجيل الدخول بنجاح كـ **مطور النظام**.")
        tab1, tab2, tab3 = st.tabs(
            ["🔴 البث المباشر", "📅 جدول التدريبات", "👥 الطلاب المسجلين"]
        )

        # 1. إعدادات البث المباشر
        with tab1:
            st.subheader("التحكم في البث المباشر")
            current_status = self.db.get_setting("live_active") == "true"
            is_active = st.checkbox("تفعيل البث المباشر الآن", value=current_status)
            live_url = st.text_input(
                "رابط البث (YouTube/Twitch/Vimeo):",
                value=self.db.get_setting("live_url"),
            )

            if st.button("حفظ إعدادات البث"):
                self.db.update_setting(
                    "live_active", "true" if is_active else "false"
                )
                self.db.update_setting("live_url", live_url)
                st.success("تم تحديث حالة ورابط البث المباشر بنجاح!")

        # 2. إعدادات الجدول
        with tab2:
            st.subheader("إضافة ميعاد تدريب جديد")
            with st.form("add_schedule"):
                title = st.text_input("اسم الكورس/التدريب")
                day = st.text_input("اليوم (مثال: الخميس)")
                time_str = st.text_input("الوقت (مثال: 5:00 مساءً)")
                instructor = st.text_input("اسم المحاضر")
                if st.form_submit_button("إضافة للجدول"):
                    self.db.add_schedule_item(title, day, time_str, instructor)
                    st.success("تمت الإضافة بنجاح.")

            st.subheader("الجدول الحالي")
            df_sch = self.db.get_schedule()
            st.dataframe(df_sch, use_container_width=True)

            delete_id = st.number_input(
                "أدخل المعرف (ID) لحذف العنصر:", step=1, value=0
            )
            if st.button("حذف ميعاد"):
                self.db.delete_schedule_item(delete_id)
                st.success("تم الحذف بنجاح.")

        # 3. عرض الطلاب المسجلين
        with tab3:
            st.subheader("قائمة الطلاب المسجلين")
            df_students = self.db.get_all_students()
            st.dataframe(df_students, use_container_width=True)

    def run(self):
        # القائمة الجانبية للتبديل بين واجهة المستخدم ولوحة المطور
        st.sidebar.title("📌 القائمة")
        page = st.sidebar.radio("انتقل إلى:", ["الواجهة الرئيسية", "لوحة المطور"])

        if page == "الواجهة الرئيسية":
            self.render_student_view()
        else:
            self.render_admin_dashboard()

        st.markdown(
            '<div class="footer">🌟 منصة نوفا التعليمية</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    app = NovaPlatformApp()
    app.run()
