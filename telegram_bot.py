import os
import sys
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime

# دعم طباعة الحروف العربية في التيرمينال
sys.stdout.reconfigure(encoding='utf-8')

# ----------------------------------------------------
# دالة تجميع وحساب بيانات التقرير الدوري
# ----------------------------------------------------
def generate_report_data():
    # تحميل الجداول الموحدة
    try:
        fact_sales = pd.read_csv('fact_sales.csv')
        dim_geography = pd.read_csv('dim_geography.csv')
        dim_employees = pd.read_csv('dim_employees.csv')
        dim_customers = pd.read_csv('dim_customers.csv')
    except Exception as e:
        print(f"خطأ أثناء قراءة ملفات البيانات: {e}")
        return None

    # دمج البيانات
    df = fact_sales.merge(dim_employees, on='global_employee_id')
    df = df.merge(dim_geography, on='geography_id')
    
    # حساب الإحصائيات
    total_sales = df['total_amount'].sum()
    transaction_count = len(df)
    
    top_region = df.groupby('region')['total_amount'].sum().idxmax()
    top_region_sales = df.groupby('region')['total_amount'].sum().max()
    
    top_employee = df.groupby('employee_name')['total_amount'].sum().idxmax()
    top_employee_sales = df.groupby('employee_name')['total_amount'].sum().max()

    # تحميل العمليات الشاذة (التنبيهات)
    anomalies_msg = ""
    if os.path.exists('detected_anomalies.csv'):
        anomalies = pd.read_csv('detected_anomalies.csv')
        if not anomalies.empty:
            anomalies_msg = "\n🚨 *تنبيهات العمليات الشاذة الأخيرة (Top Alerts):*\n"
            # أخذ آخر 3 عمليات شاذة
            latest_anomalies = anomalies.tail(3)
            for idx, row in latest_anomalies.iterrows():
                anomalies_msg += f"- صيدلية: `{row['clean_account_name']}` | منتج: `{row['clean_product_name']}` | المبلغ: `{row['total_amount']:.2f} ج.م` | خصم: `{row['discount']}%`\n"
        else:
            anomalies_msg = "\n✅ لا توجد عمليات شاذة مكتشفة مؤخراً."
    else:
        anomalies_msg = "\n⚠️ ملف اكتشاف العمليات الشاذة غير متوفر."

    # تنسيق نص الرسالة
    report_text = f"""
📊 *تقرير المبيعات الدوري الموحد* 📊
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
------------------------------------------
💰 *إجمالي المبيعات:* `{total_revenue_format(total_sales)}` ج.م
📈 *عدد العمليات:* `{transaction_count:,}` حركة مبيعات

🌍 *أعلى منطقة مبيعاً:* `{top_region}`
💵 (مبيعات المنطقة: `{total_revenue_format(top_region_sales)}` ج.م)

👤 *أفضل مندوب مبيعات:* `{top_employee}`
💵 (مبيعات المندوب: `{total_revenue_format(top_employee_sales)}` ج.م)
------------------------------------------
{anomalies_msg}
    """
    return report_text

def total_revenue_format(val):
    if val >= 1_000_000:
        return f"{val/1_000_000:.2f}M"
    elif val >= 1_000:
        return f"{val/1_000:.2f}K"
    return f"{val:.2f}"

# ----------------------------------------------------
# دالة إرسال الرسالة إلى تليجرام
# ----------------------------------------------------
async def send_telegram_message(text):
    # قراءة التوكن والـ Chat ID من متغيرات البيئة
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("\n=== [MOCK MODE] لم يتم العثور على TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID ===")
        print("سيتم طباعة رسالة التقرير هنا كمعاينة للبوت:\n")
        print(text)
        print("========================================================================\n")
        print("ℹ️ لإرسال التقرير فعلياً إلى تليجرام، قم بضبط متغيرات البيئة وتشغيل السكربت:")
        print("   $env:TELEGRAM_BOT_TOKEN='your_token'")
        print("   $env:TELEGRAM_CHAT_ID='your_chat_id'")
        print("   python telegram_bot.py")
        return False
        
    try:
        from telegram import Bot
        bot = Bot(token=token)
        # إرسال الرسالة بدعم تنسيق Markdown
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        print("✅ تم إرسال تقرير تليجرام بنجاح!")
        return True
    except Exception as e:
        print(f"❌ فشل إرسال رسالة تليجرام: {e}")
        return False

# ----------------------------------------------------
# التشغيل الرئيسي للسكربت
# ----------------------------------------------------
if __name__ == "__main__":
    report_text = generate_report_data()
    if report_text:
        asyncio.run(send_telegram_message(report_text))
