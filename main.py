import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# 1. إعدادات وتصميم الصفحة
# =========================================================
st.set_page_config(page_title="منصة نوفا التعليمية - نظام البث الفوري", page_icon="🌟", layout="wide")

st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-baseweb="input"] { text-align: right; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; background-color: #2e7d32; color: white; height: 42px; }
    .profile-card { background-color: #0f172a; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    .live-active { background-color: #15803d; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-weight: bold; font-size: 18px; }
    .btn-external { display: inline-block; background-color: #2563eb; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-bottom: 15px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# قائمة المواد الافتراضية
AVAILABLE_COURSES = [
    "لغة بايثون - تعلم البرمجة للمبتدئين",
    "أساسيات البرمجة للمبتدئين",
    "تطوير تطبيقات الويب (Streamlit & Flask)",
    "تطوير الألعاب (Godot & Pygame)",
    "مادة المشمش"
]

# =========================================================
# 2. إدارة قاعدة البيانات
# =========================================================
DB_NAME = "nova_v6_live.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. جدول الطلاب
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT UNIQUE NOT NULL,
                student_name TEXT NOT NULL,
                course_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. جدول البث المباشر المخصص للمواد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_live (
                course_name TEXT PRIMARY KEY,
                is_live TEXT DEFAULT 'false',
                room_id TEXT
            )
        """)
        
        # 3. جدول التقييمات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT,
                student_name TEXT,
                course_name TEXT,
                rating INTEGER,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. جدول مواعيد المواد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                day TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                next_live_info TEXT
            )
        """)
        conn.commit()

# --- وظائف التحكم ---
def add_student_code(code, name, course):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO student_codes (student_code, student_name, course_name) VALUES (?, ?, ?)",
                           (code.strip(), name.strip(), course.strip()))
            conn.commit()
            return True, "تمت إضافة الكود وتخصيص المادة بنجاح!"
    except sqlite3.IntegrityError:
        return False, "⚠️ هذا الكود موجود بالفعل في النظام."
    except Exception as e:
        return False, str(e)

def delete_student_code(code_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_codes WHERE id = ?", (code_id,))
        conn.commit()

def verify_student(code):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM student_codes WHERE student_code = ?", conn, params=(code.strip(),))
        if not df.empty:
            return df.iloc[0].to_dict()
    return None

def add_schedule_item(course, day, time_slot, next_live_info):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO schedule (course_name, day, time_slot, next_live_info) VALUES (?, ?, ?, ?)",
                       (course.strip(), day.strip(), time_slot.strip(), next_live_info.strip()))
        conn.commit()

def get_student_schedule(course_name):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("SELECT day AS 'اليوم', time_slot AS 'الموعد', next_live_info AS 'موعد البث القادم' FROM schedule WHERE course_name = ?", conn, params=(course_name,))

def delete_schedule_item(item_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedule WHERE id = ?", (item_id,))
        conn.commit()

def check_course_live(course_name):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_live, room_id FROM course_live WHERE course_name = ?", (course_name.strip(),))
        res = cursor.fetchone()
        if res and res[0] == 'true':
            return True, res[1]
        return False, None

def set_course_live(course_name, is_live, room_id):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO course_live (course_name, is_live, room_id) VALUES (?, ?, ?)",
                       (course_name.strip(), 'true' if is_live else 'false', room_id.strip()))
        conn.commit()

def save_feedback(code, name, course, rating, message):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO live_feedback (student_code, student_name, course_name, rating, message) VALUES (?, ?, ?, ?, ?)",
                       (code, name, course, rating, message))
        conn.commit()

# =========================================================
# 3. الواجهات الرئيسية
# =========================================================
init_db()

page = st.sidebar.radio("التنقل:", ["🔴 القاعة والبث المباشر (للطالب)", "⚙️ لوحة تحكم المطور"])

# ---------------------------------------------------------
# واجهة الطالب
# ---------------------------------------------------------
if page == "🔴 القاعة والبث المباشر (للطالب)":
    st.title("🌟 منصة نوفا التعليمية - دخول القاعة")

    if "logged_student" not in st.session_state:
        st.session_state.logged_student = None

    if st.session_state.logged_student is None:
        st.subheader("🔑 تسجيل الدخول بالكود")
        input_code = st.text_input("أدخل كود الطالب المعتمد من المطور:", placeholder="مثال: NOVA-1001")
        
        if st.button("دخول القاعة 🚀"):
            stu = verify_student(input_code)
            if stu:
                st.session_state.logged_student = stu
                st.success("تم التحقق ودخول القاعة بنجاح!")
                st.rerun()
            else:
                st.error("❌ هذا الكود غير موجود أو غير مفعل. يرجى مراجعة المطور.")
    else:
        stu = st.session_state.logged_student
        student_course = stu['course_name']
        
        st.markdown(f"""
            <div class="profile-card">
                <h3>👤 مرحباً بك: {stu['student_name']}</h3>
                <p>📚 <b>المادة/الكورس المسجل فيه:</b> <span style="color: #4ade80; font-size: 18px;">{student_course}</span> | 🔑 <b>الكود:</b> {stu['student_code']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_nav1, col_nav2 = st.columns([4, 1])
        with col_nav2:
            if st.button("تسجيل خروج"):
                st.session_state.logged_student = None
                st.rerun()
        with col_nav1:
            if st.button("🔄 تحديث حالة البث فوراً"):
                st.rerun()

        st.divider()
        
        # فحص البث المباشر المخصص لمادة الطالب
        is_live, room_id = check_course_live(student_course)

        if is_live:
            st.markdown(f"<div class='live-active'>🔴 البث المباشر شغال الآن لمادة ({student_course})</div>", unsafe_allow_html=True)
            
            display_name = stu['student_name'].replace(" ", "_")
            jitsi_url = f"https://meet.jit.si/{room_id}#userInfo.displayName=%22{display_name}%22"
            
            # زر للفتح المباشر في نافذة خارجية لضمان عمل الصوت والصورة الشاشة بأعلى جودة
            st.markdown(f'<a href="{jitsi_url}" target="_blank" class="btn-external">🖥️ فتح القاعة في نافذة جديدة بدقة عالية</a>', unsafe_allow_html=True)
            
            # مضاعفة تصاريح الـ iframe لتفعيل الصوت، المايك، الشاشة والكاميرا
            components.html(f"""
                <iframe src="{jitsi_url}" 
                        allow="camera *; microphone *; display-capture *; autoplay *; clipboard-write *; fullscreen *"
                        allowfullscreen="true"
                        style="height: 650px; width: 100%; border: 0px; border-radius: 12px;">
                </iframe>
            """, height=670)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⭐ تقييم المحاضرة")
                rating = st.slider("نسبة التقييم (%):", 0, 100, 95, step=5)
            with c2:
                st.subheader("💬 إرسال استفسار للمطور")
                msg = st.text_area("أكتب استفسارك هنا:")
                if st.button("إرسال التقييم 📤"):
                    if msg.strip():
                        save_feedback(stu['student_code'], stu['student_name'], student_course, rating, msg)
                        st.success("تم إرسال الرسالة بنجاح!")
                    else:
                        st.warning("يرجى كتابة الرسالة أولاً.")
        else:
            st.info(f"⌛ لا يوجد بث مباشر شغال حالياً لمادة ({student_course}).")
            st.subheader(f"📅 مواعيد وجدول مادة: ({student_course})")
            
            df_sch = get_student_schedule(student_course)
            
            if df_sch.empty:
                st.warning("لم يقم المطور بإضافة مواعيد لهذه المادة بعد.")
            else:
                st.dataframe(df_sch, use_container_width=True)

# ---------------------------------------------------------
# واجهة المطور
# ---------------------------------------------------------
else:
    st.title("⚙️ لوحة إدارة منصة نوفا")
    admin_pass = st.text_input("كلمة سر المطور:", type="password")

    if admin_pass == st.secrets.get("ADMIN_PASSWORD", "2010"):
        st.success("أهلاً بك يا مطور المنصة 👋")
        
        t1, t2, t3, t4 = st.tabs(["🔑 إدارة الطلاب والأكواد", "📅 جدول المواعيد والبث", "🎙️ التحكم بالبث المباشر للمواد", "📊 التقييمات"])

        # Tab 1: الأكواد
        with t1:
            st.subheader("➕ إضافة كود طالب وتحديد المادة")
            with st.form("add_code_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_code = st.text_input("كود الطالب:", placeholder="مثال: NOVA-1001")
                with col2:
                    new_name = st.text_input("اسم الطالب الرباعي:")
                with col3:
                    new_course = st.selectbox("اختر المادة/الكورس:", AVAILABLE_COURSES)
                
                btn_save = st.form_submit_button("حفظ الكود 💾")

            if btn_save:
                if new_code and new_name and new_course:
                    ok, msg = add_student_code(new_code, new_name, new_course)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("يرجى إدخال كافة البيانات.")

            st.divider()
            st.subheader("📋 الأكواد المحفوظة")
            with sqlite3.connect(DB_NAME) as conn:
                df_codes = pd.read_sql_query("SELECT id, student_code, student_name, course_name FROM student_codes", conn)

            if df_codes.empty:
                st.info("لا توجد أكواد محفوظة.")
            else:
                for _, r in df_codes.iterrows():
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.write(f"🔑 **{r['student_code']}** | 👤 {r['student_name']} | 📚 المادة: **{r['course_name']}**")
                    with col_b:
                        if st.button("حذف الكود 🗑️", key=f"del_{r['id']}"):
                            delete_student_code(r['id'])
                            st.success("تم المسح.")
                            st.rerun()

        # Tab 2: الجدول
        with t2:
            st.subheader("➕ إضافة موعد وموعد البث القادم للمادة")
            with st.form("add_sched_form"):
                c1, c2 = st.columns(2)
                with c1:
                    sched_course = st.selectbox("حدد المادة:", AVAILABLE_COURSES)
                    sched_day = st.selectbox("اليوم:", ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"])
                with c2:
                    sched_time = st.text_input("موعد الحصة:", placeholder="مثال: الساعة 8:00 مساءً")
                    sched_next = st.text_input("تاريخ ووقت البث القادم:", placeholder="مثال: يوم الجمعة القادم الساعة 9:00 مساءً")
                
                btn_sched = st.form_submit_button("حفظ الموعد 💾")

            if btn_sched:
                if sched_course and sched_time:
                    add_schedule_item(sched_course, sched_day, sched_time, sched_next)
                    st.success("تم حفظ الموعد بنجاح!")
                    st.rerun()

            st.divider()
            st.subheader("📋 المواعيد المضافة")
            with sqlite3.connect(DB_NAME) as conn:
                df_all_sch = pd.read_sql_query("SELECT id, course_name, day, time_slot, next_live_info FROM schedule", conn)
                if df_all_sch.empty:
                    st.info("لا توجد مواعيد مضافة.")
                else:
                    for _, sr in df_all_sch.iterrows():
                        ca, cb = st.columns([4, 1])
                        with ca:
                            st.write(f"📚 **المادة:** {sr['course_name']} | 🗓️ **اليوم:** {sr['day']} | ⏰ **الموعد:** {sr['time_slot']} | 🔴 **البث القادم:** {sr['next_live_info']}")
                        with cb:
                            if st.button("حذف 🗑️", key=f"del_sch_{sr['id']}"):
                                delete_schedule_item(sr['id'])
                                st.rerun()

        # Tab 3: البث المباشر المخصص لكل مادة
        with t3:
            st.subheader("🎙️ إدارة وتشغيل البث المباشر الفوري للمواد")
            
            target_course = st.selectbox("اختر المادة المراد فتح البث لها الآن:", AVAILABLE_COURSES)
            
            clean_room_id = "nova_room_" + "".join([c for c in target_course if c.isalnum()])
            
            is_active, _ = check_course_live(target_course)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button(f"🚀 تشغيل البث فوراً لمادة: ({target_course})"):
                    set_course_live(target_course, True, clean_room_id)
                    st.success(f"تم فتح البث المباشر لمادة ({target_course}) بنجاح!")
                    st.rerun()
            
            with col_b2:
                if st.button(f"🛑 إيقاف البث لمادة: ({target_course})"):
                    set_course_live(target_course, False, clean_room_id)
                    st.warning(f"تم إغلاق البث المباشر لمادة ({target_course}).")
                    st.rerun()

            st.divider()
            if is_active:
                st.success(f"🔴 البث يعمل الآن بشكل مباشر لمادة: ({target_course})")
                dev_jitsi_url = f"https://meet.jit.si/{clean_room_id}#userInfo.displayName=%22المطور_المحاضر%22"
                
                st.markdown(f'<a href="{dev_jitsi_url}" target="_blank" class="btn-external">🖥️ فتح غرفة المحاضر في نافذة مستقلة (لمشاركة الشاشة بدون أي قيود)</a>', unsafe_allow_html=True)
                
                components.html(f"""
                    <iframe src="{dev_jitsi_url}" 
                            allow="camera *; microphone *; display-capture *; autoplay *; clipboard-write *; fullscreen *"
                            allowfullscreen="true"
                            style="height: 600px; width: 100%; border: 0px; border-radius: 12px;">
                    </iframe>
                """, height=620)
            else:
                st.info(f"⚪ البث مغلق حالياً لمادة: ({target_course})")

        # Tab 4: التقييمات
        with t4:
            st.subheader("📊 رسائل وتقييمات الطلاب")
            with sqlite3.connect(DB_NAME) as conn:
                df_fb = pd.read_sql_query("SELECT student_code AS 'الكود', student_name AS 'الاسم', course_name AS 'المادة', rating AS 'التقييم %', message AS 'الرسالة', created_at AS 'التاريخ' FROM live_feedback ORDER BY id DESC", conn)
                st.dataframe(df_fb, use_container_width=True)
