import streamlit as st
import datetime

# إعدادات صفحة المنصة والشكل الجمالي
st.set_page_config(
    page_title="منصة نوفا التعليمية الذكية",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

# تصميم وتنسيق CSS عصري وملون للواجهة
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stButton>button {
        background: linear-gradient(45deg, #FF416C, #FF4B2B);
        color: white;
        font-weight: bold;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #FF4B2B, #FF416C);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    .card-box {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-right: 5px solid #FF416C;
    }
    .ai-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .live-box {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #1E3C72;
    }
    </style>
""", unsafe_allow_html=True)

# قاعدة بيانات المدرسين (تحتوي على بيانات المدرس وحصصه الخاصة به)
if "teachers" not in st.session_state:
    st.session_state.teachers = {}

if "students_db" not in st.session_state:
    st.session_state.students_db = {}

if "live_stream_link" not in st.session_state:
    st.session_state.live_stream_link = ""

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

st.title("🎓 منصة نوفا التعليمية المتطورة")
st.markdown("##### *بوابة التعليم العصرية، البث المباشر والذكاء الاصطناعي*")
st.markdown("---")

# ================= شاشة تسجيل الدخول المرة الواحدة =================
if not st.session_state.logged_in:
    st.markdown("### 🔐 بوابة الدخول الموحدة")
    
    role_choice = st.selectbox("حدد هويتك في المنصة:", ["طالب", "معلم (مدرس)", "المطور التنفيذي"])
    
    if role_choice == "معلم (مدرس)":
        st.info("💡 كود المعلم السري لدخول لوحة التحكم هو: 90100")
        teacher_code = st.text_input("كود المعلم السري:", type="password")
        teacher_email = st.text_input("البريد الإلكتروني للمعلم:")
        teacher_pass = st.text_input("كلمة المرور:", type="password")
        
        if st.button("🚀 تسجيل دخول المعلم"):
            if teacher_code == "90100":
                if teacher_email.strip():
                    st.session_state.logged_in = True
                    st.session_state.user_role = "teacher"
                    st.session_state.current_user = teacher_email
                    # إنشاء بروفایل فارغ للمدرس لو مش موجود
                    if teacher_email not in st.session_state.teachers:
                        st.session_state.teachers[teacher_email] = {
                            "name": "", "subject": "", "age": 25, "stage": "ثانوي", "price": 50, 
                            "image": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=400",
                            "lessons": []
                        }
                    st.success("تم تسجيل الدخول بنجاح! مرحباً بك يا استاذنا.")
                    st.rerun()
                else:
                    st.warning("الرجاء إدخال البريد الإلكتروني.")
            else:
                st.error("❌ كود المعلم خطأ! الكود الصحيح هو 90100")
                
    elif role_choice == "طالب":
        student_email = st.text_input("البريد الإلكتروني للطالب:")
        student_pass = st.text_input("كلمة المرور:", type="password")
        
        if st.button("🚀 دخول الطالب"):
            if student_email.strip() and student_pass.strip():
                if student_email in st.session_state.students_db and st.session_state.students_db[student_email].get("banned", False):
                    st.error("🚫 عذراً، حسابك محظور بسبب مخالفة قواعد التعليقات والمراقبة. تواصل مع المطور لفك الحظر عبر: 01213783090")
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
        dev_email = st.text_input("إيميل المطور:")
        if st.button("دخول المطور"):
            if dev_email == "jehejfkfbw@gmail.com":
                st.session_state.logged_in = True
                st.session_state.user_role = "developer"
                st.session_state.current_user = dev_email
                st.rerun()
            else:
                st.error("إيميل المطور غير صحيح.")

# ================= واجهة المطور التنفيذي =================
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

    st.markdown("---")
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.rerun()

# ================= واجهة المعلم (يكتب بياناته ويضيف حصصه بنفسه) =================
elif st.session_state.user_role == "teacher":
    t_email = st.session_state.current_user
    t_data = st.session_state.teachers[t_email]
    
    st.success(f"مرحباً بك يا استاذنا الفاضل في لوحة التحكم الخاصة بك! 👨‍🏫 ({t_email})")
    
    st.markdown("### 📋 اكتب بياناتك الشخصية واسمك ومادتك بنفسك:")
    t_name = st.text_input("اكتب اسمك الكامل أو لقبك:", value=t_data["name"])
    t_subject = st.text_input("مادتك الدراسية:", value=t_data["subject"])
    t_age = st.number_input("سنك:", min_value=20, max_value=80, value=t_data["age"])
    stages_list = ["ابتدائي", "إعدادي", "ثانوي", "جميع المراحل"]
    default_stage_idx = stages_list.index(t_data["stage"]) if t_data["stage"] in stages_list else 0
    t_stage = st.selectbox("المرحلة الدراسية التي تدرس لها:", stages_list, index=default_stage_idx)
    t_price = st.number_input("مصاريف الاشتراك الشهري (جنيه):", value=t_data["price"])
    t_image = st.text_input("رابط صورتك الشخصية (URL):", value=t_data["image"])
    
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
    st.markdown("### 📚 إضافة حصة جديدة للطلاب:")
    lesson_title = st.text_input("عنوان الحصة (مثال: الحصة الأولى - مقدمة المنهج):")
    lesson_link = st.text_input("رابط فيديو الحصة (يوتيوب أو درايف):")
    
    if st.button("➕ نشر الحصة الجديدة"):
        if lesson_title.strip() and lesson_link.strip():
            st.session_state.teachers[t_email]["lessons"].append({"title": lesson_title, "link": lesson_link})
            st.success(f"تم إضافة الحصة ({lesson_title}) بنجاح لتظهر للطلاب المشتركين معك!")
        else:
            st.warning("الرجاء إدخال عنوان الحصة والرابط.")

    if st.session_state.teachers[t_email]["lessons"]:
        st.markdown("#### حصصك الحالية:")
        for idx, les in enumerate(st.session_state.teachers[t_email]["lessons"], 1):
            st.write(f"{idx}. {les['title']}")

    st.markdown("---")
    st.markdown("### 🔴 إدارة البث المباشر الكامل:")
    new_live_link = st.text_input("رابط البث المباشر (يوتيوب أو زوم):", value=st.session_state.live_stream_link)
    if st.button("📡 بدء/تحديث البث المباشر للطلاب"):
        st.session_state.live_stream_link = new_live_link
        st.success("✅ تم بدء البث المباشر بنجاح!")

    st.markdown("---")
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.rerun()

# ================= واجهة الطالب =================
elif st.session_state.user_role == "student":
    student_email = st.session_state.current_user
    
    sub_data = st.session_state.students_db.get(student_email, {})
    expiry_date = sub_data.get("sub_expiry", None)
    is_subscribed = False
    if expiry_date and datetime.datetime.now() < expiry_date:
        is_subscribed = True
        
    st.markdown(f"### أهلاً بك يا بطل! 🎒 (`{student_email}`)")
    
    if is_subscribed:
        subbed_t = sub_data.get("subscribed_teacher", "غير محدد")
        st.success(f"🌟 حسابك مفعل باشتراك شهري كامل مع الأستاذ(ة): **{subbed_t}**")
    else:
        st.warning("⚡ ملاحظة: اختر المدرس المناسب لك، وتفقد حصصه واشترك معه!")

    st.markdown("---")
    
    # قسم البث المباشر الكامل
    st.markdown("""
        <div class="live-box">
            <h2>🔴 غرفة البث المباشر الكامل للمنصة</h2>
            <p>تابع البث الحصري مع المعلمين مباشرة بجودة عالية مع مراقبة تفاعلية على مدار 24 ساعة!</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.live_stream_link:
        st.success("🎥 البث المباشر جارٍ الآن:")
        st.video(st.session_state.live_stream_link)
        st.warning("⚠️ تنبيه مراقبة صارم: يتم مراقبة الشات والتعليقات على مدار 24 ساعة. أي تعليق سلبي يعرضك للحظر الفوري!")
    else:
        st.info("⏳ لا يوجد بث مباشر مفعل حالياً من المعلمين.")

    st.markdown("---")
    
    # قسم فيديوهات الذكاء الاصطناعي
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
    st.markdown("## 👨‍🏫 المدرسون المتاحون في المنصة (اضغط على المدرس لعرض تفاصيله وحصصه):")
    
    active_teachers = {k: v for k, v in st.session_state.teachers.items() if v["name"].strip() != ""}
    
    if not active_teachers:
        st.info("📌 لا يوجد مدرسون نشروا بياناتهم حتى الآن. انتظر قليلاً لحين تسجيل المعلمين.")
    else:
        for t_email_key, t_info in active_teachers.items():
            t_display_name = t_info['name']
            
            col_img, col_info = st.columns([1, 2])
            with col_img:
                st.image(t_info['image'], caption=f"الأستاذ(ة): {t_display_name}", width=150)
            with col_info:
                st.markdown(f"""
                    <div class="card-box" style="margin-bottom:0px;">
                        <h3>📚 الأستاذ(ة): {t_display_name}</h3>
                        <p><b>المادة:</b> {t_info['subject']}</p>
                        <p><b>المرحلة:</b> {t_info['stage']} | <b>السن:</b> {t_info['age']} سنة</p>
                        <p><b>مصاريف الاشتراك الشهري:</b> {t_info['price']} جنيه فقط</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # قسم الاشتراك وعرض الحصص الخاصة بهذا المدرس فوراً عند الضغط
            with st.expander(f"💳 تفاصيل الاشتراك وعرض حصص الأستاذ(ة) {t_display_name}"):
                st.write(f"• الاشتراك الشهري مع **{t_display_name}**: **{t_info['price']} جنيه مصري فقط** لمدة شهر كامل.")
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
                st.markdown(f"### 🎬 حصص الأستاذ(ة) {t_display_name}:")
                
                if not t_info["lessons"]:
                    st.warning("⚠️ لا يوجد حصص لحد الآن.")
                else:
                    for l_idx, lesson in enumerate(t_info["lessons"], 1):
                        st.markdown(f"🟢 **{l_idx}. {lesson['title']}**")
                        if is_subscribed and sub_data.get("subscribed_teacher") == t_display_name:
                            st.video(lesson['link'])
                        else:
                            st.info("🔒 هذه الحصة تتطلب الاشتراك مع هذا المدرس لمشاهدتها.")

    st.markdown("---")
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.rerun()
