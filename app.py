import os
import streamlit as st
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI

# =========================
# إعدادات عامة
# =========================
st.set_page_config(page_title="💼 نظام المساعد الذكي", layout="wide")

API_KEY = os.getenv("GEMINI_API_KEY", "")
if not API_KEY:
    st.warning("⚠️ لم يتم العثور على مفتاح Gemini API. ضع المفتاح في متغير البيئة GEMINI_API_KEY.")
else:
    genai.configure(api_key=API_KEY)

# =========================
# تحميل بيانات الشركة من مجلد data/
# =========================
@st.cache_resource
def load_and_index_data():
    docs = []
    data_dir = "data"

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    for file in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file)
        if file.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.endswith(".txt"):
            loader = TextLoader(file_path)
        elif file.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            continue
        docs.extend(loader.load())

    # تقسيم النصوص
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # إنشاء الفهارس باستخدام FAISS
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    return vectorstore

# =========================
# إعداد السلاسل (QA Chain)
# =========================
def get_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2)
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return chain

# =========================
# واجهة المستخدم
# =========================
st.title("🤖💼 نظام المساعد الذكي - بيانات الشركة")

tab1, tab2, tab3 = st.tabs(["🗨️ المحادثة", "📂 البيانات", "⚙️ الإعدادات"])

with tab1:
    st.header("💬 محادثة مع النظام")
    if API_KEY:
        vectorstore = load_and_index_data()
        qa_chain = get_qa_chain(vectorstore)

        user_q = st.text_input("اكتب سؤالك هنا:", "")
        if st.button("إرسال"):
            if user_q:
                with st.spinner("جارٍ المعالجة..."):
                    result = qa_chain({"query": user_q})
                    st.markdown("### ✨ الإجابة")
                    st.write(result["result"])

                    # إظهار المصادر
                    with st.expander("📎 المصادر"):
                        for doc in result["source_documents"]:
                            st.write(doc.metadata.get("source", "غير معروف"))
                            st.write(doc.page_content[:200] + "...")
            else:
                st.warning("⚠️ الرجاء إدخال سؤال.")
    else:
        st.error("⚠️ النظام غير مهيأ. الرجاء إضافة API Key.")

with tab2:
    st.header("📂 الملفات المفهرسة")
    data_dir = "data"
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        if files:
            st.write("تم العثور على الملفات التالية:")
            for f in files:
                st.write("📄", f)
        else:
            st.info("لا توجد ملفات في مجلد data/.")
    else:
        st.error("مجلد data/ غير موجود.")

with tab3:
    st.header("⚙️ الإعدادات")
    st.info("ضع ملفات الشركة في مجلد `data/`. سيتم تحديث الفهرسة تلقائيًا عند تشغيل النظام.")
    st.code("export GEMINI_API_KEY='ضع_مفتاحك_هنا'")
