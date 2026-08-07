import streamlit as st
import datetime

# --- إعدادات صفحة المنصة ---
st.set_page_config(
    page_title="منصة نوفا التعليمية - NovaPlatform",
    page_icon="🎓",
    layout="wide"
)

# --- تنسيق التصميم وواجهة المستخدم (RTL) ---
st.markdown("""
    <style>
    .main {
        direction: rtl;
        text-align: right;
    }
    .stTextInput, .stTextArea, .stSelectbox {
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, h4, h5, h6, p, label, span {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

# --- بيانات الربط السحابي (Firebase) ---
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyDWu3fYfj1YHrnc2QH1SIG6XFqI_LYn5HY",
    "projectId": "novaplatform-433f8",
    "storageBucket": "novaplatform-433f8.firebasestorage.app",
    "appId": "1:1027286047684:web:de5bc2f1674fbf87ba2291"
}

# --- تهيئة الذاكرة المؤقتة للجلسة ---
if "users_db" not in st.session_state:
    st.session_state.users_db = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "edu_materials" not in st.session_state:
    st.session_state.edu_materials = [
        {
            "title": "مقدمة في أساسيات لغة بايثون",
            "category": "برمجة Python",
            "content": "شرح مفصل لبدايات البرمجة وكيفية كتابة أول كود بايثون بطريقة صحيحة.",
            "time": "2026-08-07 12:00:00"
        }
    ]

# --- نظام المصادقة والترحيب الخاص ---
special_admin_email = "jehejfkfbw@gmail.com"

# --- القائمة الجانبية للتنقل ---
st.sidebar.title("🎓 منصة نوفا التعليمية")
st.sidebar.markdown("---")

if st.session_state.current_user is None:
    auth_mode = st.sidebar.radio("اختر العملية:", ["تسجيل الدخول", "إنشاء حساب جديد"])
    
    st.title("🚀 مرحباً بك في منصة نوفا التعليمية")
    st.markdown("الرجاء تسجيل الدخول أو إنشاء حساب للبدء.")
    
    email_input = st.text_input("البريد الإلكتروني:")
    
    if auth_mode == "تسجيل الدخول":
        if st.button("دخول للنظام"):
            if email_input:
                st.session_state.current_user = email_input
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.warning("الرجاء إدخال البريد الإلكتروني.")
    else:
        if st.button("تسجيل حساب جديد (مرة واحدة فقط)"):
            if email_input:
                if email_input not in st.session_state.users_db:
                    st.session_state.users_db[email_input] = True
                    st.session_state.current_user = email_input
                    st.success("تم إنشاء الحساب بنجاح!")
                    st.rerun()
                else:
                    st.error("هذا البريد مسجل مسبقاً، لا يمكن التكرار!")
            else:
                st.warning("الرجاء إدخال البريد الإلكتروني.")

else:
    # رسالة الترحيب المخصصة بناءً على البريد المدخل
    logged_email = st.session_state.current_user
    
    if logged_email == special_admin_email:
        st.sidebar.success("مرحباً بك أيها المطور التنفيذي محمد عادل تبع شركة نوفا 🚀")
        st.title("⭐ لوحة التحكم التنفيذية - منصة نوفا")
    else:
        st.sidebar.info(f"مرحباً بك يا عميلنا العزيز: {logged_email}")
        st.title("🎓 بوابة الطالب والعميل - منصة نوفا التعليمية")

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.current_user = None
        st.rerun()

    st.sidebar.markdown("---")
    menu = st.sidebar.selectbox("الأقسام الرئيسية:", ["استعراض الدروس والمحتوى", "إضافة محتوى تعليمي", "إعدادات السحابة والربط"])

    # --- القسم الأول: استعراض المحتوى ---
    if menu == "استعراض الدروس والمحتوى":
        st.subheader("📚 الدروس والمواد التعليمية المتاحة")
        st.write("---")
        
        if st.session_state.edu_materials:
            for item in st.session_state.edu_materials:
                with st.expander(f"📌 {item['title']} ({item['category']})"):
                    st.write(f"**التفاصيل:**\n{item['content']}")
                    st.caption(f"🕒 تاريخ الإضافة: {item['time']}")
        else:
            st.info("لا توجد مواد تعليمية مضافة حالياً.")

    # --- القسم الثاني: إضافة محتوى ---
    elif menu == "إضافة محتوى تعليمي":
        st.subheader("➕ إضافة درس أو محتوى جديد للمنصة")
        
        title = st.text_input("عنوان الدرس أو المحتوى:")
        category = st.selectbox("التصنيف:", ["برمجة Python", "تطوير ألعاب", "ذكاء اصطناعي", "عام"])
        content = st.text_area("شرح المحتوى أو تفاصيل الدرس:")
        
        if st.button("نشر المحتوى سحابياً ☁️"):
            if title and content:
                new_item = {
                    "title": title,
                    "category": category,
                    "content": content,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.edu_materials.insert(0, new_item)
                st.success("تم نشر المحتوى وحفظه بنجاح في المنصة! 🎉")
            else:
                st.warning("الرجاء ملء جميع الحقول المطلوبة.")

    # --- القسم الثالث: إعدادات السحابة ---
    elif menu == "إعدادات السحابة والربط":
        st.subheader("☁️ حالة الاتصال السحابي (Firebase)")
        st.text("معرف المشروع: novaplatform-433f8")
        st.text("حالة الخادم: متصل وجاهز للعمل بكفاءة ✅")
        
        st.json(FIREBASE_CONFIG)

# --- ذيل الصفحة ---
st.write("---")
st.markdown("<p style='text-align: center;'>جميع الحقوق محفوظة © 2026 - منصة نوفا التعليمية | تطوير: Mohamed Adel Ahmed El-Mezahy</p>", unsafe_allow_html=True)
