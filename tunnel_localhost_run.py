import subprocess
import time
import sys

# ضمان طباعة المخرجات فوراً في ملف السجل
sys.stdout.reconfigure(encoding='utf-8')

print("Starting Localhost.run Keep-Alive Tunnel Script...")

while True:
    try:
        print("Connecting to Localhost.run...")
        proc = subprocess.Popen(
            ['ssh', '-o', 'StrictHostKeyChecking=no', '-R', '80:127.0.0.1:8501', 'nokey@localhost.run'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            encoding='utf-8'
        )
        
        # قراءة الأسطر وطباعتها فوراً لضمان سرعة الرصد
        for line in proc.stdout:
            cleaned_line = line.strip()
            if cleaned_line:
                print(f"[Tunnel] {cleaned_line}")
                sys.stdout.flush()
                
        proc.wait()
        print("Connection closed by Localhost.run. Reconnecting in 3 seconds...")
    except Exception as e:
        print(f"Tunnel error: {e}")
        sys.stdout.flush()
    time.sleep(3)
