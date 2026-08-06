import streamlit as st
import datetime

# إعدادات صفحة المنصة والشكل الجمالي
st.set_page_config(
    page_title="منصة نوفا التعليمية الذكية",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

# تصميم وتنسيق CSS عصري وملون للواجهة (ألوان جذابة وخلفيات مميزة)
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
    h1, h2, h3 {
        color: #1E3C72;
    }
    </style>
""", unsafe_allow_html=True)

# قاعدة بيانات المدرسين والطلاب
if "teachers" not in st.session_state:
    st.session_state.teachers = {
        "ميس رحمة": {"subject": "لغة إنجليزية وقرآن كريم", "age": 25, "price": 50, "stage": "ثانوي وإعدادي"}
    }

if "students_db" not in st.session_state:
    st.session_state.students_db = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

st.title("🎓 منصة نوفا التعليمية المتطورة")
st.markdown("##### *بوابة التعليم العصرية لجميع المراحل الدراسية (ابتدائي، إعدادي، ثانوي)*")
st.markdown("---")

# ================= شاشة تسجيل الدخول الملونة =================
if not st.session_state.logged_in:
    st.markdown("### 🔐 بوابة الدخول الموحدة")
    
    role_choice = st.selectbox("حدد هويتك في المنصة:", ["طالب", "معلم (مدرس)", "المطور التنفيذي"])
    
    if role_choice == "معلم (مدرس)":
        st.info("💡 ملاحظة: يتطلب دخول المعلمين إدخال الكود السري الخاص بالمنصة.")
        teacher_code = st.text_input("كود المعلم السري:", type="password")
        teacher_email = st.text_input("البريد الإلكتروني للمعلم:")
        teacher_pass = st.text_input("كلمة المرور:", type="password")
        
        if st.button("🚀 تسجيل دخول المعلم"):
            if teacher_code == "90100":
                if teacher_email.strip():
                    st.session_state.logged_in = True
                    st.session_state.user_role = "teacher"
                    st.session_state.current_user = teacher_email
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
                        st.session_state.students_db[student_email] = {"sub_expiry": None, "banned": False}
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

# ================= واجهة المعلم العصرية =================
elif st.session_state.user_role == "teacher":
    st.success(f"مرحباً بك يا استاذنا الفاضل في لوحة التحكم! 👨‍🏫 ({st.session_state.current_user})")
    
    st.markdown("### 📋 بياناتك الشخصية المعروضة للطلاب:")
    t_name = st.text_input("اسمك الكريم (مثال: ميس رحمة):", value="ميس رحمة")
    t_subject = st.text_input("المادة / التخصص:", value="لغة إنجليزية وقرآن كريم")
    t_age = st.number_input("السن:", min_value=20, max_value=80, value=25)
    t_stage = st.selectbox("المرحلة الدراسية:", ["ابتدائي", "إعدادي", "ثانوي", "جميع المراحل"])
    t_price = st.number_input("مصاريف الشهر (جنيه):", value=50)
    
    st.markdown("---")
    st.markdown("### 📢 نشر الحصص والبث المباشر:")
    lesson_title = st.text_input("عنوان الحصة الجديدة:")
    lesson_link = st.text_input("رابط الفيديو أو منصة الشرح:")
    is_live = st.checkbox("🔴 هل هذا بث مباشر؟")
    
    if st.button("نشر المحتوى الآن"):
        if lesson_title and lesson_link:
            st.success("تم نشر الحصة أو البث المباشر بنجاح للطلاب!")
        else:
            st.warning("الرجاء إدخال العنوان والرابط.")
            
    st.markdown("---")
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.rerun()

# ================= واجهة الطالب العصرية والملونة =================
elif st.session_state.user_role == "student":
    student_email = st.session_state.current_user
    
    sub_data = st.session_state.students_db.get(student_email, {})
    expiry_date = sub_data.get("sub_expiry", None)
    is_subscribed = False
    if expiry_date and datetime.datetime.now() < expiry_date:
        is_subscribed = True
        
    st.markdown(f"### أهلاً بك يا بطل! 🎒 (`{student_email}`)")
    
    if is_subscribed:
        st.success("🌟 حسابك مفعل باشتراك شهري كامل وساري على جميع المحاضرات.")
    else:
        st.warning("⚡ ملاحظة: أول 3 حصص مجانية بالكامل، وبث مباشر واحد مجاني للمنهج!")

    st.markdown("---")
    st.markdown("## 👨‍🏫 المدرسون المتاحون في المنصة:")
    
    # عرض المدرسين بداخل مربعات ملونة أنيقة
    for t_n, t_info in st.session_state.teachers.items():
        st.markdown(f"""
            <div class="card-box">
                <h3>📚 الأستاذ(ة): {t_n}</h3>
                <p><b>المادة:</b> {t_info['subject']}</p>
                <p><b>المرحلة:</b> {t_info['stage']} | <b>السن:</b> {t_info['age']} سنة</p>
                <p><b>مصاريف الاشتراك الشهري:</b> {t_info['price']} جنيه فقط</p>
                <p style="color: #27ae60;"><b>✨ مميزات الاشتراك:</b> أول 3 حصص مجاناً + بث مباشر مجاني للمنهج!</p>
            </div>
        """, unsafe_allow_html=True)
        
        # تفاصيل الدفع والاشتراك
        with st.expandarette if hasattr(st, 'expandarette') else st.expander(f"💳 اشترك الآن مع {t_n}"):
            st.write("**تفاصيل الدفع لتحويل الاشتراك الشهري:**")
            st.write("• قيمة الاشتراك: **50 جنيه مصري فقط** لمدة شهر كامل.")
            st.write("• طريقة الدفع: تحويل عبر محفظة **أورنج كاش** على الرقم المخصص: `01213783090`")
            
            pay_phone = st.text_input(f"أدخل رقم هاتفك المحول منه لتفعيل اشتراك {t_n}:", key=f"p_{t_n}")
            if st.button(f"تأكيد الدفع وتفعيل الشهر لـ {t_n}", key=f"b_{t_n}"):
                if pay_phone.strip():
                    st.session_state.students_db[student_email]["sub_expiry"] = datetime.datetime.now() + datetime.timedelta(days=30)
                    st.success("🎉 تم تأكيد الدفع وتفعيل الاشتراك الشهري المفتوح بنجاح!")
                    st.rerun()
                else:
                    st.warning("أدخل رقم الهاتف المحول منه أولاً.")

    st.markdown("---")
    st.markdown("## 🎬 المحاضرات والبث المباشر:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🟢 **الحصة الأولى (مجانية)**")
        if st.button("مشاهدة الحصة 1"):
            st.info("جاري عرض الحصة الأولى المجانية...")
            
        st.markdown("🟢 **الحصة الثانية (مجانية)**")
        if st.button("مشاهدة الحصة 2"):
            st.info("جاري عرض الحصة الثانية المجانية...")
            
    with col2:
        st.markdown("🟢 **الحصة الثالثة (مجانية)**")
        if st.button("مشاهدة الحصة 3"):
            st.info("جاري عرض الحصة الثالثة المجانية...")
            
        st.markdown("🔴 **البث المباشر المجاني (مرة واحدة بالمنهج)**")
        if st.button("دخول البث المباشر"):
            st.warning("⚠️ تنبيه مراقبة صارم: يتم مراقبة التعليقات والشات على مدار 24 ساعة. أي تعليق سلبي أو إساءة يعرض الطالب للحظر الفوري من المنصة!")
            st.success("تم فتح البث المباشر بنجاح.")

    if is_subscribed:
        st.markdown("---")
        st.markdown("### ⭐ المحاضرات المدفوعة الشهرية المفتوحة:")
        if st.button("مشاهدة محتوى الشهر الكامل"):
            st.success("تم فتح كافة الدروس والمراجعات الشهرية المتقدمة بنجاح.")

    st.markdown("---")
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user_role = ""
        st.rerun()
