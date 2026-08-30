from datetime import date
import sqlite3
import pandas as pd
import requests
import streamlit as st

# =========================================================
# 1. إدارة قاعدة البيانات المُحدثة (Database Manager)
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

            # جدول حسابات/بيانات الطلاب
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    email TEXT,
                    governorate TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # جدول الكورسات والمواعيد (يضيفها المطور)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    instructor TEXT NOT NULL,
                    days TEXT NOT NULL,
                    time_str TEXT NOT NULL,
                    live_url TEXT DEFAULT '',
                    is_live_active TEXT DEFAULT 'false'
                )
            """)

            # جدول اشتراكات الطلاب في الكورسات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_phone TEXT NOT NULL,
                    course_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    UNIQUE(student_phone, course_id)
                )
            """)

            conn.commit()

    # --- إدارة الكورسات ---
    def add_course(self, title, instructor, days, time_str, live_url):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO courses (title, instructor, days, time_str, live_url) VALUES (?, ?, ?, ?, ?)",
                (title, instructor, days, time_str, live_url),
            )
            conn.commit()

    def get_all_courses(self):
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM courses", conn)

    def update_course_live(self, course_id, live_url, is_active):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE courses SET live_url = ?, is_live_active = ? WHERE id = ?",
                (live_url, "true" if is_active else "false", course_id),
            )
            conn.commit()

    # --- إدارة الطلاب والاشتراكات ---
    def register_student(self, name, phone, email, governorate):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO students (full_name, phone, email, governorate) VALUES (?, ?, ?, ?)",
                    (name, phone, email, governorate),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return True  # الحساب موجود مسبقاً
        except Exception:
            return False

    def enroll_student(self, phone, course_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO enrollments (student_phone, course_id) VALUES (?, ?)",
                    (phone, course_id),
                )
                conn.commit()
                return True, "تم الاشتراك في الكورس بنجاح!"
        except sqlite3.IntegrityError:
            return False, "أنت مشترك في هذا الكورس بالفعل."

    def is_enrolled(self, phone, course_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM enrollments WHERE student_phone = ? AND course_id = ?",
                (phone, course_id),
            )
            return cursor.fetchone() is not None

    def get_enrolled_courses(self, phone):
        with self.get_connection() as conn:
            query = """
                SELECT c.* FROM courses c
                JOIN enrollments e ON c.id = e.course_id
                WHERE e.student_phone = ?
            """
            return pd.read_sql_query(query, conn, params=(phone,))


# =========================================================
# 2. كلاس الإشعارات (WhatsApp Notifier)
# =========================================================


class WhatsAppNotifier:

    def __init__(self):
        self.phone = st.secrets.get("CALLMEBOT_PHONE", None)
        self.apikey = st.secrets.get("CALLMEBOT_APIKEY", None)

    def send_message(self, message):
        if not self.phone or not self.apikey:
            return False
        url = "https://api.callmebot.com/whatsapp.php"
        params = {"phone": self.phone, "text": message, "apikey": self.apikey}
        try:
            res = requests.get(url, params=params, timeout=10)
            return res.ok
        except Exception:
            return False


# =========================================================
# 3. التطبيق الرئيسي (Nova Platform)
# =========================================================


class NovaPlatformApp:

    def __init__(self):
        self.db = StudentDatabase()
        self.notifier = WhatsAppNotifier()
        self.setup_page()

    def setup_page(self):
        st.set_page_config(
            page_title="منصة نوفا التعليمية", page_icon="🌟", layout="centered"
        )

    def render_student_view(self):
        st.title("🌟 منصة نوفا التعليمية")

        # 1. تسجيل دخول الطالب برقم الهاتف
        st.subheader("🔑 تسجيل الدخول")
        user_phone = st.text_input(
            "أدخل رقم هاتفك للوصول لكورساتك والاشتراك:",
            placeholder="010xxxxxxx",
        )

        if not user_phone:
            st.info(
                "يرجى كتابة رقم الهاتف أولاً لرؤية الكورسات المتاحة والبث المباشر."
            )
            return

        # 2. عرض الكورسات المتاحة للاشتراك
        st.divider()
        st.subheader("📚 الكورسات المتاحة")
        courses_df = self.db.get_all_courses()

        if courses_df.empty:
            st.warning("لا توجد كورسات مضافة حالياً من المطور.")
        else:
            for _, row in courses_df.iterrows():
                with st.expander(f"📌 {row['title']} - المحاضر: {row['instructor']}"):
                    st.write(f"📅 **الأيام:** {row['days']}")
                    st.write(f"⏰ **الموعد:** {row['time_str']}")

                    is_subbed = self.db.is_enrolled(user_phone, row["id"])

                    if is_subbed:
                        st.success("✅ أنت مشترك في هذا الكورس")
                    else:
                        if st.button(
                            f"📝 الاشتراك في {row['title']}", key=f"sub_{row['id']}"
                        ):
                            # تسجيل بيانات أولية إن لم تكن موجودة
                            self.db.register_student(
                                "طالب", user_phone, "", "غير محدد"
                            )
                            ok, msg = self.db.enroll_student(
                                user_phone, row["id"]
                            )
                            if ok:
                                st.success(msg)
                                self.notifier.send_message(
                                    f"🎉 اشتراك جديد!\nالكورس: {row['title']}\nطالب: {user_phone}"
                                )
                                st.rerun()
                            else:
                                st.error(msg)

        # 3. قسم البث المباشر للكورسات المشترك فيها فقط
        st.divider()
        st.subheader("🔴 البث المباشر للدروس")
        my_courses = self.db.get_enrolled_courses(user_phone)

        if my_courses.empty:
            st.info("قم بالاشتراك في أحد الكورسات أعلاه للتمكن من مشاهدة البث المباشر.")
        else:
            has_live = False
            for _, c in my_courses.iterrows():
                if c["is_live_active"] == "true":
                    has_live = True
                    st.error(f"LIVE NOW: بث مباشر شغال كورس ({c['title']})")
                    st.video(c["live_url"])

            if not has_live:
                st.info("لا يوجد بث مباشر شغال حالياً للكورسات المشترك بها.")

    def render_admin_dashboard(self):
        st.title("⚙️ لوحة تحكم المطور")
        password = st.text_input("أدخل كلمة سر المطور:", type="password")
        admin_pass = st.secrets.get("ADMIN_PASSWORD", "2010")

        if password != admin_pass:
            st.warning("كلمة السر خاطئة.")
            return

        st.success("أهلاً بك يا مطور المنصة 👋")
        tab1, tab2 = st.tabs(["➕ إضافة كورسات والتحكم بالبث", "👥 بيانات المشتركين"])

        with tab1:
            st.subheader("إضافة كورس جديد")
            with st.form("add_c"):
                title = st.text_input("اسم الكورس (مثل: كورس بايثون)")
                instructor = st.text_input("اسم المحاضر")
                days = st.text_input("الأيام (مثال: السبت والأربعاء)")
                time_str = st.text_input("الوقت (مثال: 7:00 مساءً)")
                live_url = st.text_input("رابط البث المباشر الافتراضي")
                if st.form_submit_button("حفظ الكورس"):
                    self.db.add_course(
                        title, instructor, days, time_str, live_url
                    )
                    st.success("تم إضافة الكورس بنجاح.")

            st.divider()
            st.subheader("التحكم في البث المباشر للكورسات")
            df_c = self.db.get_all_courses()
            for _, row in df_c.iterrows():
                st.write(f"**{row['title']}** ({row['days']} - {row['time_str']})")
                col1, col2 = st.columns([2, 1])
                with col1:
                    new_url = st.text_input(
                        "رابط البث الحالي:",
                        value=row["live_url"],
                        key=f"url_{row['id']}",
                    )
                with col2:
                    is_active = st.checkbox(
                        "تفعيل البث",
                        value=(row["is_live_active"] == "true"),
                        key=f"act_{row['id']}",
                    )

                if st.button("تحديث البث", key=f"btn_{row['id']}"):
                    self.db.update_course_live(row["id"], new_url, is_active)
                    st.success("تم تحديث حالة البث!")

        with tab2:
            st.subheader("بيانات الاشتراكات")
            with self.db.get_connection() as conn:
                df_en = pd.read_sql_query(
                    """
                    SELECT e.id, e.student_phone, c.title as course_name 
                    FROM enrollments e 
                    JOIN courses c ON e.course_id = c.id
                """,
                    conn,
                )
                st.dataframe(df_en, use_container_width=True)

    def run(self):
        page = st.sidebar.radio("القائمة:", ["صفحة الطلاب", "لوحة المطور"])
        if page == "صفحة الطلاب":
            self.render_student_view()
        else:
            self.render_admin_dashboard()


if __name__ == "__main__":
    app = NovaPlatformApp()
    app.run()
