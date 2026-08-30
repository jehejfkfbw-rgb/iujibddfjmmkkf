import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# 1. إعدادات وتصميم الصفحة
# =========================================================
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="🌟", layout="wide")

st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-baseweb="input"] { text-align: right; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; background-color: #2e7d32; color: white; height: 42px; }
    .profile-card { background-color: #0f172a; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    .live-active { background-color: #15803d; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-weight: bold; font-size: 18px; }
    .direct-link-btn { display: block; width: 100%; background-color: #dc2626; color: white; padding: 14px; text-align: center; border-radius: 8px; font-weight: bold; font-size: 18px; text-decoration: none; margin-bottom: 15px; }
    .direct-link-btn:hover { background-color: #b91c1c; color: white; }
    .chat-box { background-color: #1e293b; color: white; padding: 12px; border-radius: 8px; max-height: 300px; overflow-y: auto; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# المواد المتاحة على المنصة
AVAILABLE_COURSES = [
    "لغة بايثون - تعلم البرمجة للمبتدئين",
    "أساسيات البرمجة للمبتدئين",
    "تطوير تطبيقات الويب (Streamlit & Flask)",
    "تطوير الألعاب (Godot & Pygame)"
]

# خريطة لربط كل مادة بغرفة بث مستقلة تماماً
COURSE_ROOMS = {
    "لغة بايثون - تعلم البرمجة للمبتدئين": "nova_room_python_exclusive_2026",
    "أساسيات البرمجة للمبتدئين": "nova_room_basics_exclusive_2026",
    "تطوير تطبيقات الويب (Streamlit & Flask)": "nova_room_web_exclusive_2026",
    "تطوير الألعاب (Godot & Pygame)": "nova_room_games_exclusive_2026"
}

# =========================================================
# 2. إدارة قاعدة البيانات
# =========================================================
DB_NAME = "nova_strict_isolation_v25.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT UNIQUE NOT NULL,
                student_name TEXT NOT NULL,
                course_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_live (
                course_name TEXT PRIMARY KEY,
                is_live TEXT DEFAULT 'false',
                room_id TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                day TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                next_live_info TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                student_name TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
        conn.commit()

def add_student_code(code, name, course):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO student_codes (student_code, student_name, course_name) VALUES (?, ?, ?)",
                           (code.strip(), name.strip(), course.strip()))
            conn.commit()
            return True, "تمت إضافة الطالب وتخصيص المادة بنجاح!"
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
        return pd.read_sql_query("SELECT day AS 'اليوم', time_slot AS 'موعد الحصة', next_live_info AS 'تفاصيل البث القادم' FROM schedule WHERE course_name = ?", conn, params=(course_name.strip(),))

def delete_schedule_item(item_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedule WHERE id = ?", (item_id,))
        conn.commit()

def check_course_live(course_name):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # فحص صارم للمادة المحددة فقط بالاسم بدقة
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

def add_chat_message(course_name, student_name, message):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO live_chat (course_name, student_name, message) VALUES (?, ?, ?)",
                       (course_name.strip(), student_name.strip(), message.strip()))
        conn.commit()

def get_chat_messages(course_name):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("SELECT student_name AS 'الطالب', message AS 'التعليق', created_at AS 'الوقت' FROM live_chat WHERE course_name = ? ORDER BY id DESC LIMIT 50", conn, params=(course_name.strip(),))

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

page = st.sidebar.radio("التنقل:", ["🔴 قاعة الطالب وبث المادة", "⚙️ لوحة تحكم المطور"])

# ---------------------------------------------------------
# واجهة الطالب
# ---------------------------------------------------------
if page == "🔴 قاعة الطالب وبث المادة":
    st.title("🌟 منصة نوفا التعليمية - بوابة الطالب")

    if "logged_student" not in st.session_state:
        st.session_state.logged_student = None

    if st.session_state.logged_student is None:
        st.subheader("🔑 تسجيل الدخول بالكود المعتمد")
        input_code = st.text_input("أدخل كود الطالب الخاص بك:", placeholder="مثال: NOVA-1001")
        
        if st.button("دخول القاعة الدراسية 🚀"):
            stu = verify_student(input_code)
            if stu:
                st.session_state.logged_student = stu
                st.success("تم التحقق بنجاح، أهلاً بك في قاعتك!")
                st.rerun()
            else:
                st.error("❌ هذا الكود غير صحيح أو لم يتم تفعيله من قبل المطور.")
    else:
        stu = st.session_state.logged_student
        student_course = stu['course_name']
        
        st.markdown(f"""
            <div class="profile-card">
                <h3>👤 الطالب: {stu['student_name']}</h3>
                <p>📚 <b>مادتك الدراسية المخصصة:</b> <span style="color: #4ade80; font-size: 18px;">{student_course}</span> | 🔑 <b>الكود:</b> {stu['student_code']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_nav1, col_nav2 = st.columns([4, 1])
        with col_nav2:
            if st.button("تسجيل خروج"):
                st.session_state.logged_student = None
                st.rerun()
        with col_nav1:
            if st.button("🔄 تحديث الصفحة والبث فوراً"):
                st.rerun()

        st.divider()
        
        # فحص حالة البث الخاص بالمادة الحالية فقط بدقة تامة
        is_live, room_id = check_course_live(student_course)

        if is_live:
            st.markdown(f"<div class='live-active'>🔴 البث المباشر شغال الآن لمادتك فقط: ({student_course})</div>", unsafe_allow_html=True)
            
            specific_room = COURSE_ROOMS.get(student_course, "nova_default_room_2026")
            student_view_url = f"https://vdo.ninja/?view={specific_room}&autoplay&codec=vp8&clean"
            
            st.markdown(f"""
                <a href="{student_view_url}" target="_blank" class="direct-link-btn">
                    🚀 اضغط هنا لفتح البث المباشر (شاشة كاملة وبأعلى جودة)
                </a>
            """, unsafe_allow_html=True)
            
            col_v1, col_v2 = st.columns([2, 1])
            with col_v1:
                st.info("📌 مشغل الفيديو المباشر للمادة داخل الصفحة:")
                components.html(f"""
                    <iframe src="{student_view_url}" 
                            allow="autoplay; fullscreen; microphone; speaker; display-capture"
                            style="height: 480px; width: 100%; border: 0px; border-radius: 12px; background: #000;">
                    </iframe>
                """, height=500)
            
            with col_v2:
                st.subheader("💬 شات التعليقات والأسئلة")
                chat_msg = st.text_input("اكتب سؤالك للأستاذ:", key="chat_input_val")
                if st.button("إرسال التعليق 📤"):
                    if chat_msg.strip():
                        add_chat_message(student_course, stu['student_name'], chat_msg)
                        st.success("تم إرسال تعليقك للأستاذ!")
                        st.rerun()
                    else:
                        st.warning("اكتب تعليقاً أولاً.")
                
                st.markdown("---")
                st.write("📜 **التعليقات الواردة للبث:**")
                df_chat = get_chat_messages(student_course)
                if df_chat.empty:
                    st.info("لا توجد تعليقات حتى الآن.")
                else:
                    for _, crow in df_chat.iterrows():
                        st.markdown(f"💬 **{crow['الطالب']}**: {crow['التعليق']}")
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⭐ تقييم المحاضرة")
                rating = st.slider("نسبة التقييم (%):", 0, 100, 95, step=5)
            with c2:
                st.subheader("💬 إرسال رسالة خاصة للمطور")
                msg = st.text_area("اكتب رسالتك هنا:")
                if st.button("إرسال للمطور 📤"):
                    if msg.strip():
                        save_feedback(stu['student_code'], stu['student_name'], student_course, rating, msg)
                        st.success("تم إرسال رسالتك بنجاح!")
                    else:
                        st.warning("يرجى كتابة الرسالة.")
        else:
            # لو البث مش شغال للمادة دي، تظهر رسالة التوقف + جدول المواعيد المستقل للمادة وحدها
            st.warning(f"⌛ لا يوجد بث مباشر شغال حالياً لمادة ({student_course}). تابع الجدول أدناه لمعرفة موعد المحاضرة القادمة.")
            
            st.subheader(f"📅 جدول مواعيد الحصص والبث القادم لمادتك فقط: ({student_course})")
            df_sch = get_student_schedule(student_course)
            if df_sch.empty:
                st.info("لم يقم المطور بإضافة جدول مواعيد لهذه المادة حتى الآن.")
            else:
                st.dataframe(df_sch, use_container_width=True)

# ---------------------------------------------------------
# واجهة المطور
# ---------------------------------------------------------
else:
    st.title("⚙️ لوحة إدارة منصة نوفا (المطور)")
    admin_pass = st.text_input("كلمة سر المطور:", type="password")

    if admin_pass == st.secrets.get("ADMIN_PASSWORD", "2010"):
        st.success("أهلاً بك يا مطور المنصة الفريد 👋")
        
        t1, t2, t3, t4 = st.tabs(["🔑 إدارة الطلاب والأكواد", "📅 جداول المواعيد المستقلة", "🎙️ التحكم ببث كل مادة على حدة", "📊 تعليقات ورسائل الطلاب"])

        with t1:
            st.subheader("➕ إضافة كود طالب جديد وتخصيص مادته الأساسية")
            with st.form("add_code_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_code = st.text_input("كود الطالب:", placeholder="مثال: NOVA-1001")
                with col2:
                    new_name = st.text_input("اسم الطالب الرباعي:")
                with col3:
                    new_course = st.selectbox("اختر المادة المخصصة له:", AVAILABLE_COURSES)
                
                btn_save = st.form_submit_button("حفظ الطالب والكود 💾")

            if btn_save:
                if new_code and new_name and new_course:
                    ok, msg = add_student_code(new_code, new_name, new_course)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("يرجى إكمال كافة البيانات المطلوبة.")

            st.divider()
            st.subheader("📋 قائمة الطلاب المسجلين وأكوادهم")
            with sqlite3.connect(DB_NAME) as conn:
                df_codes = pd.read_sql_query("SELECT id, student_code, student_name, course_name FROM student_codes", conn)

            if df_codes.empty:
                st.info("لا توجد أكواد مسجلة حالياً.")
            else:
                for _, r in df_codes.iterrows():
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.write(f"🔑 **{r['student_code']}** | 👤 {r['student_name']} | 📚 المادة: **{r['course_name']}**")
                    with col_b:
                        if st.button("حذف 🗑️", key=f"del_{r['id']}"):
                            delete_student_code(r['id'])
                            st.success("تم الحذف.")
                            st.rerun()

        with t2:
            st.subheader("➕ إضافة موعد حصة أو بث خاص لمادة معينة")
            with st.form("add_sched_form"):
                c1, c2 = st.columns(2)
                with c1:
                    sched_course = st.selectbox("اختر المادة لإضافة جدولها:", AVAILABLE_COURSES, key="sc_course")
                    sched_day = st.selectbox("اليوم:", ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"])
                with c2:
                    sched_time = st.text_input("موعد الحصة:", placeholder="مثال: الساعة 8:00 مساءً")
                    sched_next = st.text_input("موعد البث القادم بالتفصيل:", placeholder="مثال: الجمعة القادمة الساعة 9 م")
                
                btn_sched = st.form_submit_button("حفظ موعد المادة 💾")

            if btn_sched:
                if sched_course and sched_time:
                    add_schedule_item(sched_course, sched_day, sched_time, sched_next)
                    st.success("تم حفظ موعد هذه المادة بنجاح!")
                    st.rerun()

            st.divider()
            st.subheader("📋 جميع المواعيد والجداول مرتبة حسب المواد")
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
                                st.rerun()

        with t3:
            st.subheader("🎙️ التحكم المستقل تماماً ببث كل مادة على حدة")
            
            target_course = st.selectbox("اختر المادة المراد إدارة بثها الآن:", AVAILABLE_COURSES, key="live_target")
            specific_room = COURSE_ROOMS.get(target_course, "nova_default_room_2026")
            
            is_active, _ = check_course_live(target_course)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button(f"🚀 فتح بث هذه المادة حصرياً: ({target_course})"):
                    set_course_live(target_course, True, specific_room)
                    st.success(f"تم فتح البث الحصري لمادة ({target_course}) وحدها بنجاح!")
                    st.rerun()
            
            with col_b2:
                if st.button(f"🛑 إيقاف بث هذه المادة فقط: ({target_course})"):
                    set_course_live(target_course, False, specific_room)
                    st.warning(f"تم إغلاق البث الخاص بهذه المادة وتحويل طلابها لجدول المواعيد.")
                    st.rerun()

            st.divider()
            if is_active:
                st.success(f"🔴 البث المباشر **مفتوح الآن** وحصري لمادة: ({target_course})")
                
                source_type = st.radio("اختر وسيلة الإرسال:", ["🖥️ بث شاشة اللابتوب (Screen Share)", "📷 بث كاميرا اللابتوب"])
                
                if "شاشة" in source_type:
                    dev_push_url = f"https://vdo.ninja/?push={specific_room}&screenshare&quality=0&autostart"
                else:
                    dev_push_url = f"https://vdo.ninja/?push={specific_room}&webcam&quality=0&autostart"

                st.info("📌 اضغط على زر (Start) في المشغل أدناه لبث هذه المادة لطلابها فقط:")

                components.html(f"""
                    <iframe src="{dev_push_url}" 
                            allow="camera; microphone; display-capture; autoplay"
                            style="height: 550px; width: 100%; border: 0px; border-radius: 12px; background: #111;">
                    </iframe>
                """, height=570)
                
                st.subheader(f"💬 تعليقات طلاب مادة ({target_course}) الحية للأستاذ:")
                df_live_chats = get_chat_messages(target_course)
                if df_live_chats.empty:
                    st.info("لم يرسل أي طالب تعليقاً بعد.")
                else:
                    for _, lcr in df_live_chats.iterrows():
                        st.markdown(f"👤 **{lcr['الطالب']}**: {lcr['التعليق']} ⏱️ *({lcr['الوقت']})*")
            else:
                st.info(f"⚪ البث مغلق تماماً لمادة: ({target_course}). ولن يظهر لطلابها أي بث.")

        with t4:
            st.subheader("📊 رسائل واستفسارات الطلاب الواردة")
            with sqlite3.connect(DB_NAME) as conn:
                df_fb = pd.read_sql_query("SELECT student_code AS 'الكود', student_name AS 'اسم الطالب', course_name AS 'المادة', rating AS 'التقييم %', message AS 'رسالة الطالب', created_at AS 'التاريخ' FROM live_feedback ORDER BY id DESC", conn)
                st.dataframe(df_fb, use_container_width=True)
