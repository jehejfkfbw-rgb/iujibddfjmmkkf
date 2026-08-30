import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# 1. إعدادات وتصميم الصفحة
# =========================================================
st.set_page_config(page_title="منصة نوفا التعليمية - البث المباشر", page_icon="🌟", layout="wide")

st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-baseweb="input"] { text-align: right; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; background-color: #2e7d32; color: white; height: 42px; }
    .profile-card { background-color: #0f172a; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    .info-box { background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. إدارة قاعدة البيانات (ربط المادة بالجدول)
# =========================================================
DB_NAME = "nova_platform.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. جدول أكواد الطلاب
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT UNIQUE NOT NULL,
                student_name TEXT NOT NULL,
                course_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. جدول إعدادات البث المباشر
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_room (
                id INTEGER PRIMARY KEY,
                is_live TEXT DEFAULT 'false',
                room_id TEXT DEFAULT 'nova_room_1'
            )
        """)
        cursor.execute("INSERT OR REPLACE INTO live_room (id, is_live, room_id) VALUES (1, 'false', 'nova_room_1')")
        
        # 3. جدول التقييمات
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
        
        # 4. جدول مواعيد المواد (مرتبط باسم المادة)
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

# --- وظائف التحكم بالأكواد والجدول ---
def add_student_code(code, name, course):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO student_codes (student_code, student_name, course_name) VALUES (?, ?, ?)",
                           (code.strip(), name.strip(), course.strip()))
            conn.commit()
            return True, "تمت إضافة الكود وحفظه بنجاح!"
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

def get_live_status():
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_live, room_id FROM live_room WHERE id = 1")
        res = cursor.fetchone()
        return (res[0] == 'true', res[1]) if res else (False, 'nova_room_1')

def set_live_status(is_live, room_id):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE live_room SET is_live = ?, room_id = ? WHERE id = 1", 
                       ('true' if is_live else 'false', room_id))
        conn.commit()

def save_feedback(code, name, rating, message):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO live_feedback (student_code, student_name, rating, message) VALUES (?, ?, ?, ?)",
                       (code, name, rating, message))
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
        
        st.markdown(f"""
            <div class="profile-card">
                <h3>👤 مرحباً بك: {stu['student_name']}</h3>
                <p>📚 <b>المادة/الكورس المسجل فيه:</b> <span style="color: #4ade80;">{stu['course_name']}</span> | 🔑 <b>الكود:</b> {stu['student_code']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("تسجيل خروج"):
            st.session_state.logged_student = None
            st.rerun()

        st.divider()
        is_live, room_id = get_live_status()

        if is_live:
            st.subheader(f"🔴 البث المباشر شغال الآن لمادة ({stu['course_name']})")
            
            display_name = stu['student_name'].replace(" ", "_")
            jitsi_url = f"https://meet.jit.si/{room_id}#userInfo.displayName=%22{display_name}%22"
            
            components.html(f"""
                <iframe src="{jitsi_url}" 
                        allow="camera; microphone; display-capture; autoplay; clipboard-write"
                        style="height: 600px; width: 100%; border: 0px; border-radius: 12px;">
                </iframe>
            """, height=620)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⭐ تقييم الشرح")
                rating = st.slider("نسبة التقييم (%):", 0, 100, 95, step=5)
            with c2:
                st.subheader("💬 إرسال رسالة للمطور")
                msg = st.text_area("أكتب استفسارك هنا:")
                if st.button("إرسال التقييم 📤"):
                    if msg.strip():
                        save_feedback(stu['student_code'], stu['student_name'], rating, msg)
                        st.success("تم إرسال الرسالة بنجاح!")
                    else:
                        st.warning("يرجى كتابة الرسالة أولاً.")
        else:
            st.info("⌛ لا يوجد بث مباشر شغال حالياً.")
            st.subheader(f"📅 مواعيد مادة: ({stu['course_name']})")
            
            df_sch = get_student_schedule(stu['course_name'])
            
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
        
        t1, t2, t3, t4 = st.tabs(["🔑 إدارة أكواد الطلاب", "📅 ضبط مواعيد المواد والبث", "🎙️ التحكم بالبث المباشر", "📊 التقييمات"])

        # Tab 1: إضافة وحفظ الأكواد
        with t1:
            st.subheader("➕ إضافة كود طالب وتحديد المادة")
            with st.form("add_code_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_code = st.text_input("كود الطالب:", placeholder="مثال: NOVA-1001")
                with col2:
                    new_name = st.text_input("اسم الطالب الرباعي:")
                with col3:
                    new_course = st.text_input("المادة/الكورس:", placeholder="مثال: لغة بايثون / أساسيات البرمجة")
                
                btn_save = st.form_submit_button("حفظ الكود في قاعدة البيانات 💾")

            if btn_save:
                if new_code and new_name and new_course:
                    ok, msg = add_student_code(new_code, new_name, new_course)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("يرجى كتابة كافة البيانات.")

            st.divider()
            st.subheader("📋 الأكواد المحفوظة حالياً")
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
                            st.success("تم مسح الكود.")
                            st.rerun()

        # Tab 2: إضافة مواعيد المواد
        with t2:
            st.subheader("➕ إضافة موعد وموعد البث القادم لكل مادة")
            with st.form("add_sched_form"):
                c1, c2 = st.columns(2)
                with c1:
                    sched_course = st.text_input("اسم المادة بالضبط:", placeholder="مثال: لغة بايثون")
                    sched_day = st.selectbox("اليوم:", ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"])
                with c2:
                    sched_time = st.text_input("موعد الحصة/المحاضرة:", placeholder="مثال: الساعة 8:00 مساءً")
                    sched_next = st.text_input("تاريخ ووقت البث المباشر القادم:", placeholder="مثال: يوم الجمعة القادم الساعة 9:00 مساءً")
                
                btn_sched = st.form_submit_button("حفظ موعد المادة 💾")

            if btn_sched:
                if sched_course and sched_time:
                    add_schedule_item(sched_course, sched_day, sched_time, sched_next)
                    st.success("تم إضافة الموعد بنجاح!")
                    st.rerun()
                else:
                    st.error("يرجى إدخال المادة والموعد.")

            st.divider()
            st.subheader("📋 المواعيد المضافة حالياً")
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
                            if st.button("حذف الموعد 🗑️", key=f"del_sch_{sr['id']}"):
                                delete_schedule_item(sr['id'])
                                st.success("تم مسح الموعد.")
                                st.rerun()

        # Tab 3: إدارة البث المباشر
        with t3:
            is_live_act, room_id_act = get_live_status()
            st.subheader("🔴 تشغيل / إيقاف البث")
            
            r_name = st.text_input("معرف القاعة (Room ID):", value=room_id_act)
            
            if not is_live_act:
                if st.button("🚀 بدء البث المباشر الآن للطلاب"):
                    set_live_status(True, r_name)
                    st.success("تم فتح البث المباشر! الطلاب يستطيعون الدخول فوراً.")
                    st.rerun()
            else:
                st.warning("البث مباشر يعمل حالياً.")
                
                dev_jitsi_url = f"https://meet.jit.si/{r_name}#userInfo.displayName=%22المطور_المحاضر%22"
                components.html(f"""
                    <iframe src="{dev_jitsi_url}" 
                            allow="camera; microphone; display-capture; autoplay; clipboard-write"
                            style="height: 550px; width: 100%; border: 0px; border-radius: 12px;">
                    </iframe>
                """, height=570)

                if st.button("🛑 إنهاء البث المباشر"):
                    set_live_status(False, r_name)
                    st.success("تم إنهاء البث المباشر وإغلاق القاعة.")
                    st.rerun()

        # Tab 4: التقييمات
        with t4:
            st.subheader("📊 رسائل وتقييمات الطلاب")
            with sqlite3.connect(DB_NAME) as conn:
                df_fb = pd.read_sql_query("SELECT student_code AS 'الكود', student_name AS 'الاسم', rating AS 'التقييم %', message AS 'الرسالة', created_at AS 'التاريخ' FROM live_feedback ORDER BY id DESC", conn)
                st.dataframe(df_fb, use_container_width=True)
