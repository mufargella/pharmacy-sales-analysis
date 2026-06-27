import time
import subprocess
import json
import os
import sys

# ضمان طباعة المخرجات فوراً في ملف السجل
sys.stdout.reconfigure(encoding='utf-8')

print("Starting Periodic Telegram Scheduler Daemon...")
config_file = 'telegram_config.json'

def get_config():
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading config: {e}")
    return {}

# تعيين وقت التشغيل السابق ليكون 0 ليعمل التقرير فور تفعيل الخيار لأول مرة
last_run_time = 0

while True:
    try:
        config = get_config()
        enabled = config.get('enabled', False)
        interval_minutes = float(config.get('interval_minutes', 1440))  # افتراضياً 24 ساعة (1440 دقيقة)
        
        current_time = time.time()
        
        if enabled:
            # التحقق مما إذا حان وقت التشغيل (مرور الفترة المحددة)
            if current_time - last_run_time >= (interval_minutes * 60):
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Triggering periodic Telegram report...")
                sys.stdout.flush()
                
                # تشغيل بوت التليجرام لإرسال التقرير
                result = subprocess.run(['python', 'telegram_bot.py'], capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode == 0:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Periodic report sent successfully.")
                else:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Failed to send periodic report: {result.stderr}")
                
                sys.stdout.flush()
                last_run_time = current_time
        else:
            # إذا تم إلغاء التفعيل، نقوم بتصفير التوقيت ليرسل فوراً عند التفعيل مجدداً
            last_run_time = 0
            
    except Exception as ex:
        print(f"Scheduler loop error: {ex}")
        sys.stdout.flush()
        
    # النوم لمدة 10 ثوانٍ قبل التحقق من الإعدادات مرة أخرى لضمان الاستجابة السريعة لأي تغييرات
    time.sleep(10)
