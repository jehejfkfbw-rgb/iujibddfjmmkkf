import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# ==================== 1. إعدادات الصفحة والتصميم ====================
st.set_page_config(
    page_title="منصة نوفا التعليمية",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تطبيق تنسيقات CSS احترافية (Dark Dashboard Theme)
st.markdown("""
<style>
    /* الاتجاه العام */
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #0e1117;
    }
    
    /* تنسيق الكروت الإحصائية */
    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #60a5fa;
    }
    .metric-label {
        font-size: 14px;
        color: #9ca3af;
    }

    /* كارت المدرس للطلاب */
    .course-card {
        background-color: #1f2937;
        border-radius: 16px;
        border: 1px solid #374151;
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    
    /* الهيدر العلوي */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
    }

    /* تحسين الزر الرئيسي */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 2. تهيئة الذاكرة وقواعد البيانات ====================
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

if "user_info" not in st.session_state:
    st.session_state.user_info = None

if "teachers" not in st.session_state:
    st.session_state.teachers = [
        {
            "id": 1,
            "name": "أحمد محمود",
            "subject": "الفيزياء",
            "price": 150,
            "image": "https://via.placeholder.com/150/3b82f6/ffffff?text=Prof+Ahmed",
            "room_name": "nova_physics_room_1",
            "uploaded_videos": [{"name": "المحاضرة 1: مقدمة في الكهربية", "file": None}]
        },
        {
            "id": 2,
            "name": "سارة الشريف",
            "subject": "الرياضيات",
            "price": 200,
            "image": "https://via.placeholder.com/150/ec4899/ffffff?text=Prof+Sara",
            "room_name": "nova_math_room_2",
            "uploaded_videos": []
        }
    ]

if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = {} # Format: {teacher_id: subscription_date}

# ==================== 3. بوابة تسجيل الدخول الموحدة ====================
if not st.session_state.is_logged_in:
    
    # رأس شاشة الدخول
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center;'>
                <h1 style='color: #60a5fa; font-size: 42px;'>🎓 منصة نوفا</h1>
                <p style='color: #9ca3af;'>بوابتك الموحدة للتعلم الذكي والبث المباشر</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("unified_login_form"):
            st.subheader("🔑 تسجيل الدخول لحسابك")
            email_or_user = st.text_input("اسم المستخدم أو البريد الإلكتروني:")
            password = st.text_input("كلمة السر:", type="password")
            
            submit = st.form_submit_button("دخول المنصة", use_container_width=True)
            
            if submit:
                # منطق الدخول الأمني التلقائي
                if email_or_user.strip() == "admin" and password == "20101999":
                    st.session_state.is_logged_in = True
                    st.session_state.user_info = {"name": "المطور التنفيذي", "role": "المطور التنفيذي 👑", "email": "admin@nova.com"}
                    st.success("تم تسجيل الدخول كـ مطور تنفيذي!")
                    st.rerun()
                elif password == "90100":
                    st.session_state.is_logged_in = True
                    st.session_state.user_info = {"name": email_or_user or "المعلم", "role": "أستاذ 👨‍🏫", "email": email_or_user}
                    st.success("تم تسجيل الدخول كـ معلم!")
                    st.rerun()
                elif email_or_user and password:
                    st.session_state.is_logged_in = True
                    st.session_state.user_info = {"name": email_or_user, "role": "طالب 👨‍🎓", "email": email_or_user}
                    st.success("تم تسجيل الدخول كـ طالب!")
                    st.rerun()
                else:
                    st.error("يرجى إدخال اسم المستخدم وكلمة السر الصحيحة.")

        st.info("💡 **تلميح للدخول:**\n- **طالب:** أي إيميل وكلمة سر.\n- **معلم:** كلمة السر `90100`.\n- **المطور:** اسم المستخدم `admin` وكلمة السر `20101999`.")

# ==================== 4. شاشة لوحة التحكم بعد الدخول ====================
else:
    user = st.session_state.user_info

    # --- القائمة الجانبية (Sidebar) ---
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {user['name']}")
        st.caption(f"المنصب: **{user['role']}**")
        st.markdown("---")
        
        # التنقل الداخلي في اللوحة
        if user["role"] == "طالب 👨‍🎓":
            page = st.radio("القائمة الرئيسية", ["📚 دروسي واشتراكاتي", "🔍 استكشاف المدرسين", "⚙️ الإعدادات"])
        elif user["role"] == "أستاذ 👨‍🏫":
            page = st.radio("لوحة المعلم", ["📊 نظرة عامة", "📤 رفع الحصص المسجلة", "🔴 استوديو البث المباشر"])
        else: # المطور
            page = st.radio("لوحة الإدارة", ["📈 النظرة الشاملة", "👨‍🏫 إدارة الأساتذة", "⚙️ إعدادات النظام"])
            
        st.markdown("---")
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.is_logged_in = False
            st.session_state.user_info = None
            st.rerun()

    # --- الهيدر الرئيسي لكل صفحة ---
    st.markdown(f"""
        <div class="main-header">
            <h2 style="margin:0;">🚀 لوحة تحكم المنصة</h2>
            <p style="margin:0; opacity: 0.8;">مرحباً بك مجدداً {user['name']} | نوع الحساب: {user['role']}</p>
        </div>
    """, unsafe_allow_html=True)

    # ---------------- A. واجهة الطالب ----------------
    if user["role"] == "طالب 👨‍🎓":
        if page in ["📚 دروسي واشتراكاتي", "🔍 استكشاف المدرسين"]:
            st.subheader("👨‍🏫 المدرسون والمواد المتاحة")
            
            cols = st.columns(2)
            for idx, teacher in enumerate(st.session_state.teachers):
                with cols[idx % 2]:
                    st.markdown(f"""
                        <div class="course-card">
                            <h3>👨‍🏫 الأستاذ: {teacher['name']}</h3>
                            <p>📖 <b>المادة:</b> {teacher['subject']} | 💰 <b>الاشتراك:</b> {teacher['price']} جنيه/شهرياً</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    t_id = teacher["id"]
                    is_subbed = t_id in st.session_state.subscriptions
                    
                    if is_subbed:
                        st.success("✅ أنت مشترك في هذه المادة")
                        with st.expander("🎥 عرض الحصص والبث المباشر"):
                            st.write("📌 **الحصص المسجلة:**")
                            if teacher["uploaded_videos"]:
                                for v_idx, vid in enumerate(teacher["uploaded_videos"]):
                                    st.write(f"- حصة {v_idx+1}: {vid['name']}")
                            else:
                                st.caption("لا يوجد فيديوهات مرفوعة حتى الآن.")
                            
                            st.write("🔴 **البث المباشر الحالي:**")
                            jitsi_html = f"""
                            <iframe src="https://meet.jit.si/{teacher['room_name']}#config.prejoinPageEnabled=false" 
                                    style="height: 350px; width: 100%; border: 1px solid #374151; border-radius: 10px;"
                                    allow="camera; microphone; display-capture; autoplay" allowfullscreen>
                            </iframe>
                            """
                            components.html(jitsi_html, height=360)
                    else:
                        if st.button(f"💳 الاشتراك الآن ({teacher['price']} جنيه)", key=f"sub_{t_id}"):
                            st.session_state.subscriptions[t_id] = datetime.now()
                            st.balloons()
                            st.rerun()

        elif page == "⚙️ الإعدادات":
            st.subheader("⚙️ إعدادات الحساب")
            st.text_input("الاسم:", value=user["name"])
            st.text_input("البريد الإلكتروني:", value=user["email"])
            st.button("حفظ التغييرات")

    # ---------------- B. واجهة الأستاذ ----------------
    elif user["role"] == "أستاذ 👨‍🏫":
        # تحديد ملف المدرس الحالي
        curr_teacher = st.session_state.teachers[0] # افتراضياً المدرس الأول
        
        if page == "📊 نظرة عامة":
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{len(st.session_state.subscriptions)}</div><div class="metric-label">إجمالي الطلاب المشتركين</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{len(curr_teacher["uploaded_videos"])}</div><div class="metric-label">الحصص المرفوعة</div></div>', unsafe_allow_html=True)
            with c3:
                revenue = len(st.session_state.subscriptions) * curr_teacher["price"]
                st.markdown(f'<div class="metric-card"><div class="metric-value">{revenue} ج.م</div><div class="metric-label">أرباح الشهر الحالي</div></div>', unsafe_allow_html=True)

        elif page == "📤 رفع الحصص المسجلة":
            st.subheader("📤 إضافة حصة مسجلة جديدة")
            v_title = st.text_input("عنوان الحصة/المحاضرة:")
            u_file = st.file_uploader("اختر فيديو الحصة:", type=["mp4", "mov"])
            if st.button("نشر الحصة للطلاب") and v_title:
                curr_teacher["uploaded_videos"].append({"name": v_title, "file": u_file})
                st.success("تم نشر الحصة بنجاح!")

        elif page == "🔴 استوديو البث المباشر":
            st.subheader("🎙️ استوديو البث المباشر")
            st.info("قم بفتح الكاميرا والمايك للبدء في الشرح المباشر للطلاب المشتركين.")
            jitsi_html = f"""
            <iframe src="https://meet.jit.si/{curr_teacher['room_name']}#config.prejoinPageEnabled=false" 
                    style="height: 500px; width: 100%; border: 0px; border-radius: 10px;"
                    allow="camera; microphone; display-capture; autoplay" allowfullscreen>
            </iframe>
            """
            components.html(jitsi_html, height=520)

    # ---------------- C. واجهة المطور التنفيذي ----------------
    elif user["role"] == "المطور التنفيذي 👑":
        if page == "📈 النظرة الشاملة":
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{len(st.session_state.teachers)}</div><div class="metric-label">إجمالي المعلمين</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{len(st.session_state.subscriptions)}</div><div class="metric-label">الاشتراكات النشطة</div></div>', unsafe_allow_html=True)
            with c3:
                total_rev = sum([t["price"] for t_id in st.session_state.subscriptions for t in st.session_state.teachers if t["id"]==t_id])
                st.markdown(f'<div class="metric-card"><div class="metric-value">{total_rev} ج.م</div><div class="metric-label">إجمالي الدخل المتوقع</div></div>', unsafe_allow_html=True)

        elif page == "👨‍🏫 إدارة الأساتذة":
            st.subheader("➕ إضافة مدرس جديد للمنصة")
            with st.form("add_teacher_form"):
                t_name = st.text_input("اسم المعلم:")
                t_sub = st.text_input("المادة:")
                t_price = st.number_input("سعر الاشتراك (جنيه):", value=150)
                submit_t = st.form_submit_button("إضافة المعلم")
                
                if submit_t and t_name:
                    new_id = len(st.session_state.teachers) + 1
                    st.session_state.teachers.append({
                        "id": new_id,
                        "name": t_name,
                        "subject": t_sub,
                        "price": t_price,
                        "room_name": f"nova_room_{new_id}",
                        "uploaded_videos": []
                    })
                    st.success(f"تمت إضافة الأستاذ {t_name} بنجاح!")
                    st.rerun()

            st.write("---")
            st.subheader("📋 قائمة المعلمين الحاليين")
            for t in st.session_state.teachers:
                st.write(f"- **{t['name']}** ({t['subject']}) - سعر الاشتراك: {t['price']} ج.م | رمز الغرفة: `{t['room_name']}`")

        elif page == "⚙️ إعدادات النظام":
            st.subheader("🔧 خيارات النظام")
            if st.button("🔴 إعادة ضبط المصنع (مسح البيانات المؤقتة)"):
                st.session_state.clear()
                st.rerun()

st.markdown("<br><hr><center style='color:#6b7280;'>🌟 منصة نوفا التعليمية © 2026 - نظام الإدارة الموحد</center>", unsafe_allow_html=True)
