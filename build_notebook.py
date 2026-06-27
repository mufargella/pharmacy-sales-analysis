import nbformat as nbf

# Create new notebook
nb = nbf.v4.new_notebook()
cells = []

# ==========================================
# Phase 1: Exploration
# ==========================================
cells.append(nbf.v4.new_markdown_cell("""# مشروع هندسة وتحليل بيانات المبيعات (Sales Data Engineering & Analytics)

يهدف هذا الدفتر إلى معالجة وتنظيف بيانات المبيعات غير المتناسقة المجمعة من مستودعات ومخازن متعددة، وتوحيد أسماء الصيدليات والمنتجات ومناديب المبيعات، ثم نمذجتها وتحليلها واستخدام التعلم الآلي للتنبؤ واكتشاف العمليات الشاذة.

## المرحلة 1: إعداد البيئة واستكشاف البيانات (Data Exploration & Setup)
في هذه المرحلة سنقوم بـ:
1. استيراد المكتبات الأساسية.
2. تحميل ملف البيانات `supplier_sales_2026-06-04_222403.csv`.
3. استكشاف الأعمدة ونسبة القيم المفقودة (Nulls).
4. استكشاف التكرار والتناقض في المسميات للمنتجات والصيدليات والمناديب."""))

cells.append(nbf.v4.new_code_cell("""import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from rapidfuzz import process, fuzz
import re

# إعداد لغة العرض في المخططات لدعم اللغة العربية
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# تحميل البيانات
df = pd.read_csv('supplier_sales_2026-06-04_222403.csv')
print(f"تم تحميل البيانات بنجاح. أبعاد الجدول: {df.shape}")
df.head()"""))

cells.append(nbf.v4.new_code_cell("""# استكشاف القيم المفقودة ونسبة اكتمال البيانات
print("--- القيم المفقودة في كل عمود ---")
missing_info = pd.DataFrame({
    'القيم المفقودة': df.isnull().sum(),
    'النسبة المئوية (%)': (df.isnull().sum() / len(df)) * 100
})
print(missing_info)

# استكشاف عدد القيم الفريدة في الأعمدة الأساسية
print("\\n--- عدد القيم الفريدة في الأعمدة الأساسية ---")
cols_to_check = ['supplier_id', 'prod_id', 'product_name', 'account_id', 'account_name', 'employee_name', 'city', 'region', 'area']
for col in cols_to_check:
    print(f"{col}: {df[col].nunique()} قيمة فريدة")"""))

cells.append(nbf.v4.new_code_cell("""# إثبات أن معرف المنتج ومعرف الحساب (الصيدلية) ليسا معرفين عامين (Global Keys)
print("--- إثبات عدم توحيد المعرفات (prod_id & account_id) بين الموردين ---")

# 1. فحص المنتجات التي لها نفس prod_id ولكن بأسماء مختلفة تماماً بين الموردين
prod_names_per_id = df.groupby('prod_id')['product_name'].nunique()
ids_with_multiple_names = prod_names_per_id[prod_names_per_id > 1].index
print(f"عدد معرفات المنتجات (prod_id) التي ترتبط بأكثر من اسم منتج: {len(ids_with_multiple_names)}")

print("\\nأمثلة لمعرفات منتجات ترتبط بمنتجات مختلفة تماماً:")
for pid in ids_with_multiple_names[:5]:
    names = df[df['prod_id'] == pid]['product_name'].unique()
    print(f"prod_id = {pid} مرتبط بالأسماء التالية: {list(names)}")

# 2. فحص الصيدليات التي لها نفس account_id ولكن بأسماء مختلفة تماماً بين الموردين
acc_names_per_id = df.groupby('account_id')['account_name'].nunique()
acc_ids_with_multiple_names = acc_names_per_id[acc_names_per_id > 1].index
print(f"\\nعدد معرفات الحسابات (account_id) التي ترتبط بأكثر من اسم صيدلية: {len(acc_ids_with_multiple_names)}")

print("\\nأمثلة لمعرفات حسابات ترتبط بصيدليات مختلفة تماماً:")
for aid in acc_ids_with_multiple_names[:5]:
    names = df[df['account_id'] == aid]['account_name'].unique()
    print(f"account_id = {aid} مرتبط بالأسماء التالية: {list(names)}")"""))

# ==========================================
# Phase 2: Cleaning & Unification
# ==========================================
cells.append(nbf.v4.new_markdown_cell("""## المرحلة 2: تنظيف البيانات وتوحيد الكيانات (Data Cleaning & Entity Resolution)

في هذا الجزء سنقوم بـ:
1. كتابة دوال برمجية لتنظيف النصوص العربية (إزالة الرموز الخاصة، وتوحيد رسم الحروف مثل الياء والهاء والألف).
2. استخدام خوارزميات المطابقة التقريبية (Fuzzy Matching) لتوحيد أسماء مناديب المبيعات والصيدليات والمنتجات المتشابهة.
3. استخراج معلومات الجغرافيا (المدن والمناطق) من العنوان أو اسم الصيدلية وتعبئتها في الجدول بدلاً من كونها فارغة."""))

cells.append(nbf.v4.new_code_cell("""def clean_arabic_text(text):
    if not isinstance(text, str):
        return ""
    
    # تحويل النص للحروف الصغيرة وإزالة أي مسافات زائدة
    text = text.strip().lower()
    
    # توحيد رسم الهمزات والألف
    text = re.sub(r'[أإآا]', 'ا', text)
    
    # توحيد التاء المربوطة والهاء في النهاية
    text = re.sub(r'ة\\b', 'ه', text)
    
    # توحيد الياء والالف المقصورة في النهاية
    text = re.sub(r'[ىي]\\b', 'ي', text)
    
    # إزالة الرموز الخاصة والتنقيط والمسافات الزائدة
    text = re.sub(r'[^\\w\\s\\u0600-\\u06FF]', ' ', text)
    text = re.sub(r'\\s+', ' ', text).strip()
    
    return text

# تجربة دالة التنظيف على عينة
test_names = [
    "ص مها مديرية امن الجيزة &ش*& 003",
    "ص السعدنى فيصل 002",
    "ص السعدني فيصل 002",
    "نهى الدالى",
    "نهي الدالي",
    "نهى الدالى "
]
print("--- تجربة دالة تنظيف النصوص ---")
for name in test_names:
    print(f"الاسم الأصلي: '{name}' -> الاسم بعد التنظيف: '{clean_arabic_text(name)}'")"""))

cells.append(nbf.v4.new_code_cell("""def build_mapping_dict(unique_names, threshold=85):
    cleaned_to_original = {}
    cleaned_names = []
    
    for name in unique_names:
        if pd.isna(name):
            continue
        cleaned = clean_arabic_text(name)
        if cleaned:
            cleaned_to_original[cleaned] = cleaned_to_original.get(cleaned, []) + [name]
            if cleaned not in cleaned_names:
                cleaned_names.append(cleaned)
                
    mapping = {}
    visited = set()
    cleaned_names.sort(key=len, reverse=True)
    
    for name in cleaned_names:
        if name in visited:
            continue
            
        matches = process.extract(name, cleaned_names, scorer=fuzz.token_sort_ratio, score_cutoff=threshold)
        group = [m[0] for m in matches if m[0] not in visited]
        if not group:
            continue
            
        standard_name = min(group, key=len)
        for item in group:
            mapping[item] = standard_name
            visited.add(item)
            
    final_mapping = {}
    for cleaned_name, original_list in cleaned_to_original.items():
        standard = mapping.get(cleaned_name, cleaned_name)
        standard_readable = cleaned_to_original[standard][0]
        for orig in original_list:
            final_mapping[orig] = standard_readable
            
    return final_mapping

# فحص مناديب المبيعات
unique_employees = df['employee_name'].dropna().unique()
emp_mapping = build_mapping_dict(unique_employees, threshold=80)
print(f"عدد مناديب المبيعات الأصلي: {len(unique_employees)}")
print(f"عدد مناديب المبيعات بعد التوحيد: {len(set(emp_mapping.values()))}")"""))

cells.append(nbf.v4.new_code_cell("""# 1. توحيد أسماء المنتجات
unique_products = df['product_name'].dropna().unique()
product_mapping = build_mapping_dict(unique_products, threshold=85)
print(f"عدد المنتجات الأصلي: {len(unique_products)}")
print(f"عدد المنتجات بعد التوحيد: {len(set(product_mapping.values()))}")

# 2. توحيد أسماء الصيدليات
unique_accounts = df['account_name'].dropna().unique()
account_mapping = build_mapping_dict(unique_accounts, threshold=85)
print(f"\\nعدد الصيدليات الأصلي: {len(unique_accounts)}")
print(f"عدد الصيدليات بعد التوحيد: {len(set(account_mapping.values()))}")"""))

cells.append(nbf.v4.new_code_cell("""# استخراج الجغرافيا مع قائمة كلمات مفتاحية محسنة وموسعة لتغطية أكبر قدر ممكن من الصيدليات
areas_keywords = {
    # مناطق الجيزة
    'فيصل': ('فيصل', 'الجيزة', 'القاهرة الكبرى'),
    'الهرم': ('الهرم', 'الجيزة', 'القاهرة الكبرى'),
    'الدقى': ('الدقى', 'الجيزة', 'القاهرة الكبرى'),
    'دقى': ('الدقى', 'الجيزة', 'القاهرة الكبرى'),
    'المهندسين': ('المهندسين', 'الجيزة', 'القاهرة الكبرى'),
    'امبابه': ('امبابه', 'الجيزة', 'القاهرة الكبرى'),
    'الوراق': ('الوراق', 'الجيزة', 'القاهرة الكبرى'),
    'بشتيل': ('بشتيل', 'الجيزة', 'القاهرة الكبرى'),
    'ارض اللواء': ('ارض اللواء', 'الجيزة', 'القاهرة الكبرى'),
    'كرداسه': ('كرداسه', 'الجيزة', 'القاهرة الكبرى'),
    'كفرطهرمس': ('كفرطهرمس', 'الجيزة', 'القاهرة الكبرى'),
    'كفر طهرمس': ('كفرطهرمس', 'الجيزة', 'القاهرة الكبرى'),
    'صفط': ('صفط اللبن', 'الجيزة', 'القاهرة الكبرى'),
    'العمرانية': ('العمرانية', 'الجيزة', 'القاهرة الكبرى'),
    'بولاق': ('بولاق الدكرور', 'الجيزة', 'القاهرة الكبرى'),
    'الجيلاتمه': ('الجلاتمه', 'الجيزة', 'القاهرة الكبرى'),
    'الجلاتمه': ('الجلاتمه', 'الجيزة', 'القاهرة الكبرى'),
    'حدائق الاهرام': ('حدائق الاهرام', 'الجيزة', 'القاهرة الكبرى'),
    'حدايق الاهرام': ('حدائق الاهرام', 'الجيزة', 'القاهرة الكبرى'),
    'حدائق اكتوبر': ('حدائق اكتوبر', 'الجيزة', 'القاهرة الكبرى'),
    'حدايق اكتوبر': ('حدائق اكتوبر', 'الجيزة', 'القاهرة الكبرى'),
    'الكونيسه': ('الكونيسه', 'الجيزة', 'القاهرة الكبرى'),
    'البراجيل': ('البراجيل', 'الجيزة', 'القاهرة الكبرى'),
    'برطس': ('برطس', 'الجيزة', 'القاهرة الكبرى'),
    'المعتمديه': ('المعتمديه', 'الجيزة', 'القاهرة الكبرى'),
    'الطوابق': ('الطوابق', 'الجيزة', 'القاهرة الكبرى'),
    'ام المصريين': ('ام المصريين', 'الجيزة', 'القاهرة الكبرى'),
    'اللبيني': ('اللبيني', 'الجيزة', 'القاهرة الكبرى'),
    'العجوزة': ('العجوزة', 'الجيزة', 'القاهرة الكبرى'),
    'العجوزه': ('العجوزة', 'الجيزة', 'القاهرة الكبرى'),
    
    # مناطق القاهرة
    'السيدة زينب': ('السيدة زينب', 'القاهرة', 'القاهرة الكبرى'),
    'سيده زينب': ('السيدة زينب', 'القاهرة', 'القاهرة الكبرى'),
    'دار السلام': ('دار السلام', 'القاهرة', 'القاهرة الكبرى'),
    'المعادى': ('المعادى', 'القاهرة', 'القاهرة الكبرى'),
    'مصر القديمة': ('مصر القديمة', 'القاهرة', 'القاهرة الكبرى'),
    'حلوان': ('حلوان', 'القاهرة', 'القاهرة الكبرى'),
    'شبرا': ('شبرا', 'القاهرة', 'القاهرة الكبرى'),
    'الزيتون': ('الزيتون', 'القاهرة', 'القاهرة الكبرى'),
    'عين شمس': ('عين شمس', 'القاهرة', 'القاهرة الكبرى'),
    'المنيرة': ('المنيرة', 'القاهرة', 'القاهرة الكبرى'),
    'الرحاب': ('الرحاب', 'القاهرة', 'القاهرة الكبرى'),
    'المقطم': ('المقطم', 'القاهرة', 'القاهرة الكبرى'),
    'القطامية': ('القطامية', 'القاهرة', 'القاهرة الكبرى')
}

def extract_geography(row):
    search_text = clean_arabic_text(str(row['account_name']) + " " + str(row['account_address']))
    for kw, (area, city, region) in areas_keywords.items():
        cleaned_kw = clean_arabic_text(kw)
        if cleaned_kw in search_text:
            return pd.Series([area, city, region])
    return pd.Series(['غير محدد', 'غير محدد', 'غير محدد'])

df[['extracted_area', 'extracted_city', 'extracted_region']] = df.apply(extract_geography, axis=1)

print("--- توزيع عينة من المناطق المستخرجة ---")
print(df['extracted_area'].value_counts().head(10))
print(f"نسبة تغطية المناطق: {((df['extracted_area'] != 'غير محدد').sum() / len(df)) * 100:.2f}%")

print("\\n--- توزيع المدن المستخرجة ---")
print(df['extracted_city'].value_counts())"""))

# ==========================================
# Phase 3: Data Modeling
# ==========================================
cells.append(nbf.v4.new_markdown_cell("""## المرحلة 3: نمذجة البيانات وتصديرها (Data Modeling)

في هذه المرحلة، سنقوم بـ:
1. تطبيق خريطة التوحيد (Mappings) على البيانات الأصلية للحصول على أسماء موحدة.
2. إنشاء معرّفات عامة موحدة فريدة (Global Keys) لكل من المنتجات والصيدليات والمناديب والجغرافيا.
3. تفكيك الجدول الكبير الموحد إلى جداول الأبعاد (Dimensions) وجدول الحقائق (Fact Table) بنظام **Star Schema**.
4. تصدير هذه الجداول كملفات CSV نظيفة تماماً."""))

cells.append(nbf.v4.new_code_cell("""# 1. تطبيق الخرائط على الجدول الرئيسي للحصول على الحقول الموحدة
df['clean_employee_name'] = df['employee_name'].map(emp_mapping).fillna(df['employee_name']).fillna('غير محدد')
df['clean_product_name'] = df['product_name'].map(product_mapping).fillna(df['product_name'])
df['clean_account_name'] = df['account_name'].map(account_mapping).fillna(df['account_name'])

# 2. إنشاء معرّفات موحدة فريدة للكيانات (Global IDs)

# أ. جدول بعد المنتجات (dim_products)
unique_clean_products = df['clean_product_name'].unique()
dim_products = pd.DataFrame({
    'global_prod_id': [f"P{i+1:04d}" for i in range(len(unique_clean_products))],
    'product_name': unique_clean_products
})
prod_to_id = dict(zip(dim_products['product_name'], dim_products['global_prod_id']))

# ب. جدول بعد الصيدليات (dim_customers)
unique_clean_accounts = df['clean_account_name'].unique()
# نأخذ عنواناً واحداً ممثلاً لكل صيدلية موحدة لتفادي التكرار
customer_details = df.groupby('clean_account_name').agg({
    'account_address': 'first',
    'extracted_area': 'first',
    'extracted_city': 'first',
    'extracted_region': 'first'
}).reset_index()

dim_customers = pd.DataFrame({
    'global_account_id': [f"C{i+1:04d}" for i in range(len(unique_clean_accounts))],
    'account_name': customer_details['clean_account_name'],
    'account_address': customer_details['account_address'],
    'area': customer_details['extracted_area'],
    'city': customer_details['extracted_city'],
    'region': customer_details['extracted_region']
})
cust_to_id = dict(zip(dim_customers['account_name'], dim_customers['global_account_id']))

# ج. جدول بعد الموظفين/المناديب (dim_employees)
unique_clean_employees = df['clean_employee_name'].unique()
dim_employees = pd.DataFrame({
    'global_employee_id': [f"E{i+1:03d}" for i in range(len(unique_clean_employees))],
    'employee_name': unique_clean_employees
})
emp_to_id = dict(zip(dim_employees['employee_name'], dim_employees['global_employee_id']))

# د. جدول بعد الموردين (dim_suppliers)
unique_suppliers = df['supplier_id'].unique()
dim_suppliers = pd.DataFrame({
    'supplier_id': unique_suppliers,
    'supplier_name': [f"Supplier_{sid}" for sid in unique_suppliers]
})

# هـ. جدول بعد الجغرافيا (dim_geography)
unique_geo = df[['extracted_area', 'extracted_city', 'extracted_region']].drop_duplicates().reset_index(drop=True)
dim_geography = pd.DataFrame({
    'geography_id': [f"G{i+1:03d}" for i in range(len(unique_geo))],
    'area': unique_geo['extracted_area'],
    'city': unique_geo['extracted_city'],
    'region': unique_geo['extracted_region']
})
# إنشاء مفتاح مركب للربط السريع
dim_geography['geo_key'] = dim_geography['area'] + "_" + dim_geography['city'] + "_" + dim_geography['region']
geo_to_id = dict(zip(dim_geography['geo_key'], dim_geography['geography_id']))
dim_geography.drop(columns=['geo_key'], inplace=True)

# 3. ربط جدول الحقائق (fact_sales) بالمعرفات العامة
df['global_prod_id'] = df['clean_product_name'].map(prod_to_id)
df['global_account_id'] = df['clean_account_name'].map(cust_to_id)
df['global_employee_id'] = df['clean_employee_name'].map(emp_to_id)
df['geo_key'] = df['extracted_area'] + "_" + df['extracted_city'] + "_" + df['extracted_region']
df['geography_id'] = df['geo_key'].map(geo_to_id)

fact_sales = df[[
    'id', 'invoice_id', 'supplier_id', 'global_prod_id', 'global_account_id', 
    'global_employee_id', 'geography_id', 'quantity', 'discount', 
    'total_amount', 'creation_date', 'created_at'
]].rename(columns={'id': 'transaction_id'})

# 4. حفظ الجداول في ملفات CSV جديدة ونظيفة
fact_sales.to_csv('fact_sales.csv', index=False)
dim_products.to_csv('dim_products.csv', index=False)
dim_customers.to_csv('dim_customers.csv', index=False)
dim_employees.to_csv('dim_employees.csv', index=False)
dim_suppliers.to_csv('dim_suppliers.csv', index=False)
dim_geography.to_csv('dim_geography.csv', index=False)

print("--- تم تصدير جداول الـ Star Schema بنجاح! ---")
print(f"Fact Table (fact_sales): {fact_sales.shape[0]} صف")
print(f"Products Dimension (dim_products): {dim_products.shape[0]} صف")
print(f"Customers Dimension (dim_customers): {dim_customers.shape[0]} صف")
print(f"Employees Dimension (dim_employees): {dim_employees.shape[0]} صف")
print(f"Geography Dimension (dim_geography): {dim_geography.shape[0]} صف")"""))

# ==========================================
# Phase 4: Analytics
# ==========================================
cells.append(nbf.v4.new_markdown_cell("""## المرحلة 4: التحليلات واستخراج الإحصائيات (Analytics & Insights)

في هذه المرحلة، سنقوم بتحليل البيانات والإيرادات على مستوى الصيدليات ونستخرج التحليلات الأساسية:
1. إيرادات كل صيدلية وتقسيمها حسب المورد.
2. مقارنة "قبل" و "بعد" التنظيف للمنتجات ومناديب المبيعات لتوضيح تأثير التنظيف والتنسيق على التقارير."""))

cells.append(nbf.v4.new_code_cell("""# 1. حساب إجمالي الإيرادات والفواتير لكل صيدلية وتقسيمها حسب المورد
pharmacy_revenue = df.groupby('clean_account_name')['total_amount'].sum().sort_values(ascending=False).reset_index()
pharmacy_invoices = df.groupby('clean_account_name')['invoice_id'].nunique().reset_index()

pharmacy_summary = pd.merge(pharmacy_revenue, pharmacy_invoices, on='clean_account_name')
pharmacy_summary.columns = ['الصيدلية', 'إجمالي الإيرادات', 'عدد الفواتير الفريدة']

print("--- أعلى 10 صيدليات تحقيقاً للإيرادات ---")
print(pharmacy_summary.head(10).to_string(index=False))

# تقسيم إيرادات صيدلية معينة بحسب المورد (مثال لأعلى صيدلية)
top_pharmacy_name = pharmacy_summary.iloc[0]['الصيدلية']
top_pharmacy_breakdown = df[df['clean_account_name'] == top_pharmacy_name].groupby('supplier_id')['total_amount'].sum().reset_index()
top_pharmacy_breakdown.columns = ['معرف المورد', 'الإيرادات']
print(f"\\n--- تقسيم إيرادات أعلى صيدلية ({top_pharmacy_name}) حسب المورد ---")
print(top_pharmacy_breakdown.to_string(index=False))"""))

cells.append(nbf.v4.new_code_cell("""# 2. مقارنة "قبل" و "بعد" التوحيد والتنظيف لإيضاح أثر العملية على تقارير الأداء

# أ. مناديب المبيعات (employee_name) قبل وبعد التنظيف
print("--- أعلى 5 مناديب مبيعات مبيعاً قبل التوحيد ---")
print(df.groupby('employee_name')['total_amount'].sum().sort_values(ascending=False).head(5))

print("\\n--- أعلى 5 مناديب مبيعات مبيعاً بعد التوحيد ---")
print(df.groupby('clean_employee_name')['total_amount'].sum().sort_values(ascending=False).head(5))

# ب. المنتجات (product_name) قبل وبعد التنظيف
print("\\n--- أعلى 5 منتجات مبيعاً قبل التوحيد ---")
print(df.groupby('product_name')['total_amount'].sum().sort_values(ascending=False).head(5))

print("\\n--- أعلى 5 منتجات مبيعاً بعد التوحيد ---")
print(df.groupby('clean_product_name')['total_amount'].sum().sort_values(ascending=False).head(5))"""))

cells.append(nbf.v4.new_code_cell("""# ج. رسم بياني يوضح تأثير التنظيف على أعلى المنتجات مبيعاً
top_products_before = df.groupby('product_name')['total_amount'].sum().sort_values(ascending=False).head(10)
top_products_after = df.groupby('clean_product_name')['total_amount'].sum().sort_values(ascending=False).head(10)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

sns.barplot(x=top_products_before.values, y=top_products_before.index, ax=axes[0], palette='Reds_r')
axes[0].set_title('أعلى 10 منتجات مبيعاً (قبل التوحيد والتنظيف)')
axes[0].set_xlabel('إجمالي المبيعات')
axes[0].set_ylabel('اسم المنتج كما ورد')

sns.barplot(x=top_products_after.values, y=top_products_after.index, ax=axes[1], palette='Greens_r')
axes[1].set_title('أعلى 10 منتجات مبيعاً (بعد التوحيد والتنظيف)')
axes[1].set_xlabel('إجمالي المبيعات')
axes[1].set_ylabel('اسم المنتج الموحد')

plt.tight_layout()
plt.savefig('cleaning_impact_comparison.png', dpi=100)
plt.show()"""))

# Save the notebook structure
nb['cells'] = cells
with open('project_notebook.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Updated build_notebook.py successfully and rewrote project_notebook.ipynb with Phases 1, 2, 3, and 4.")
