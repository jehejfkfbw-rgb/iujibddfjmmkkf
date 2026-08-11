import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import datetime
import hashlib
import os

# إعدادات الصفحة
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="⚡", layout="wide")

DB_NAME = "nova_platform.db"
MEDIA_DIR = "media"

# التأكد من إنشاء مجلد الوسائط بدون مسافات خفية
os.makedirs(MEDIA_DIR, exist_ok=True)

# تهيئة قاعدة البيانات والجدول الأساسية
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # جدول المستخدمين
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        phone TEXT PRIMARY KEY,
                        name TEXT,
                        password TEXT,
                        role TEXT,
                        is_blocked INTEGER DEFAULT 0
                    )''')
        # جدول الأساتذة
        c.execute('''CREATE TABLE IF NOT EXISTS teachers (
                        phone TEXT PRIMARY KEY,
                        name TEXT,
                        subject TEXT,
                        price REAL,
                        room_id TEXT,
                        is_blocked INTEGER DEFAULT 0
                    )''')
        # جدول الاشتراكات
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_phone TEXT,
                        teacher_phone TEXT,
                        status TEXT,
                        wallet_number TEXT
                    )''')
        # جدول المنشورات والفيديوهات
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_phone TEXT,
                        title TEXT,
                        media_type TEXT,
                        file_path TEXT,
                        status TEXT
                    )''')
        # جدول البلاغات
        c.execute('''CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_phone TEXT,
                        student_name TEXT,
                        message TEXT,
                        timestamp TEXT,
                        status TEXT
                    )''')
        # جدول الإعدادات
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )''')
        # جدول استعادة كلمة المرور
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
                        phone TEXT PRIMARY KEY,
                        code TEXT
                    )''')
        conn.commit()

init_db()

# دالة لجلب الإعدادات
def get_setting(key, default=""):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = c.fetchone()
            return row[0] if row else default
    except:
        return default

# تشفير كلمات المرور
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# إدارة الجلسة (Session State)
if "user_phone" not in st.session_state:
    st.session_state.user_phone = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

def login_user(phone, role):
    st.session_state.user_phone = phone
    st.session_state.user_role = role

def logout_user():
    st.session_state.user_phone = None
    st.session_state.user_role = None

# ==========================================
# الدوال المساعدة لبطاقات الطلاب والمعلمين
# ==========================================
def render_student_teacher_card(t_name, t_sub, t_price, room_id, t_phone, student_phone):
    st.markdown(f"""
    <div style="background: #1e1e2f; padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #4f46e5;">
        <h3 style="color: #6366f1; margin: 0 0 10px 0;">الأستاذ: {t_name}</h3>
        <p style="margin: 5px 0;"><b>المادة:</b> {t_sub}</p>
        <p style="margin: 5px 0;"><b>سعر الاشتراك الشهري:</b> {t_price} جنيه</p>
    </div>
    """, unsafe_allow_html=True)

    # التحقق من حالة الاشتراك
    sub_status = None
    wallet_used = ""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT status, wallet_number FROM subscriptions WHERE student_phone=? AND teacher_phone=?", (student_phone, t_phone))
            row = c.fetchone()
            if row:
                sub_status, wallet_used = row
    except:
        pass

    if sub_status == "approved":
        st.success("✅ أنت مشترك بالفعل مع هذا الأستاذ ومصرح لك بالمشاهدة.")
        
        # عرض محتوى البث المباشر إن وجد
        st.markdown("---")
        st.markdown(f"🔴 **البث المباشر المخصص (Room ID: `{room_id}`):**")
        stream_html = f"""
        <iframe src="https://vdo.ninja/?view={room_id}&autoplay=1" 
                style="width: 100%; height: 320px; border: 2px solid #10b981; border-radius: 12px; background: #000;"
                allow="camera; microphone; autoplay" allowfullscreen>
        </iframe>
        """
        components.html(stream_html, height=340)

        # عرض المحتوى والفيديوهات المسجلة أو المنشورة
        st.markdown("---")
        st.subheader("📁 الفيديوهات والملفات التعليمية الخاصة بالاستاذ")
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT title, media_type, file_path FROM posts WHERE teacher_phone=? AND status='approved'", (t_phone,))
                posts = c.fetchall()
            if posts:
                for p_title, p_type, p_path in posts:
                    st.markdown(f"**{p_title}**")
                    if os.path.exists(p_path):
                        if p_type == "video":
                            st.video(p_path)
                        elif p_type == "image":
                            st.image(p_path)
                    else:
                        st.warning("الملف غير متوفر حالياً على الخادم.")
            else:
                st.info("لا توجد منشورات مرفوعة حالياً من هذا الأستاذ.")
        except Exception as e:
            st.error(f"خطأ في تحميل المحتوى: {e}")

    elif sub_status == "pending":
        st.warning(f"⏳ طلب اشتراكك قيد المراجعة من قبل الأستاذ (تم التحويل من محفظة: {wallet_used})")
    else:
        with st.form(f"sub_form_{t_phone}"):
            st.write("💳 للحصول على الاشتراك، قم بالتحويل على محفظة الأستاذ التالية: `010XXXXXXXX`")
            w_num = st.text_input("أدخل رقم المحفظة التي قمت بالتحويل منها:")
            sub_btn = st.form_submit_button("إرسال طلب الاشتراك بعد التحويل")
            if sub_btn:
                if w_num:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT OR REPLACE INTO subscriptions (student_phone, teacher_phone, status, wallet_number) VALUES (?, ?, 'pending', ?)",
                                      (student_phone, t_phone, w_num))
                            conn.commit()
                        st.success("✔️ تم إرسال طلب اشتراكك بنجاح! ينتظر موافقة الأستاذ.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"خطأ في إرسال الطلب: {e}")
                else:
                    st.error("يرجى إدخال رقم المحفظة المحول منها!")

def display_teacher_requests(teacher_phone):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT student_phone, wallet_number, status FROM subscriptions WHERE teacher_phone=?", (teacher_phone,))
            requests = c.fetchall()
            
        if requests:
            for s_ph, w_num, stat in requests:
                col1, col2, col3 = st.columns([2, 2, 2])
                col1.write(f"📱 طالب: `{s_ph}`")
                col2.write(f"💳 محفظة: `{w_num}`")
                
                if stat == "pending":
                    if col3.button("✔️ قبول الاشتراك", key=f"acc_{s_ph}"):
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE subscriptions SET status='approved' WHERE student_phone=? AND teacher_phone=?", (s_ph, teacher_phone))
                            conn.commit()
                        st.success("تم قبول الطالب بنجاح!")
                        st.rerun()
                else:
                    col3.write("✅ مقبول")
        else:
            info_box = st.empty()
            info_box.info("لا توجد طلبات اشتراك معلقة حتى الآن.")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")

def render_live_chat(room_id, teacher_name):
    st.markdown("### 💬 الدردشة التفاعلية للبث المباشر")
    chat_box_html = f"""
    <iframe src="https://vdo.ninja/?chat={room_id}&name={teacher_name}" 
            style="width: 100%; height: 250px; border: 1px solid #4f46e5; border-radius: 8px; background: #111;"
            allowfullscreen>
    </iframe>
    """
    components.html(chat_box_html, height=270)

# ==========================================
# الواجهة الرئيسية (التسجيل الدخول وإنشاء الحسابات)
# ==========================================
st.markdown("<h1 style='text-align: center; color: #6366f1;'>⚡ منصة نوفا التعليمية</h1>", unsafe_allow_html=True)
st.write("---")

if st.session_state.user_phone is None:
    tab_login, tab_register, tab_forgot = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب جديد", "🔄 استعادة كلمة المرور"])

    with tab_login:
        st.subheader("تسجيل الدخول إلى حسابك")
        with st.form("login_form"):
            l_phone = st.text_input("رقم الهاتف:")
            l_pass = st.text_input("كلمة المرور:", type="password")
            login_submit = st.form_submit_button("دخول")
            
            if login_submit:
                if l_phone and l_pass:
                    hashed_p = hash_password(l_pass)
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT phone, role, is_blocked, password FROM users WHERE phone=?", (l_phone,))
                            user_data = c.fetchone()
                            
                        if user_data:
                            db_phone, db_role, db_blocked, db_pass = user_data
                            if db_blocked == 1:
                                st.error("🚫 هذا الحساب محظور من قبل الإدارة!")
                            elif db_pass == hashed_p:
                                login_user(db_phone, db_role)
                                st.success("✔️ تم تسجيل الدخول بنجاح!")
                                st.rerun()
                            else:
                                st.error("❌ كلمة المرور غير صحيحة!")
                        else:
                            st.error("❌ رقم الهاتف غير مسجل!")
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
                else:
                    st.error("يرجى ملء جميع الحقول المطلوبة!")

    with tab_register:
        st.subheader("إنشاء حساب جديد في المنصة")
        reg_role = st.selectbox("نوع الحساب:", ["طالب", "أستاذ"])
        
        with st.form("register_form"):
            r_name = st.text_input("الاسم الكامل:")
            r_phone = st.text_input("رقم الهاتف:")
            r_pass = st.text_input("كلمة المرور:", type="password")
            
            # حقول خاصة بالأساتذة فقط
            t_secret_code = ""
            t_sub = ""
            t_price = 0.0
            t_room = ""
            
            if reg_role == "أستاذ":
                t_secret_code = st.text_input("الكود السري لإنشاء حساب أستاذ:", type="password")
                t_sub = st.text_input("المادة الدراسية:")
                t_price = st.number_input("سعر الاشتراك الشهري (بالجنيه):", min_value=0.0, value=100.0)
                t_room = st.text_input("ررفم غرفة البث (Room ID فريد):", value=f"nova_{int(datetime.datetime.now().timestamp())}")
                
            reg_submit = st.form_submit_button("تسجيل الحساب")
            
            if reg_submit:
                if r_name and r_phone and r_pass:
                    if reg_role == "أستاذ":
                        system_secret = get_setting("teacher_secret", "901000")
                        if t_secret_code != system_secret:
                            st.error("🚫 الكود السري للأساتذة غير صحيح!")
                            st.stop()
                    
                    hashed_reg_pass = hash_password(r_pass)
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO users (phone, name, password, role, is_blocked) VALUES (?, ?, ?, ?, 0)",
                                      (r_phone, r_name, hashed_reg_pass, reg_role))
                            
                            if reg_role == "أستاذ":
                                c.execute("INSERT INTO teachers (phone, name, subject, price, room_id, is_blocked) VALUES (?, ?, ?, ?, ?, 0)",
                                          (r_phone, r_name, t_sub, t_price, t_room))
                                          
                            conn.commit()
                        st.success("✔️ تم إنشاء الحساب بنجاح! يمكنك الانتقال لتبويب تسجيل الدخول.")
                    except sqlite3.IntegrityError:
                        st.error("🚫 رقم الهاتف مستخدم من قبل بالفعل!")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء التسجيل: {e}")
                else:
                    st.error("يرجى استيفاء جميع الحقول المطلوبة!")

    with tab_forgot:
        st.subheader("استعادة كلمة المرور")
        with st.form("forgot_form"):
            reset_phone = st.text_input("رقم الهاتف المراد استعادته:")
            send_code_btn = st.form_submit_button("إرسال كود التأكيد التجريبي")
            
            if send_code_btn:
                if reset_phone:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT phone FROM users WHERE phone=?", (reset_phone,))
                            if c.fetchone():
                                dummy_code = "1234"
                                c.execute("INSERT OR REPLACE INTO password_resets (phone, code) VALUES (?, ?)", (reset_phone, dummy_code))
                                conn.commit()
                                st.info(f"💡 (وضع الاختبار) كود التأكيد الخاص برقمك هو: **{dummy_code}**")
                            else:
                                st.error("رقم الهاتف غير مسجل في النظام!")
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
                else:
                    st.error("يرجى إدخال رقم الهاتف!")

        with st.form("verify_reset_form"):
            reset_phone_v = st.text_input("رقم الهاتف:")
            entered_code = st.text_input("كود التأكيد:")
            new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
            verify_btn = st.form_submit_button("تحديث كلمة المرور")
            
            if verify_btn:
                if reset_phone_v and entered_code and new_pass:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("SELECT code FROM password_resets WHERE phone=?", (reset_phone_v,))
                        r_row = c.fetchone()
                        
                    if r_row and r_row[0] == entered_code:
                        hashed_new_pass = hash_password(new_pass)
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE users SET password=? WHERE phone=?", (hashed_new_pass, reset_phone_v))
                            c.execute("DELETE FROM password_resets WHERE phone=?", (reset_phone_v,))
                            conn.commit()
                        st.success("✔️ تم تحديث كلمة المرور بنجاح! يمكنك تسجيل الدخول الآن.")
                    else:
                        st.error("🚫 كود التأكيد غير صحيح!")
                else:
                    st.error("يرجى ملء جميع الحقول!")

else:
    # ==========================================
    # لوحات التحكم للمستخدمين المسجلين
    # ==========================================
    user_phone = st.session_state.user_phone
    user_role = st.session_state.user_role

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.write(f"👤 مرحبًا بك | صلاحية الحساب: **{user_role}**")
    with col_h2:
        if st.button("🚪 تسجيل خروج"):
            logout_user()
            st.rerun()
    st.write("---")

    # لوحة تحكم الطالب
    if user_role == "طالب":
        st.subheader("📚 قائمة الأساتذة والمواد المتاحة للانضمام")
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, subject, price, room_id, phone FROM teachers WHERE is_blocked=0")
                all_teachers = c.fetchall()
                
            if all_teachers:
                for t_name, t_sub, t_price, room_id, t_phone in all_teachers:
                    render_student_teacher_card(t_name, t_sub, t_price, room_id, t_phone, user_phone)
            else:
                st.info("لا توجد أساتذة متاحين حالياً في المنصة.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء تحميل الأساتذة: {e}")

        st.write("---")
        st.subheader("⚠️ الإبلاغ عن مشكلة أو التواصل مع الدعم")
        with st.form("student_report_form"):
            report_msg = st.text_area("اكتب مشكلتك أو شكواك هنا ليتم إرسالها للإدارة:")
            report_btn = st.form_submit_button("إرسال البلاغ")
            if report_btn:
                if report_msg:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("SELECT name FROM users WHERE phone=?", (user_phone,))
                            u_r = c.fetchone()
                            u_name_val = u_r[0] if u_r else "طالب"
                            
                            t_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("INSERT INTO reports (student_phone, student_name, message, timestamp, status) VALUES (?, ?, ?, ?, 'pending')",
                                      (user_phone, u_name_val, report_msg, t_now_str))
                            conn.commit()
                        st.success("✔️ تم إرسال بلاغك بنجاح وستم مراجعه من قبل الإدارة قريباً!")
                    except Exception as e:
                        st.error(f"خطأ في إرسال البلاغ: {e}")
                else:
                    st.error("يرجى كتابة محتوى البلاغ أو الشكوى!")

    # لوحة تحكم الأستاذ
    elif user_role == "أستاذ":
        st.subheader("👨‍🏫 لوحة تحكم الأستاذ")
        
        t_info = None
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("SELECT name, subject, price, room_id FROM teachers WHERE phone=?", (user_phone,))
                t_info = c.fetchone()
        except:
            pass
            
        if t_info:
            t_name_val, t_sub_val, t_price_val, t_room_val = t_info
            
            with st.expander("⚙️ تعديل بياناتي الشخصية والأسعار"):
                with st.form("update_teacher_profile"):
                    new_t_name = st.text_input("اسم الأستاذ:", value=t_name_val)
                    new_t_sub = st.text_input("المادة الدراسية:", value=t_sub_val)
                    new_t_price = st.number_input("سعر الاشتراك الشهري (جـ):", value=float(t_price_val))
                    upd_prof_btn = st.form_submit_button("حفظ التعديلات")
                    
                    if upd_prof_btn:
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE teachers SET name=?, subject=?, price=? WHERE phone=?", 
                                          (new_t_name, new_t_sub, new_t_price, user_phone))
                                c.execute("UPDATE users SET name=? WHERE phone=?", (new_t_name, user_phone))
                                conn.commit()
                            st.success("✔️ تم تحديث بياناتك بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ أثناء التحديث: {e}")

            st.write("---")
            st.markdown(f"🔴 **غرفة البث المباشر الخاصة بك (Room ID: `{t_room_val}`):**")
            stream_embed_html = f"""
            <iframe src="https://vdo.ninja/?push={t_room_val}&autostart=1" 
                    style="width: 100%; height: 320px; border: 2px solid #4f46e5; border-radius: 12px; background: #000;"
                    allow="camera; microphone; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(stream_embed_html, height=340)
            
            st.write("---")
            render_live_chat(t_room_val, t_name_val)

            st.write("---")
            st.subheader("📤 نشر فيديو أو محتوى تعليمي للطلاب المشتركين")
            with st.form("upload_content_form", clear_on_submit=True):
                p_title = st.text_input("عنوان الفيديو أو المنشور:")
                p_type = st.selectbox("نوع المحتوى:", ["video", "image"])
                uploaded_file = st.file_uploader("اختر الملف (فيديو أو صورة):", type=["mp4", "mov", "avi", "png", "jpg", "jpeg"])
                post_submit_btn = st.form_submit_button("نشر المحتوى")
                
                if post_submit_btn:
                    if p_title and uploaded_file is not None:
                        file_ext = uploaded_file.name.split('.')[-1]
                        unique_filename = f"{user_phone}_{int(datetime.datetime.now().timestamp())}.{file_ext}"
                        file_path = os.path.join(MEDIA_DIR, unique_filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO posts (teacher_phone, title, media_type, file_path, status) VALUES (?, ?, ?, ?, 'approved')",
                                          (user_phone, p_title, p_type, file_path))
                                conn.commit()
                            st.success("✔️ تم رفع ونشر المحتوى بنجاح للطلاب المشتركين!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ أثناء حفظ النشر: {e}")
                    else:
                        st.error("يرجى إدخال العنوان وإرفاق الملف المطلوب!")

            st.write("---")
            st.subheader("👥 طلبات اشتراكات الطلاب والمحفظة المحول منها")
            display_teacher_requests(user_phone)

    # لوحة تحكم المطور الرئيسي
    elif user_role == "مطور":
        st.subheader("👑 لوحة تحكم المطور الرئيسي (التحكم الكامل)")
        
        tab_dev1, tab_dev2, tab_dev3 = st.tabs(["👥 إدارة المستخدمين والأساتذة", "⚠️ البلاغات والشكاوى الواردة", "⚙️ إعدادات النظام"])
        
        with tab_dev1:
            st.markdown("### إدارة حظر وحذف المستخدمين والأساتذة")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT phone, name, role, is_blocked FROM users")
                    all_sys_users = c.fetchall()
                    
                if all_sys_users:
                    for s_ph, s_name, s_role, s_blk in all_sys_users:
                        col_u1, col_u2, col_u3 = st.columns([3, 2, 2])
                        col_u1.write(f"👤 **{s_name}** ({s_role}) - `{s_ph}`")
                        blk_status_str = "محظور 🚫" if s_blk == 1 else "نشط ✅"
                        col_u2.write(f"الحالة: {blk_status_str}")
                        
                        if s_blk == 0:
                            if col_u3.button("🚫 حظر", key=f"blk_user_{s_ph}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET is_blocked=1 WHERE phone=?", (s_ph,))
                                    c.execute("UPDATE teachers SET is_blocked=1 WHERE phone=?", (s_ph,))
                                    conn.commit()
                                st.warning(f"تم حظر المستخدم {s_name}")
                                st.rerun()
                        else:
                            if col_u3.button("✅ إلغاء الحظر", key=f"unblk_user_{s_ph}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET is_blocked=0 WHERE phone=?", (s_ph,))
                                    c.execute("UPDATE teachers SET is_blocked=0 WHERE phone=?", (s_ph,))
                                    conn.commit()
                                st.success(f"تم رفع الحظر عن {s_name}")
                                st.rerun()
                else:
                    st.info("لا يوجد مستخدمين مسجلين بعد.")
            except Exception as e:
                st.error(f"خطأ: {e}")

        with tab_dev2:
            st.markdown("### 📋 البلاغات والشكاوى المقدمة من الطلاب")
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    c = conn.cursor()
                    c.execute("SELECT id, student_phone, student_name, message, timestamp, status FROM reports ORDER BY id DESC")
                    reports = c.fetchall()
                    
                if reports:
                    for r_id, r_phone, r_name, r_msg, r_time, r_status in reports:
                        st.markdown(f"**البلاغ #{r_id}** | الطالب: **{r_name}** (`{r_phone}`) | التاريخ: <small>{r_time}</small>", unsafe_allow_html=True)
                        st.info(r_msg)
                        
                        col_r1, col_r2 = st.columns(2)
                        if r_status != 'resolved':
                            if col_r1.button("✅ تم الحل / معالجة البلاغ", key=f"res_rep_{r_id}"):
                                with sqlite3.connect(DB_NAME) as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE reports SET status='resolved' WHERE id=?", (r_id,))
                                    conn.commit()
                                st.success("تم تحديث حالة البلاغ!")
                                st.rerun()
                        if col_r2.button("🗑️ حذف البلاغ", key=f"del_rep_{r_id}"):
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM reports WHERE id=?", (r_id,))
                                conn.commit()
                            st.warning("تم حذف البلاغ.")
                            st.rerun()
                        st.write("---")
                else:
                    st.info("لا توجد بلاغات أو شكاوى جديدة.")
            except Exception as e:
                st.error(f"خطأ: {e}")

        with tab_dev3:
            st.markdown("### ⚙️ إعدادات النظام العامة")
            with st.form("dev_settings_form"):
                current_teacher_secret = get_setting("teacher_secret", "901000")
                new_t_secret = st.text_input("تعديل الكود السري لإنشاء حسابات الأساتذة:", value=current_teacher_secret)
                save_settings_btn = st.form_submit_button("حفظ الإعدادات")
                
                if save_settings_btn:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            c = conn.cursor()
                            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('teacher_secret', ?)", (new_t_secret,))
                            conn.commit()
                        st.success("✔️ تم حفظ إعدادات النظام بنجاح!")
                    except Exception as e:
                        st.error(f"خطأ: {e}")
