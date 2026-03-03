import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()

class RestrictedBot:
    def __init__(self, pdf_path):
        # 1. Load and Split PDF
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = splitter.split_documents(docs)
        
        # 2. Create Vector Store (ChromaDB)
        embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma.from_documents(texts, embeddings, persist_directory="./chroma_db")
        
        # 3. Setup LLM with Strict Guardrail Prompt
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        
        template = """
        You are a restricted assistant. Use ONLY the context below to answer.
        If the answer is NOT in the context, say: "This information is not available in the PDF."
        Do NOT answer general knowledge questions.
        
        Context: {context}
        Question: {question}
        Answer:"""
        
        QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": QA_PROMPT}
        )

    def ask(self, query):
        return self.qa_chain.invoke(query)["result"]