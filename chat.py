import os
from datetime import datetime
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

# استخدام متغير البيئة للمفتاح
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ لم يتم العثور على متغير البيئة OPENAI_API_KEY")

# قراءة البيانات العربية والإنجليزية
with open("data/company_info_ar.txt", "r", encoding="utf-8") as f:
    ar_text = f.read().splitlines()

with open("data/company_info_en.txt", "r", encoding="utf-8") as f:
    en_text = f.read().splitlines()

# إنشاء embeddings لكل لغة
emb = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectordb_ar = FAISS.from_texts(ar_text, emb)
vectordb_en = FAISS.from_texts(en_text, emb)

retriever_ar = vectordb_ar.as_retriever()
retriever_en = vectordb_en.as_retriever()

# سلسلة سؤال/جواب
qa_ar = RetrievalQA.from_chain_type(
    llm=OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0),
    retriever=retriever_ar
)
qa_en = RetrievalQA.from_chain_type(
    llm=OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0),
    retriever=retriever_en
)

print("🤖 مساعد الشركة جاهز. اكتب سؤالك (أو 'خروج' لإنهاء):")

log_file = "chat_history.txt"

while True:
    query = input("س: ")
    if query.strip().lower() in ["خروج", "exit", "quit"]:
        print("🚪 تم إنهاء الجلسة.")
        break

    # تحديد اللغة
    if any('\u0600' <= c <= '\u06FF' for c in query):
        answer = qa_ar.run(query)
        lang = "AR"
    else:
        answer = qa_en.run(query)
        lang = "EN"

    print("ج:", answer)

    # حفظ في السجل مع اللغة
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] ({lang})\nس: {query}\nج: {answer}\n\n")
