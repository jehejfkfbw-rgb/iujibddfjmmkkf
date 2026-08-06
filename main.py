import streamlit as st
import datetime
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}]}
)

st.set_page_config(
    page_title="منصة نوفا التعليمية الذكية",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }
    
    .stApp {
        background: #0f172a;
        color: #f1f5f9;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 20px;
    }
    
    .ai-box {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        color: #e0e7ff;
        padding: 20px;
        border-radius: 20px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 20px;
    }
    
    .live-box {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        color: #fee2e2;
        padding: 20px;
        border-radius: 20px;
        border: 1px solid rgba(239, 68, 68, 0.2);
        margin-bottom: 20px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        font-weight: bold;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: 0.3s;
        width: 100%;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        transform: translateY(-2px);
    }
    
    h1, h2, h3 {
        color: #60a5fa !important;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

if "teachers" not in st.session_state:
    st.session_state.teachers = {}

if "students_db" not in st.session_state:
    st.session_state.students_db = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

st.title("🎓 منصة نوفا التعليمية الذكية")
st.markdown("<p style='text-align: center; color: #94a3b8;'>بوابة التعليم العصرية، البث الحي المباشر والذكاء الاصطناعي</p>", unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.markdown("### 📌 إعدادات الحساب")
    if st.session_state.logged_in:
        st.write(f"👤 المستخدم: **{st.session_state.current_user}**")
        st.write(f"🔹 الهوية: **{st.session_state.user_role}**")
        st.markdown("---")
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.user_role = ""
            st.session_state.current_user = ""
            st.success("تم تسجيل الخروج بنجاح!")
            st.rerun()
    else:
        st.info("قم بتسجيل الدخول للبدء.")

if not st.session_state.logged_in:
    st.markdown("### 🔐 بوابة الدخول الموحدة")
    
    role_choice = st.selectbox("حدد هويتك في المنصة:", ["طالب", "معلم (مدرس)", "المطور التنفيذي"])
    
    if role_choice == "معلم (مدرس)":
        teacher_code = st.text_input("كود المعلم السري:", type="password")
        teacher_email = st.text_input("البريد الإلكتروني للمعلم:")
        teacher_pass = st.text_input("كلمة المرور:", type="password")
        
        if st.button("🚀 تسجيل دخول المعلم"):
            if teacher_code == "90100":
                if teacher_email.strip():
                    st.session_state.logged_in = True
                    st.session_state.user_role = "teacher"
                    st.session_state.current_user = teacher_email
                    if teacher_email not in st.session_state.teachers:
                        st.session_state.teachers[teacher_email] = {
                            "name": "", "subject": "", "age": 25, "stage": "ثانوي", "price": 50, "image": None, "lessons": [], "is_live": False
                        }
                    st.success("تم تسجيل الدخول بنجاح! مرحباً بك يا استاذنا.")
                    st.rerun()
                else:
                    st.warning("الرجاء إدخال البريد الإلكتروني.")
            else:
                st.error("❌ كود المعلم خطأ!")
                
    elif role_choice == "طالب":
        student_email = st.text_input("البريد الإلكتروني للطالب:")
        student_pass = st.text_input("كلمة المرور:", type="password", key="s_pass")
        
        if st.button("🚀 دخول الطالب"):
            if student_email.strip() and student_pass.strip():
                if student_email in st.session_state.students_db and st.session_state.students_db[student_email].get("banned", False):
                    st.error("🚫 عذراً، حسابك محظور. تواصل مع المطور عبر: 01213783090")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "student"
                    st.session_state.current_user = student_email
                    if student_email not in st.session_state.students_db:
                        st.session_state.students_db[student_email] = {"sub_expiry": None, "banned": False, "subscribed_teacher": ""}
                    st.rerun()
            else:
                st.warning("الرجاء إدخال البريد الإلكتروني وكلمة المرور.")
                
    elif role_choice == "المطور التنفيذي":
        dev_email = st.text_input("إيميل المطور:", key="dev_inp")
        dev_pass = st.text_input("كلمة مرور المطور:", type="password", key="dev_pass_inp")
        if st.button("دخول المطور"):
            if dev_email == "jehejfkfbw@gmail.com" and dev_pass == "DDEE4DAB":
                st.session_state.logged_in = True
                st.session_state.user_role = "developer"
                st.session_state.current_user = dev_email
                st.rerun()
            else:
                st.error("بيانات دخول المطور غير صحيحة.")

elif st.session_state.user_role == "developer":
    st.success("✨ مرحبا بك ايها المطور التنفيذي محمد عادل تبع شركه نوفا 🌟💼")
    st.info("🛡️ لوحة المراقبة الحية على مدار 24 ساعة للطلاب والمعلمين.")
    
    st.markdown("### 🛠️ إدارة الحظر والتحكم:")
    target_banned_email = st.text_input("أدخل إيميل الطالب لفك الحظر عنه:")
    if st.button("🔓 فك الحظر الفوري"):
        if target_banned_email in st.session_state.students_db:
            st.session_state.students_db[target_banned_email]["banned"] = False
            st.success(f"تم فك الحظر عن الطالب {target_banned_email} بنجاح!")
        else:
            st.warning("الإيميل غير مسجل.")

elif st.session_state.user_role == "teacher":
    t_email = st.session_state.current_user
    if t_email not in st.session_state.teachers:
        st.session_state.teachers[t_email] = {
            "name": "", "subject": "", "age": 25, "stage": "ثانوي", "price": 50, "image": None, "lessons": [], "is_live": False
        }
    t_data = st.session_state.teachers[t_email]
    
    st.success(f"مرحباً بك يا استاذنا الفاضل في لوحة التحكم الخاصة بك! 👨‍🏫 ({t_email})")
    
    st.markdown("### 📋 اكتب بياناتك الشخصية واسمك ومادتك وصورتك الشخصية بنفسك:")
    t_name = st.text_input("اكتب اسمك الكامل أو لقبك:", value=t_data.get("name", ""))
    t_subject = st.text_input("مادتك الدراسية:", value=t_data.get("subject", ""))
    t_age = st.number_input("سنك:", min_value=20, max_value=80, value=t_data.get("age", 25))
    stages_list = ["ابتدائي", "إعدادي", "ثانوي", "جميع المراحل"]
    saved_stage = t_data.get("stage", "ثانوي")
    default_stage_idx = stages_list.index(saved_stage) if saved_stage in stages_list else 0
    t_stage = st.selectbox("المرحلة الدراسية التي تدرس لها:", stages_list, index=default_stage_idx)
    t_price = st.number_input("مصاريف الاشتراك الشهري (جنيه):", value=t_data.get("price", 50))
    
    uploaded_image = st.file_uploader("اختر صورتك الشخصية من صور جهازك:", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        t_image = uploaded_image
        st.image(uploaded_image, caption="معاينة صورتك الشخصية", width=120)
    else:
        t_image = t_data.get("image", None)
    
    if st.button("حفظ ونشر بياناتي للطلاب"):
        if t_name.strip() and t_subject.strip():
            st.session_state.teachers[t_email]["name"] = t_name
            st.session_state.teachers[t_email]["subject"] = t_subject
            st.session_state.teachers[t_email]["age"] = t_age
            st.session_state.teachers[t_email]["stage"] = t_stage
            st.session_state.teachers[t_email]["price"] = t_price
            st.session_state.teachers[t_email]["image"] = t_image
            st.success(f"تم حفظ بياناتك بنجاح يا استاذ {t_name}!")
        else:
            st.warning("الرجاء كتابة الاسم والمادة على الأقل.")

    st.markdown("---")
    st.markdown("### 📚 رفع حصة جديدة مباشرة من استوديو الموبايل أو الجهاز:")
    lesson_title = st.text_input("عنوان الحصة (مثال: شرح الباب الأول):")
    uploaded_video = st.file_uploader("اختر فيديو الشرح من ملفاتك أو صورك:", type=["mp4", "mov", "avi", "mkv"])
    
    if st.button("➕ رفع ونشر الحصة لطلابك"):
        if lesson_title.strip() and uploaded_video is not None:
            st.session_state.teachers[t_email]["lessons"].append({
                "title": lesson_title, 
                "video_file": uploaded_video
            })
            st.success(f"تم رفع الحصة ({lesson_title}) بنجاح لتظهر للطلاب المشتركين معك!")
        else:
            st.warning("الرجاء إدخال عنوان الحصة واختيار ملف الفيديو من جهازك.")

    if st.session_state.teachers[t_email]["lessons"]:
        st.markdown("#### حصصك الحالية المحفوظة:")
        for idx, les in enumerate(st.session_state.teachers[t_email]["lessons"], 1):
            st.write(f"{idx}. {les['title']}")

    st.markdown("---")
    st.markdown("### 🔴 غرفة البث الحي المباشر (WebRTC):")
    st.info("اضغط على زر (START) أدناه لبدء بثك المباشر الحي ومشاركته مع طلابك فوراً:")
    
    webrtc_ctx = webrtc_streamer(
        key=f"teacher_live_{t_email}",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": True},
        async_processing=True,
    )
    
    if webrtc_ctx.state.playing:
        st.session_state.teachers[t_email]["is_live"] = True
        st.success("🟢 الكاميرا تعمل وصوتك وصورتك يظهران في البث الحي الآن!")
    else:
        st.session_state.teachers[t_email]["is_live"] = False

elif st.session_state.user_role == "student":
    student_email = st.session_state.current_user
    
    sub_data = st.session_state.students_db.get(student_email, {})
    expiry_date = sub_data.get("sub_expiry", None)
    is_subscribed = False
    if expiry_date and datetime.datetime.now() < expiry_date:
        is_subscribed = True
        
    st.markdown(f"### أهلاً بك يا بطل! 🎒 (`{student_email}`)")
    
    subbed_t = sub_data.get("subscribed_teacher", "غير محدد")
    if is_subscribed:
        st.success(f"🌟 حسابك مفعل باشتراك شهري كامل مع الأستاذ(ة): **{subbed_t}**")
    else:
        st.warning("⚡ ملاحظة: اختر المدرس المناسب لك، وتفقد حصصه واشترك معه!")

    if is_subscribed:
        teacher_key_found = None
        for tk, tv in st.session_state.teachers.items():
            if tv.get("name") == subbed_t:
                teacher_key_found = tk
                break
        
        if teacher_key_found and st.session_state.teachers[teacher_key_found].get("is_live", False):
            st.markdown(f"""
                <div class="live-box">
                    <h2>🔴 بث مباشر حي الآن مع أستاذك: {subbed_t}</h2>
                    <p>أستاذك يبث الآن مباشرة بالصوت والصورة!</p>
                </div>
            """, unsafe_allow_html=True)
            webrtc_streamer(
                key=f"student_live_{teacher_key_found}",
                mode=WebRtcMode.RECVONLY,
                rtc_configuration=RTC_CONFIGURATION
            )
            st.warning("⚠️ تنبيه مراقبة صارم: يتم مراقبة الشات والتعليقات على مدار 24 ساعة.")

    st.markdown("---")
    
    st.markdown("""
        <div class="ai-box">
            <h3>🤖 قسم فيديوهات الذكاء الاصطناعي في التعليم</h3>
            <p>استمتع بشرح مرئي ومبسط لكيفية توظيف الذكاء الاصطناعي في الدراسة!</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_ai1, col_ai2 = st.columns(2)
    with col_ai1:
        if st.button("🎥 فيديو: الذكاء الاصطناعي والمستقبل التعليمي"):
            st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    with col_ai2:
        if st.button("🎥 فيديو: كيف تستخدم الأدوات الذكية في المذاكرة"):
            st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    st.markdown("---")
    st.markdown("## 👨‍شاهِد المدرسين المتاحين واشترك معهم:")
    
    active_teachers = {}
    for k, v in st.session_state.teachers.items():
        if isinstance(v, dict) and v.get("name", "").strip() != "":
            active_teachers[k] = v
    
    if not active_teachers:
        st.info("📌 لا يوجد مدرسون نشروا بياناتهم حتى الآن. انتظر قليلاً لحين تسجيل المعلمين.")
    else:
        for t_email_key, t_info in active_teachers.items():
            t_display_name = t_info.get('name', 'معلم')
            t_img = t_info.get('image', None)
            
            col_img, col_info = st.columns([1, 2])
            with col_img:
                if t_img is not None:
                    st.image(t_img, caption=f"الأستاذ(ة): {t_display_name}", width=130)
                else:
                    st.image("https://images.unsplash.com/photo-1544717305-2782549b5136?w=400", caption=f"الأستاذ(ة): {t_display_name}", width=130)
            with col_info:
                st.markdown(f"""
                    <div class="glass-card" style="margin-bottom:0px;">
                        <h3>📚 الأستاذ(ة): {t_display_name}</h3>
                        <p><b>المادة:</b> {t_info.get('subject', 'غير محدد')}</p>
                        <p><b>المرحلة:</b> {t_info.get('stage', 'ثانوي')} | <b>السن:</b> {t_info.get('age', 25)} سنة</p>
                        <p><b>مصاريف الاشتراك الشهري:</b> {t_info.get('price', 50)} جنيه فقط</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with st.expander(f"💳 تفاصيل الاشتراك وعرض حصص وبث الأستاذ(ة) {t_display_name}"):
                st.write(f"• الاشتراك الشهري مع **{t_display_name}**: **{t_info.get('price', 50)} جنيه مصري فقط** لمدة شهر كامل.")
                st.write("• طريقة الدفع: تحويل عبر محفظة **أورنج كاش** على الرقم المخصص: `01213783090`")
                
                pay_phone = st.text_input(f"أدخل رقم هاتفك المحول منه لتفعيل اشتراك {t_display_name}:", key=f"p_{t_email_key}")
                if st.button(f"تأكيد الدفع وتفعيل اشتراك {t_display_name}", key=f"b_{t_email_key}"):
                    if pay_phone.strip():
                        st.session_state.students_db[student_email]["sub_expiry"] = datetime.datetime.now() + datetime.timedelta(days=30)
                        st.session_state.students_db[student_email]["subscribed_teacher"] = t_display_name
                        st.success(f"🎉 تم تأكيد الدفع بنجاح! أنت الآن مشترك رسمياً مع الأستاذ(ة) {t_display_name}")
                        st.rerun()
                    else:
                        st.warning("أدخل رقم الهاتف المحول منه أولاً.")
                
                st.markdown("---")
                
                if is_subscribed and sub_data.get("subscribed_teacher") == t_display_name:
                    if t_info.get("is_live", False):
                        st.markdown(f"### 🔴 البث الحي المباشر للأستاذ {t_display_name}:")
                        webrtc_streamer(
                            key=f"student_view_{t_email_key}",
                            mode=WebRtcMode.RECVONLY,
                            rtc_configuration=RTC_CONFIGURATION
                        )
                    else:
                        st.info("⏳ الأستاذ لم يبدأ البث الحي بالكاميرا حتى الآن.")
                
                st.markdown(f"### 🎬 حصص الأستاذ(ة) {t_display_name}:")
                lessons_list = t_info.get("lessons", [])
                if not lessons_list:
                    st.warning("⚠️ لا يوجد حصص لحد الآن مع هذا المدرس.")
                else:
                    for l_idx, lesson in enumerate(lessons_list, 1):
                        st.markdown(f"🟢 **{l_idx}. {lesson.get('title', 'حصة')}**")
                        if is_subscribed and sub_data.get("subscribed_teacher") == t_display_name:
                            st.video(lesson.get('video_file'))
                        else:
                            st.info("🔒 هذه الحصة تتطلب الاشتراك مع هذا المدرس لمشاهدتها.")
