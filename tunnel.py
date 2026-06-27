import subprocess
import time
import sys

# ضمان طباعة المخرجات فوراً في التيرمينال دون تخزين مؤقت
sys.stdout.reconfigure(encoding='utf-8')

print("Starting Serveo Keep-Alive Tunnel Script...")

while True:
    try:
        print("Connecting to Serveo...")
        proc = subprocess.Popen(
            ['ssh', '-o', 'StrictHostKeyChecking=no', '-R', '80:127.0.0.1:8501', 'serveo.net'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            encoding='utf-8'
        )
        
        # قراءة الأسطر فوراً وطباعتها
        for line in proc.stdout:
            cleaned_line = line.strip()
            if cleaned_line:
                print(f"[Tunnel] {cleaned_line}")
                # نقوم بعمل flush للمخرجات لضمان كتابتها في ملف السجل فوراً
                sys.stdout.flush()
                
        proc.wait()
        print("Connection closed by Serveo. Reconnecting in 3 seconds...")
    except Exception as e:
        print(f"Tunnel error: {e}")
        sys.stdout.flush()
    time.sleep(3)
