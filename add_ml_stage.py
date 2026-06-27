import json
import nbformat as nbf

# Load existing notebook
with open('project_notebook.ipynb', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Create new cells for Stage 5
ml_cells = []

ml_cells.append(nbf.v4.new_markdown_cell("""## المرحلة 5: التعلم الآلي والتنبؤ (Machine Learning)

في هذا الجزء سنقوم بتطبيق 3 نماذج تعلم آلي:
1. **اكتشاف العمليات الشاذة (Anomaly Detection):** باستخدام خوارزمية **Isolation Forest** لتحديد الصفقات الشاذة أو المشكوك فيها (مثل خصم غير منطقي أو كمية ضخمة جداً).
2. **التنبؤ بالمبيعات (Sales Forecasting):** تجميع المبيعات يومياً وإنشاء خصائص زمنية وتدريب نموذج للتنبؤ بالمبيعات للأيام القادمة.
3. **التنبؤ بالطلب (Demand Prediction):** التنبؤ بحجم الطلب (الكميات المباعة) على أكثر منتج مبيعاً لدينا."""))

# Anomaly Detection Cell
ml_cells.append(nbf.v4.new_code_cell("""from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

print("--- 1. اكتشاف العمليات الشاذة (Anomaly Detection) ---")

# اختيار الخصائص الرقمية للتحليل
features = ['quantity', 'discount', 'total_amount']
X = df[features].copy()

# تقييس البيانات
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# تدريب نموذج Isolation Forest
# نسبة التلوث المتوقعة 1% (أي 1% من البيانات قد تكون شاذة)
iso_forest = IsolationForest(contamination=0.01, random_state=42)
df['is_anomaly'] = iso_forest.fit_predict(X_scaled)
# تحويل التصنيف: 1 لطبيعي، -1 لشاذ
df['is_anomaly'] = df['is_anomaly'].map({1: 0, -1: 1})

anomalies = df[df['is_anomaly'] == 1]
print(f"تم اكتشاف {len(anomalies)} عملية شاذة من إجمالي {len(df)} صف.")

# عرض بعض العمليات الشاذة المكتشفة
print("\\nأمثلة على العمليات الشاذة المكتشفة:")
print(anomalies[['clean_account_name', 'clean_product_name', 'quantity', 'discount', 'total_amount']].head(10).to_string(index=False))

# حفظ المعاملات الشاذة في ملف منفصل للتنبيهات
anomalies.to_csv('detected_anomalies.csv', index=False)
"""))

# Sales Forecasting Cell
ml_cells.append(nbf.v4.new_code_cell("""from sklearn.ensemble import RandomForestRegressor
from datetime import timedelta

print("--- 2. التنبؤ بالمبيعات المستقبلية (Sales Forecasting) ---")

# تحويل تاريخ الفاتورة مع معالجة التواريخ التالفة "0000-00-00" باستخدام errors='coerce'
df['date'] = pd.to_datetime(df['creation_date'], errors='coerce').dt.date

# حذف التواريخ التالفة (التي تحولت إلى NaT)
df_clean_dates = df.dropna(subset=['date']).copy()

daily_sales = df_clean_dates.groupby('date')['total_amount'].sum().reset_index()
daily_sales['date'] = pd.to_datetime(daily_sales['date'])
daily_sales = daily_sales.sort_values('date').reset_index(drop=True)

# إنشاء خصائص زمنية للتنبؤ (Time Features)
daily_sales['day_of_week'] = daily_sales['date'].dt.dayofweek
daily_sales['day_of_month'] = daily_sales['date'].dt.day
daily_sales['month'] = daily_sales['date'].dt.month
daily_sales['lag_1'] = daily_sales['total_amount'].shift(1)
daily_sales['lag_7'] = daily_sales['total_amount'].shift(7)
daily_sales['rolling_mean_7'] = daily_sales['total_amount'].shift(1).rolling(window=7).mean()

# حذف الصفوف التي تحتوي على قيم مفقودة نتيجة الـ Shift
daily_sales_clean = daily_sales.dropna().copy()

# تقسيم البيانات إلى تدريب واختبار (آخر 30 يوم للاختبار)
train_data = daily_sales_clean.iloc[:-30]
test_data = daily_sales_clean.iloc[-30:]

feature_cols = ['day_of_week', 'day_of_month', 'month', 'lag_1', 'lag_7', 'rolling_mean_7']
X_train, y_train = train_data[feature_cols], train_data['total_amount']
X_test, y_test = test_data[feature_cols], test_data['total_amount']

# تدريب نموذج RandomForest
model_forecaster = RandomForestRegressor(n_estimators=100, random_state=42)
model_forecaster.fit(X_train, y_train)

# التنبؤ على بيانات الاختبار
test_data = test_data.copy()
test_data['predicted_sales'] = model_forecaster.predict(X_test)

# حساب متوسط الخطأ المطلق
mae = np.mean(np.abs(test_data['predicted_sales'] - y_test))
print(f"متوسط الخطأ المطلق للتنبؤ (MAE) على مدار 30 يوماً الأخيرة: {mae:.2f} جنيه")

# رسم بياني للتنبؤ مقابل الفعلي
plt.figure(figsize=(14, 5))
plt.plot(daily_sales_clean['date'].iloc[-90:], daily_sales_clean['total_amount'].iloc[-90:], label='الفعلي (Actual)', color='blue')
plt.plot(test_data['date'], test_data['predicted_sales'], label='المتوقع (Forecast)', color='orange', linestyle='--')
plt.title('التنبؤ بالمبيعات اليومية لآخر 30 يوماً')
plt.xlabel('التاريخ')
plt.ylabel('إجمالي المبيعات (جنيه)')
plt.legend()
plt.tight_layout()
plt.savefig('sales_forecast_plot.png', dpi=100)
plt.show()
"""))

# Demand Prediction Cell
ml_cells.append(nbf.v4.new_code_cell("""print("--- 3. التنبؤ بحجم الطلب على المنتجات (Demand Prediction) ---")

# اختيار المنتج الأكثر مبيعاً (ميراج 1جم حقن) وتجميع الكميات المباعة منه يومياً
top_prod_name = "ميراج 1جم حقن"
top_prod_df = df[df['clean_product_name'] == top_prod_name].copy()
top_prod_df['date'] = pd.to_datetime(top_prod_df['creation_date'], errors='coerce').dt.date

# حذف التواريخ التالفة
top_prod_df = top_prod_df.dropna(subset=['date']).copy()

daily_demand = top_prod_df.groupby('date')['quantity'].sum().reset_index()
daily_demand['date'] = pd.to_datetime(daily_demand['date'])
daily_demand = daily_demand.sort_values('date').reset_index(drop=True)

# إعادة تعبئة الأيام الفارغة (إذا لم يكن هناك مبيعات في يوم ما)
all_dates = pd.date_range(start=daily_demand['date'].min(), end=daily_demand['date'].max())
daily_demand = daily_demand.set_index('date').reindex(all_dates, fill_value=0).reset_index()
daily_demand.columns = ['date', 'quantity']

# إنشاء خصائص زمنية
daily_demand['day_of_week'] = daily_demand['date'].dt.dayofweek
daily_demand['month'] = daily_demand['date'].dt.month
daily_demand['lag_1'] = daily_demand['quantity'].shift(1)
daily_demand['lag_7'] = daily_demand['quantity'].shift(7)
daily_demand_clean = daily_demand.dropna().copy()

# تدريب النموذج
X_demand = daily_demand_clean[['day_of_week', 'month', 'lag_1', 'lag_7']]
y_demand = daily_demand_clean['quantity']

demand_model = RandomForestRegressor(n_estimators=100, random_state=42)
demand_model.fit(X_demand, y_demand)
print(f"تم تدريب نموذج التنبؤ بالطلب لمنتج '{top_prod_name}' بنجاح.")
"""))

# Append cells to notebook
# Since we need to replace the failed ML cells rather than appending them repeatedly, let's load the notebook, 
# keep only the cells up to the modeling & analytics, and append the corrected ML cells!
# Cells from 0 to 14 in the original are: Title(0), Imports(1), Nulls(2), Proof(3), Stage 2 Title(4), Clean(5), Fuzzy Emp(6), Fuzzy Prod(7), Geo(8), Stage 3 Title(9), Modeling(10), Stage 4 Title(11), Revenue(12), Compare(13), Plot(14)
# Let's verify how many cells are in the notebook currently. If we already appended ML cells once and it failed, 
# we should keep only the first 15 cells (indices 0 to 14) and drop the rest.
nb['cells'] = nb['cells'][:15]
nb['cells'].extend(ml_cells)

# Save the updated notebook
with open('project_notebook.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Stage 5 (Machine Learning) fixed and updated in project_notebook.ipynb.")
