from openai import OpenAI

# ---------------- إعداد العميل ----------------
client = OpenAI(
    api_key="sk-29ba8e07294f4b0f9b186fca898e9520",  # ضع مفتاحك هنا
    base_url="https://api.deepseek.com"  # تأكد من الرابط الصحيح
)

# ---------------- إرسال الطلب ----------------
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that only uses the provided data."},
        {"role": "user", "content": "Hello"}
    ],
    stream=False
)

# ---------------- استخراج النص بحرية ----------------
# بعض نسخ DeepSeek ترسل الرد هنا:
if hasattr(response, "message") and hasattr(response.message, "content"):
    print(response.message.content)
elif hasattr(response, "choices") and len(response.choices) > 0:
    # كحل احتياطي فقط
    print(response.choices[0].message.content)
else:
    print("⚠️ لم يتم الحصول على إجابة من الخادم")
