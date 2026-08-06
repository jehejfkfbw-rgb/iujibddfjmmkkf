import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="منصة نوفا التعليمية", page_icon="🌟", layout="wide")

# --- تنسيق اتجاه الصفحة والتصميم العام ---
st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    .teacher-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        background-color: #f9f9f9;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. تهيئة قواعد البيانات المؤقتة (Session State)
if "teachers" not in st.session_state:
    st.session_state.teachers = [
        {
            "id": 1,
            "name": "أحمد محمود",
            "age": 35,
            "subject": "الفيزياء",
            "price": 150,
            "image": "https://via.placeholder.com/150/007bff/ffffff?text=Prof+Ahmed",
            "room_name": "nova_physics_room_1",
            "uploaded_videos": []  # تخزين الفيديوهات بحجم Bytes
        }
    ]

if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = {}

if "current_teacher_id" not in st.session_state:
    st.session_state.current_teacher_id = 1  # الأستاذ الافتراضي المفعّل

if "teacher_authenticated" not in st.session_state:
    st.session_state.teacher_authenticated = False

if "dev_authenticated" not in st.session_state:
    st.session_state.dev_authenticated = False

if "student_authenticated" not in st.session_state:
    st.session_state.student_authenticated = False

# ---------------- الهيدر الرئيسي ----------------
st.title("🌟 منصة نوفا التعليمية")
st.caption("المنصة المترابطة للتعليم الإلكتروني البث المباشر والحصص المسجلة")
st.write("---")

# ---------------- القائمة الجانبية ----------------
with st.sidebar:
    st.header("⚙️ خيارات الدخول")
    role = st.radio("اختر نوع الحساب:", ["طالب 👨‍🎓", "أستاذ 👨‍🏫", "المطور التنفيذي 👑"])
    st.write("---")
    
    # خيار إضافي لإعادة تصفير النظام للتجربة
    if st.button("🔄 إعادة ضبط الجلسة"):
        st.session_state.clear()
        st.rerun()

# ==================== 1. وضع الطالب ====================
if role == "طالب 👨‍🎓":
    st.subheader("👨‍🎓 دخول الطالب")
    
    if not st.session_state.student_authenticated:
        with st.form("student_login_form"):
            st.write("🔑 **تسجيل دخول الطالب:**")
            s_email = st.text_input("البريد الإلكتروني:")
            s_pass = st.text_input("كلمة السر:", type="password")
            s_btn = st.form_submit_button("دخول")
            
            if s_btn:
                if s_email and s_pass:
                    st.session_state.student_authenticated = True
                    st.success("تم تسجيل دخول الطالب بنجاح!")
                    st.rerun()
                else:
                    st.error("يرجى إدخال الإيميل وكلمة السر!")
    else:
        st.sidebar.success("حساب الطالب مفعل ✅")
        if st.sidebar.button("تسجيل الخروج (طالب)"):
            st.session_state.student_authenticated = False
            st.rerun()

        st.subheader("👨‍🏫 قائمة المدرسين والمواد المتاحة")
        
        cols = st.columns(3)
        for index, teacher in enumerate(st.session_state.teachers):
            with cols[index % 3]:
                st.markdown('<div class="teacher-card">', unsafe_allow_html=True)
                st.image(teacher["image"], width=130)
                st.markdown(f"### الأستاذ: **{teacher['name']}**")
                st.markdown(f"👤 **العمر:** {teacher.get('age', 30)} سنة")
                st.markdown(f"📖 **المادة:** {teacher['subject']}")
                st.markdown(f"💰 **الاشتراك:** {teacher['price']} جنيه/شهرياً")
                
                t_id = teacher["id"]
                sub_date = st.session_state.subscriptions.get(t_id, None)
                
                if sub_date:
                    days_passed = (datetime.now() - sub_date).days
                    days_left = 30 - days_passed
                    
                    if days_left > 0:
                        st.success(f"✅ اشتراك نشط (متبقي {days_left} يوم)")
                        st.info("🎁 العرض: مشاهدة كافة الحصص + البث المباشر")
                        
                        st.markdown("---")
                        # عرض الفيديوهات المسجلة التي رفعها الأستاذ
                        st.write("🎥 **الحصص والفيديوهات المسجلة:**")
                        if teacher["uploaded_videos"]:
                            for v_idx, video_data in enumerate(teacher["uploaded_videos"]):
                                st.write(f"📌 **حصة رقم {v_idx + 1}:** {video_data['name']}")
                                st.video(video_data["content"])
                        else:
                            st.caption("لا توجد فيديوهات مسجلة مرفوعة لهذا المدرس بعد.")
                            
                        # البث المباشر
                        st.write("🔴 **البث المباشر الحي:**")
                        room_id = teacher.get("room_name", f"nova_room_{t_id}")
                        jitsi_html = f"""
                        <iframe src="https://meet.jit.si/{room_id}#config.prejoinPageEnabled=false" 
                                style="height: 400px; width: 100%; border: 2px solid #28a745; border-radius: 10px;"
                                allow="camera; microphone; display-capture">
                        </iframe>
                        """
                        components.html(jitsi_html, height=420)
                    else:
                        st.error("⚠️ انتهت فترة الاشتراك 30 يوم!")
                        if st.button(f"تجديد الاشتراك ({teacher['price']} جنيه)", key=f"pay_{t_id}"):
                            st.session_state.subscriptions[t_id] = datetime.now()
                            st.rerun()
                else:
                    st.warning("🔒 المحتوى مغلق. اشترك الآن لرؤية الحصص والبث!")
                    if st.button(f"اشتراك الآن مع {teacher['name']}", key=f"btn_sub_{t_id}"):
                        st.session_state.subscriptions[t_id] = datetime.now()
                        st.balloons()
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

# ==================== 2. وضع الأستاذ ====================
elif role == "أستاذ 👨‍🏫":
    st.subheader("👨‍🏫 لوحة التحكم واستوديو الأستاذ")
    
    if not st.session_state.teacher_authenticated:
        with st.form("teacher_login_form"):
            t_secret = st.text_input("كود السر الخاص بالأساتذة:", type="password")
            t_email = st.text_input("البريد الإلكتروني:")
            t_pass = st.text_input("كلمة السر:", type="password")
            login_btn = st.form_submit_button("تسجيل الدخول كـ أستاذ")
            
            if login_btn:
                # التحقق من كود السر الخاص بالأستاذ: 90100
                if t_secret.strip() == "90100" and t_email and t_pass:
                    st.session_state.teacher_authenticated = True
                    st.success("تم الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("كود السر أو البيانات غير صحيحة! (كود السر المطلوب: 90100)")
    else:
        st.success("🔓 مرحباً بك في استوديو المعلم الخاص بك")
        
        # اختيار الأستاذ المفعل حالياً
        teacher_names = [t["name"] for t in st.session_state.teachers]
        selected_t_name = st.selectbox("اختر ملفك الشخصي لإدارته:", teacher_names)
        
        # الحصول على الأستاذ المختار
        curr_teacher = next(t for t in st.session_state.teachers if t["name"] == selected_t_name)
        
        tab_data, tab_upload, tab_live = st.tabs([
            "📋 بيانات المدرس والمادة", 
            "📤 نشر فيديو/حصة جديدة", 
            "🎙️ غرف البث المباشر"
        ])
        
        # 1. إدخال/تعديل البيانات
        with tab_data:
            st.write("✏️ **إضافة مدرس جديد إلى المنصة:**")
            with st.form("teacher_profile"):
                t_name = st.text_input("اسم الأستاذ الجديد:")
                t_age = st.number_input("العمر:", min_value=20, max_value=80, value=30)
                t_sub = st.text_input("المادة الدراسية:")
                t_price = st.number_input("سعر الاشتراك الشهري (جنيه):", min_value=0, value=150)
                t_img = st.text_input("رابط الصورة الشخصية:", value="https://via.placeholder.com/150/007bff/ffffff?text=Teacher")
                save_btn = st.form_submit_button("حفظ وإضافة الأستاذ")
                
                if save_btn and t_name and t_sub:
                    new_id = len(st.session_state.teachers) + 1
                    room_code = f"nova_room_teacher_{new_id}"
                    st.session_state.teachers.append({
                        "id": new_id,
                        "name": t_name,
                        "age": t_age,
                        "subject": t_sub,
                        "price": t_price,
                        "image": t_img,
                        "room_name": room_code,
                        "uploaded_videos": []
                    })
                    st.success(f"تم تسجيل الأستاذ {t_name} بنجاح!")
                    st.rerun()

        # 2. رفع فيديوهات الحصص من الهاتف
        with tab_upload:
            st.write(f"📤 **رفع فيديو مسجل للأستاذ: ({curr_teacher['name']})**")
            uploaded_file = st.file_uploader("اختر فيديو الحصة من جهازك:", type=["mp4", "mov", "avi"])
            
            if uploaded_file is not None:
                if st.button("نشر الحصة للطلاب"):
                    # حفظ بيانات الفيديو كـ Bytes لضمان استمراريته
                    video_data = {
                        "name": uploaded_file.name,
                        "content": uploaded_file.read()
                    }
                    curr_teacher["uploaded_videos"].append(video_data)
                    st.success(f"تم نشر فيديو '{uploaded_file.name}' بنجاح لطلاب {curr_teacher['name']}!")

        # 3. البث المباشر
        with tab_live:
            st.write(f"🎙️ **استوديو البث المباشر الخاص بـ ({curr_teacher['name']}):**")
            st.info("الكاميرا والميكروفون جاهزان للعمل. شاشة البث المباشر متصلة حالياً بالطلاب المشتركين لديك:")
            
            room_id = curr_teacher["room_name"]
            jitsi_teacher_html = f"""
            <iframe src="https://meet.jit.si/{room_id}#config.prejoinPageEnabled=false" 
                    style="height: 500px; width: 100%; border: 0px; border-radius: 10px;"
                    allow="camera; microphone; display-capture">
            </iframe>
            """
            components.html(jitsi_teacher_html, height=520)

        st.write("---")
        if st.button("تسجيل الخروج كـ أستاذ 🔒"):
            st.session_state.teacher_authenticated = False
            st.rerun()

# ==================== 3. المطور التنفيذي (20101999) ====================
elif role == "المطور التنفيذي 👑":
    st.subheader("👑 لوحة تحكم المطور التنفيذي")
    
    if not st.session_state.dev_authenticated:
        secret_code = st.text_input("أدخل الرقم السري للمطور التنفيذي:", type="password")
        if st.button("دخول لوحة التحكم"):
            if secret_code.strip() == "20101999":
                st.session_state.dev_authenticated = True
                st.success("تم التحقق بنجاح!")
                st.rerun()
            else:
                st.error("الرقم السري غير صحيح!")
    else:
        st.success("🔓 تم فتح صلاحيات المطور التنفيذي")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("إجمالي الأساتذة", len(st.session_state.teachers))
        m2.metric("الاشتراكات النشطة", len(st.session_state.subscriptions))
        
        total_revenue = sum([t["price"] for t_id in st.session_state.subscriptions.keys() for t in st.session_state.teachers if t["id"] == t_id])
        m3.metric("إجمالي الإيرادات المتوقعة", f"{total_revenue} جنيه")

        st.write("---")
        st.write("📋 **قائمة الأساتذة المسجلين بالنظام:**")
        
        for t in st.session_state.teachers:
            with st.expander(f"👨‍🏫 الأستاذ: {t['name']} ({t['subject']})"):
                st.write(f"- **العمر:** {t.get('age', 'غير محدد')}")
                st.write(f"- **سعر الاشتراك:** {t['price']} جنيه")
                st.write(f"- **معرف الغرفة (Jitsi ID):** `{t['room_name']}`")
                st.write(f"- **عدد الفيديوهات المرفوعة:** {len(t['uploaded_videos'])}")
            
        if st.button("خروج المطور التنفيذي 🔒"):
            st.session_state.dev_authenticated = False
            st.rerun()

st.write("---")
st.caption("🌟 منصة نوفا التعليمية © 2026 - جميع الحقوق محفوظة")
