# test_deepseek_requests.py

import requests
import json

# ---------------- إعداد API ----------------
API_KEY = "sk-29ba8e07294f4b0f9b186fca898e9520"
API_URL = "https://api.deepseek.com/v1/chat/completions"  # الرابط الصحيح حسب حسابك

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "أنت مساعد ذكي لشركة طاقة شمسية. استخدم فقط المعلومات المتاحة."},
        {"role": "user", "content": "مرحبا، هل يمكنك الرد على هذا الاختبار؟"}
    ],
    "stream": False
}

# ---------------- إرسال الطلب واستخراج الرد ----------------
try:
    response = requests.post(API_URL, headers=headers, json=payload)
    print("Status code:", response.status_code)

    if response.status_code == 200:
        result = response.json()
        # استخراج النص مباشرة من message.content إذا موجود
        if "message" in result and "content" in result["message"]:
            print("✅ Response:", result["message"]["content"])
        elif "text" in result:
            # كحل احتياطي إذا الرسالة موجودة في حقل text
            print("✅ Response (text fallback):", result["text"])
        else:
            print("⚠️ لم يتم الحصول على إجابة من الخادم")
    else:
        print("⚠️ حدث خطأ:", response.text)

except Exception as e:
    print(f"⚠️ حدث خطأ أثناء الاتصال بالـ API: {e}")
