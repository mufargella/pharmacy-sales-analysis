import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ضبط إعدادات الصفحة لتكون عريضة وذات مظهر عصري
st.set_page_config(
    page_title="لوحة تحكم تحليلات المبيعات الذكية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# دعم اللغة العربية في الرسومات
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# تنسيقات CSS مخصصة لإضفاء مظهر بريميوم وعصري (Dark/Modern Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 5px;
        padding-bottom: 10px;
        border-bottom: 2px solid #E2E8F0;
    }
    
    .sub-title {
        font-size: 1.1rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #E2E8F0;
        text-align: center;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2563EB;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 0.95rem;
        color: #64748B;
        font-weight: 600;
    }
    
    .tab-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    
    /* استعلامات الوسائط لتحسين المظهر على الموبايل */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.7rem;
            padding-bottom: 5px;
        }
        .sub-title {
            font-size: 0.9rem;
            margin-bottom: 15px;
        }
        .metric-card {
            padding: 12px;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 1.3rem;
        }
        .metric-label {
            font-size: 0.8rem;
        }
        .tab-header {
            font-size: 1.1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# دالة تحميل البيانات
# ----------------------------------------------------
@st.cache_data
def load_data():
    # تحميل جدول الحقائق والأبعاد
    fact_sales = pd.read_csv('fact_sales.csv')
    dim_products = pd.read_csv('dim_products.csv')
    dim_customers = pd.read_csv('dim_customers.csv')
    dim_employees = pd.read_csv('dim_employees.csv')
    dim_suppliers = pd.read_csv('dim_suppliers.csv')
    dim_geography = pd.read_csv('dim_geography.csv')
    
    # تحميل البيانات الخام للمقارنة
    raw_df = pd.read_csv('supplier_sales_2026-06-04_222403.csv')
    
    # تحميل العمليات الشاذة
    if os.path.exists('detected_anomalies.csv'):
        anomalies = pd.read_csv('detected_anomalies.csv')
    else:
        anomalies = pd.DataFrame()
        
    return fact_sales, dim_products, dim_customers, dim_employees, dim_suppliers, dim_geography, raw_df, anomalies

try:
    fact_sales, dim_products, dim_customers, dim_employees, dim_suppliers, dim_geography, raw_df, anomalies = load_data()
except Exception as e:
    st.error("عذراً، حدث خطأ أثناء تحميل ملفات البيانات الموحدة. تأكد من تشغيل النوت بوك أولاً لتوليد الملفات.")
    st.stop()

# دمج البيانات للعرض والتحليل
# نقوم بإسقاط أعمدة الجغرافيا المكررة من جدول العملاء لتفادي تضارب الأسماء عند الدمج مع dim_geography
df_merged = fact_sales.merge(dim_products, on='global_prod_id')
df_merged = df_merged.merge(dim_customers.drop(columns=['area', 'city', 'region'], errors='ignore'), on='global_account_id')
df_merged = df_merged.merge(dim_employees, on='global_employee_id')
df_merged = df_merged.merge(dim_geography, on='geography_id')

# ----------------------------------------------------
# واجهة المستخدم الرئيسية
# ----------------------------------------------------
st.markdown("<div class='main-title'>لوحة تحكم تحليلات المبيعات الذكية</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>نظام هندسة وتنظيف وتحليل بيانات المبيعات متعددة المستودعات</div>", unsafe_allow_html=True)

# شريط جانبي للتصفية
st.sidebar.header("📊 خيارات التصفية")
supplier_list = ["الكل"] + sorted(list(dim_suppliers['supplier_name'].unique()))
selected_supplier = st.sidebar.selectbox("اختر المورد", supplier_list)

city_list = ["الكل"] + sorted(list(dim_geography['city'].unique()))
selected_city = st.sidebar.selectbox("اختر المدينة", city_list)

# تصفية البيانات بناء على الاختيارات
filtered_df = df_merged.copy()
if selected_supplier != "الكل":
    supp_id = dim_suppliers[dim_suppliers['supplier_name'] == selected_supplier]['supplier_id'].values[0]
    filtered_df = filtered_df[filtered_df['supplier_id'] == supp_id]
if selected_city != "الكل":
    filtered_df = filtered_df[filtered_df['city'] == selected_city]

# ----------------------------------------------------
# الكروت الإحصائية الرئيسية (KPIs)
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_revenue = filtered_df['total_amount'].sum()
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{total_revenue:,.2f} ج.م</div>
        <div class='metric-label'>إجمالي الإيرادات</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_sales_count = len(filtered_df)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{total_sales_count:,}</div>
        <div class='metric-label'>إجمالي الحركات (العمليات)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    active_customers = filtered_df['global_account_id'].nunique()
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{active_customers}</div>
        <div class='metric-label'>عدد الصيدليات الموحدة النشطة</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    active_products = filtered_df['global_prod_id'].nunique()
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{active_products}</div>
        <div class='metric-label'>عدد المنتجات الموحدة النشطة</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------
# تبويبات لوحة التحكم
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📈 نظرة عامة وتحليلات", "🔄 مقارنة قبل/بعد التنظيف", "🤖 الذكاء الاصطناعي والتنبؤ", "📢 أتمتة تليجرام"])

# ----------------------------------------------------
# التبويب الأول: نظرة عامة وتحليلات
# ----------------------------------------------------
with tab1:
    st.markdown("<div class='tab-header'>تحليلات المبيعات المفصلة</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("أعلى 10 منتجات مبيعاً من حيث الإيرادات")
        top_products = filtered_df.groupby('product_name')['total_amount'].sum().sort_values(ascending=False).head(10)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=top_products.values, y=top_products.index, ax=ax, palette='Blues_r')
        ax.set_xlabel("الإيرادات (جنيه)")
        ax.set_ylabel("")
        st.pyplot(fig)
        
    with c2:
        st.subheader("أعلى 10 صيدليات شراءً")
        top_customers = filtered_df.groupby('account_name')['total_amount'].sum().sort_values(ascending=False).head(10)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=top_customers.values, y=top_customers.index, ax=ax, palette='Purples_r')
        ax.set_xlabel("المشتريات (جنيه)")
        ax.set_ylabel("")
        st.pyplot(fig)

    st.markdown("<hr>", unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    
    with c3:
        st.subheader("المبيعات حسب المنطقة الجغرافية")
        sales_by_area = filtered_df.groupby('area')['total_amount'].sum().sort_values(ascending=False).head(8)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.pie(sales_by_area.values, labels=sales_by_area.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette('pastel'))
        ax.axis('equal')
        st.pyplot(fig)
        
    with c4:
        st.subheader("أداء مناديب المبيعات (أعلى 8 مناديب)")
        sales_by_emp = filtered_df.groupby('employee_name')['total_amount'].sum().sort_values(ascending=False).head(8)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=sales_by_emp.values, y=sales_by_emp.index, ax=ax, palette='Greens_r')
        ax.set_xlabel("مبيعات المندوب (جنيه)")
        ax.set_ylabel("")
        st.pyplot(fig)

# ----------------------------------------------------
# التبويب الثاني: مقارنة قبل/بعد التنظيف
# ----------------------------------------------------
with tab2:
    st.markdown("<div class='tab-header'>مقارنة وتحليل تأثير تنظيف وتوحيد البيانات</div>", unsafe_allow_html=True)
    
    # بطاقات تلخص الفروقات الأساسية
    mc1, mc2, mc3 = st.columns(3)
    
    with mc1:
        orig_cust = raw_df['account_name'].nunique()
        clean_cust = dim_customers.shape[0]
        merged_cust = orig_cust - clean_cust
        st.metric(
            label="عدد الصيدليات الفريدة (تخفيض التكرار)", 
            value=f"{clean_cust} صيدلية", 
            delta=f"-{merged_cust} اسم متكرر"
        )
        
    with mc2:
        orig_prod = raw_df['product_name'].nunique()
        clean_prod = dim_products.shape[0]
        merged_prod = orig_prod - clean_prod
        st.metric(
            label="عدد المنتجات الفريدة (تخفيض التكرار)", 
            value=f"{clean_prod} منتج", 
            delta=f"-{merged_prod} اسم متكرر"
        )
        
    with mc3:
        orig_emp = raw_df['employee_name'].dropna().nunique()
        clean_emp = dim_employees.shape[0] - 1  # باستثناء 'غير محدد'
        merged_emp = orig_emp - clean_emp
        st.metric(
            label="عدد مناديب المبيعات (تخفيض التكرار)", 
            value=f"{clean_emp} مندوب", 
            delta=f"-{merged_emp} اسم متكرر"
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # عرض رسم المقارنة بين المنتجات
    if os.path.exists('cleaning_impact_comparison.png'):
        st.subheader("رسم بياني: تأثير توحيد مسميات المنتجات على تقارير المبيعات")
        st.image('cleaning_impact_comparison.png', caption='مقارنة أعلى 10 منتجات مبيعاً قبل وبعد التنظيف', use_column_width=True)
    else:
        st.info("الرسم التوضيحي للمقارنة لم يتم توليده بعد.")

# ----------------------------------------------------
# التبويب الثالث: الذكاء الاصطناعي والتنبؤ
# ----------------------------------------------------
with tab3:
    st.markdown("<div class='tab-header'>التنبؤ المستقبلي واكتشاف العمليات غير الطبيعية بالذكاء الاصطناعي</div>", unsafe_allow_html=True)
    
    c_ml1, c_ml2 = st.columns([3, 2])
    
    with c_ml1:
        st.subheader("1. التنبؤ بالمبيعات اليومية لآخر 30 يوماً")
        if os.path.exists('sales_forecast_plot.png'):
            st.image('sales_forecast_plot.png', caption='الخط المتقطع يمثل التوقعات والخط المتصل يمثل المبيعات الفعلية', use_column_width=True)
        else:
            st.info("رسم التنبؤ بالمبيعات غير متوفر.")
            
    with c_ml2:
        st.subheader("2. معلومات التنبؤ بالطلب")
        st.markdown("""
        * **نموذج التنبؤ بالطلب (Demand Forecasting):**
          تم تدريب نموذج RandomForest بنجاح للتنبؤ بالكميات اليومية المطلوبة من المنتج الأكثر مبيعاً **(ميراج 1جم حقن)**.
        * **الخصائص المستخدمة للتنبؤ:**
          * اليوم من الأسبوع (Day of Week)
          * الشهر الحالي (Month)
          * كمية المبيعات لليوم السابق (Lag 1)
          * كمية المبيعات لنفس اليوم من الأسبوع السابق (Lag 7)
        """)
        
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.subheader("3. كشف العمليات الشاذة (Detected Anomalies)")
    st.markdown("باستخدام نموذج **Isolation Forest** تم كشف الصفقات ذات الخصومات أو القيم الشاذة:")
    
    if not anomalies.empty:
        # عرض جدول العمليات الشاذة
        anomalies_display = anomalies[['clean_account_name', 'clean_product_name', 'quantity', 'discount', 'total_amount', 'creation_date']].copy()
        anomalies_display.columns = ['اسم الصيدلية الموحد', 'اسم المنتج الموحد', 'الكمية المباعة', 'الخصم (%)', 'إجمالي المبلغ', 'تاريخ المعاملة']
        st.dataframe(anomalies_display, use_container_width=True)
    else:
        st.info("لا توجد عمليات شاذة مكتشفة أو ملف detected_anomalies.csv غير موجود.")

# ----------------------------------------------------
# التبويب الرابع: أتمتة تليجرام
# ----------------------------------------------------
with tab4:
    st.markdown("<div class='tab-header'>أتمتة وإرسال التقارير التلقائية عبر تليجرام</div>", unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([2, 3])
    
    with col_t1:
        st.subheader("⚙️ إعدادات البوت والاتصال")
        st.markdown("""
        لربط النظام بهاتفك أو مجموعة العمل وتلقي التقارير الفورية:
        1. ابحث عن البوت **@BotFather** على تليجرام وأرسل له `/newbot` لإنشاء بوت جديد والحصول على الـ **Bot Token**.
        2. ابحث عن البوت **@userinfobot** أو **@GetChatID_Bot** لمعرفة الـ **Chat ID** الخاص بك أو بمجموعتك.
        """)
        
        # حقول إدخال سرية
        bot_token_input = st.text_input("رمز البوت (Telegram Bot Token)", type="password", help="مثال: 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
        chat_id_input = st.text_input("معرف المحادثة (Telegram Chat ID)", type="default", help="مثال: 987654321 أو معرف المجموعة -100123456789")
        
        # زر الإرسال
        send_report_btn = st.button("🚀 إرسال تقرير اختبار الآن إلى تليجرام")
        
    with col_t2:
        st.subheader("📝 معاينة التقرير المرسل (Preview)")
        
        # توليد نص التقرير
        def total_revenue_format_dashboard(val):
            if val >= 1_000_000:
                return f"{val/1_000_000:.2f}M"
            elif val >= 1_000:
                return f"{val/1_000:.2f}K"
            return f"{val:.2f}"
            
        total_sales = filtered_df['total_amount'].sum()
        transaction_count = len(filtered_df)
        
        if not filtered_df.empty:
            top_region_idx = filtered_df.groupby('region')['total_amount'].sum().idxmax()
            top_region_sales_val = filtered_df.groupby('region')['total_amount'].sum().max()
            top_employee_idx = filtered_df.groupby('employee_name')['total_amount'].sum().idxmax()
            top_employee_sales_val = filtered_df.groupby('employee_name')['total_amount'].sum().max()
        else:
            top_region_idx, top_region_sales_val = "غير محدد", 0
            top_employee_idx, top_employee_sales_val = "غير محدد", 0

        anomalies_msg = ""
        if not anomalies.empty:
            anomalies_msg = "\n🚨 *تنبيهات العمليات الشاذة الأخيرة (Top Alerts):*\n"
            latest_anomalies = anomalies.tail(3)
            for idx, row in latest_anomalies.iterrows():
                anomalies_msg += f"- صيدلية: `{row['clean_account_name']}` | منتج: `{row['clean_product_name']}` | المبلغ: `{row['total_amount']:.2f} ج.م` | خصم: `{row['discount']}%`\n"
        else:
            anomalies_msg = "\n✅ لا توجد عمليات شاذة مكتشفة مؤخراً."

        from datetime import datetime
        report_text = f"""
📊 *تقرير مبيعات الأدوية الموحد (من لوحة التحكم)* 📊
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
------------------------------------------
💰 *إجمالي المبيعات:* `{total_revenue_format_dashboard(total_sales)}` ج.م
📈 *عدد العمليات:* `{transaction_count:,}` حركة مبيعات

🌍 *أعلى منطقة مبيعاً:* `{top_region_idx}`
💵 (مبيعات المنطقة: `{total_revenue_format_dashboard(top_region_sales_val)}` ج.م)

👤 *أفضل مندوب مبيعات:* `{top_employee_idx}`
💵 (مبيعات المندوب: `{total_revenue_format_dashboard(top_employee_sales_val)}` ج.م)
------------------------------------------
{anomalies_msg}
        """
        
        st.code(report_text, language="markdown")
        
        if send_report_btn:
            if not bot_token_input or not chat_id_input:
                st.error("⚠️ يرجى إدخال كل من الـ Token والـ Chat ID للتمكن من إرسال التقرير.")
            else:
                with st.spinner("جاري إرسال التقرير لتليجرام..."):
                    import requests
                    url = f"https://api.telegram.org/bot{bot_token_input}/sendMessage"
                    payload = {
                        "chat_id": chat_id_input,
                        "text": report_text,
                        "parse_mode": "Markdown"
                    }
                    try:
                        res = requests.post(url, json=payload, timeout=10)
                        res_json = res.json()
                        if res_json.get("ok"):
                            st.success("✅ تم إرسال التقرير التجريبي إلى هاتفك تليجرام بنجاح!")
                        else:
                            st.error(f"❌ فشل الإرسال. استجابة تليجرام: {res_json.get('description')}")
                    except Exception as ex:
                        st.error(f"❌ حدث خطأ أثناء الاتصال بتليجرام: {ex}")

