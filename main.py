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
DB_NAME = "nova_strict_isolation_v31.db"

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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                video_title TEXT NOT NULL,
                video_data BLOB NOT NULL,
                file_name TEXT NOT NULL,
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

def save_course_video(course_name, video_title, video_file):
    init_db()
    bytes_data = video_file.read()
    file_name = video_file.name
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO course_videos (course_name, video_title, video_data, file_name) VALUES (?, ?, ?, ?)",
                       (course_name, video_title, bytes_data, file_name))
        conn.commit()

def get_course_videos(course_name):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, video_title, video_data, file_name, created_at FROM course_videos WHERE course_name = ? ORDER BY id DESC", (course_name,))
        return cursor.fetchall()

def delete_course_video(video_id):
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM course_videos WHERE id = ?", (video_id,))
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
            if st.button("🔄 تحديث الصفحة وبث المادة فوراً"):
                st.rerun()

        st.divider()
        
        # التبويبات الخاصة بالطالب (البث المباشر vs الفيديوهات المسجلة والجدول)
        tab_live_s, tab_vids_s = st.tabs(["🔴 البث المباشر وغرفة الحصة", "📼 مكتبة الفيديوهات المسجلة والمراجعات"])

        with tab_live_s:
            # فحص حالة البث الخاص بالمادة الحالية فقط بدقة تامة
            is_live, room_id = check_course_live(student_course)

            if is_live:
                st.markdown(f"<div class='live-active'>🔴 البث المباشر شغال الآن لمادتك فقط: ({student_course})</div>", unsafe_allow_html=True)
                
                specific_room = COURSE_ROOMS.get(student_course, "nova_room_default")
                student_view_url = f"https://vdo.ninja/?view={specific_room}&autoplay=1&codec=vp9&bitrate=5000&maxbitrate=8000&quality=0&clean&roomscale=1"
                
                st.markdown(f"""
                    <a href="{student_view_url}" target="_blank" class="direct-link-btn">
                        🚀 اضغط هنا لفتح البث المباشر (شاشة كاملة وبأعلى جودة HD فائقة)
                    </a>
                """, unsafe_allow_html=True)
                
                col_v1, col_v2 = st.columns([2, 1])
                with col_v1:
                    st.info("📌 مشغل الفيديو المباشر للمادة (يملا الشاشة تماماً بدون أي فراغات):")
                    components.html(f"""
                        <div style="position: relative; width: 100%; height: 600px; background: #000; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                            <iframe src="{student_view_url}" 
                                    allow="autoplay; fullscreen; microphone; speaker; display-capture"
                                    allowfullscreen="true"
                                    webkitallowfullscreen="true"
                                    mozallowfullscreen="true"
                                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; object-fit: cover;">
                            </iframe>
                        </div>
                    """, height=620)
                
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
                st.warning(f"⌛ لا يوجد بث مباشر شغال حالياً لمادة ({student_course}). تابع الجدول أدناه لمعرفة موعد المحاضرة القادمة.")
                
                st.subheader(f"📅 جدول مواعيد الحصص والبث القادم لمادتك فقط: ({student_course})")
                df_sch = get_student_schedule(student_course)
                if df_sch.empty:
                    st.info("لم يقم المطور بإضافة جدول مواعيد لهذه المادة حتى الآن.")
                else:
                    st.dataframe(df_sch, use_container_width=True)

        with tab_vids_s:
            st.subheader(f"📼 الفيديوهات والشروحات المسجلة الخاصة بمادتك: ({student_course})")
            vids = get_course_videos(student_course)
            if not vids:
                st.info("لا توجد فيديوهات مسجلة مرفوعة لهذه المادة حتى الآن.")
            else:
                for v_id, v_title, v_data, f_name, c_at in vids:
                    st.markdown(f"### 📌 {v_title}")
                    st.text(f"تاريخ الرفع: {c_at}")
                    st.video(v_data)
                    st.download_button(
                        label=f"📥 تحميل فيديو ({v_title}) على جهازك",
                        data=v_data,
                        file_name=f_name,
                        mime="video/mp4",
                        key=f"dl_vid_{v_id}"
                    )
                    st.divider()

# ---------------------------------------------------------
# واجهة المطور
# ---------------------------------------------------------
else:
    st.title("⚙️ لوحة إدارة منصة نوفا (المطور)")
    admin_pass = st.text_input("كلمة سر المطور:", type="password")

    if admin_pass == st.secrets.get("ADMIN_PASSWORD", "2010"):
        st.success("أهلاً بك يا مطور المنصة الفريد 👋")
        
        t1, t2, t3, t4, t5 = st.tabs([
            "🔑 إدارة الطلاب والأكواد", 
            "📅 جداول المواعيد المستقلة", 
            "🎙️ التحكم ببث كل مادة", 
            "📼 رفع وإدارة فيديوهات الكورسات", 
            "📊 تعليقات ورسائل الطلاب"
        ])

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
            specific_room = COURSE_ROOMS.get(target_course, "nova_room_default")
            
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
                    dev_push_url = f"https://vdo.ninja/?push={specific_room}&screenshare&quality=0&bitrate=5000&maxbitrate=8000&codec=vp9&autostart"
                else:
                    dev_push_url = f"https://vdo.ninja/?push={specific_room}&webcam&quality=0&bitrate=4000&maxbitrate=6000&codec=vp9&autostart"

                st.info("📌 اضغط على زر (Start) في المشغل أدناه لبث هذه المادة لطلابها بجودة فائقة HD:")

                components.html(f"""
                    <iframe src="{dev_push_url}" 
                            allow="camera; microphone; display-capture; autoplay"
                            style="height: 500px; width: 100%; border: 0px; border-radius: 12px; background: #111;">
                    </iframe>
                """, height=520)
                
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
            st.subheader("📼 رفع فيديو جديد لكل كورس ليظهر لطلابه فقط وتتم حفظه في النظام")
            with st.form("upload_vid_form"):
                up_course = st.selectbox("اختر المادة المراد رفع الفيديو لها:", AVAILABLE_COURSES, key="up_vid_c")
                up_title = st.text_input("عنوان الفيديو أو المحاضرة:", placeholder="مثال: المحاضرة الأولى: مقدمة بايثون")
                up_file = st.file_uploader("اختر ملف الفيديو (MP4):", type=["mp4", "mov", "avi"])
                btn_up_vid = st.form_submit_button("رفع وحفظ الفيديو في المنصة 🚀")

            if btn_up_vid:
                if up_course and up_title and up_file:
                    save_course_video(up_course, up_title, up_file)
                    st.success("تم رفع وحفظ الفيديو بنجاح، وأصبح متاحاً لطلاب المادة فوراً!")
                    st.rerun()
                else:
                    st.error("يرجى اختيار المادة وكتابة العنوان وإرفاق ملف الفيديو.")

            st.divider()
            st.subheader("📋 الفيديوهات المرفوعة حالياً في المنصة")
            for c in AVAILABLE_COURSES:
                st.markdown(f"### 📚 مادة: {c}")
                vids_list = get_course_videos(c)
                if not vids_list:
                    st.info("لا توجد فيديوهات مرفوعة لهذه المادة.")
                else:
                    for v_id, v_title, v_data, f_name, c_at in vids_list:
                        col_v1, col_v2 = st.columns([4, 1])
                        with col_v1:
                            st.write(f"🎬 **{v_title}** | الملف: {f_name} | تاريخ الرفع: {c_at}")
                        with col_v2:
                            if st.button("حذف الفيديو 🗑️", key=f"del_v_{v_id}"):
                                delete_course_video(v_id)
                                st.success("تم حذف الفيديو.")
                                st.rerun()

        with t5:
            st.subheader("📊 رسائل واستفسارات الطلاب الواردة")
            with sqlite3.connect(DB_NAME) as conn:
                df_fb = pd.read_sql_query("SELECT student_code AS 'الكود', student_name AS 'اسم الطالب', course_name AS 'المادة', rating AS 'التقييم %', message AS 'رسالة الطالب', created_at AS 'التاريخ' FROM live_feedback ORDER BY id DESC", conn)
                st.dataframe(df_fb, use_container_width=True)
