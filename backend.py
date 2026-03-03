import os
import time
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning)

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

app = Flask(__name__)
CORS(app)

if not os.path.exists("data"):
    os.makedirs("data")

print("Reading PDFs from /data folder...")
loader = PyPDFDirectoryLoader("data/")
docs = loader.load()

if docs:
    # Limit to just 5 pages so you don't have to wait an hour for testing
    if len(docs) > 5:
        print("Limiting to 5 pages for faster testing based on your 1k TPM limit...")
        docs = docs[:5]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)
    print(f"Total chunks to process: {len(chunks)}")
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # --- THE 1K TPM PROTECTOR ---
    # 1 chunk is roughly 250 tokens. We can safely send 3 chunks (750 tokens) per minute.
    vector_store = None
    batch_size = 3 
    
    print("\n--- BEGINNING SLOW, SAFE UPLOAD ---")
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        print(f"Uploading chunks {i + 1} to {i + len(batch)} to Google...")
        
        if vector_store is None:
            vector_store = InMemoryVectorStore.from_documents(documents=batch, embedding=embeddings)
        else:
            vector_store.add_documents(documents=batch)
            
        # Pause for a full minute to reset the 1k TPM limit
        if i + batch_size < len(chunks):
            print("⏳ 1k Token Limit Reached. Pausing for 60 seconds to respect Google quota...")
            time.sleep(60)
            
    print("--- UPLOAD COMPLETE ---\n")

    retriever = vector_store.as_retriever(search_kwargs={"k": 1})

    template = """
    You are a helpful, polite PDF assistant. 
    
    Rule 1: You are allowed to respond naturally to basic greetings and small talk (like "Hi", "Hello", "Good morning", "Who are you?").
    Rule 2: For any factual questions, answer ONLY using the provided Context below.
    Rule 3: If the user asks a factual question and the answer is not in the Context, say: "I'm sorry, that is not in the documents."
    Do not use outside knowledge to answer questions.
    
    Context: {context}
    Question: {question}
    Answer:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    print("✅ Backend ready! Safely loaded under the 1k TPM limit.")
else:
    rag_chain = None
    print("⚠️ Warning: No PDFs found in /data folder.")

@app.route('/info', methods=['GET'])
def info():
    try:
        if not os.path.exists("data"):
            return jsonify({"message": "No data folder found."})
            
        files = [f for f in os.listdir("data") if f.endswith('.pdf')]
        
        if not files:
            return jsonify({"message": "I only answer based on the provided documents."})
            
        file_list = ", ".join(files)
        return jsonify({"message": f"I am an expert on the following documents: {file_list}"})
    except Exception as e:
        return jsonify({"message": "I only answer based on the provided documents."})
@app.route('/ask', methods=['POST'])
def ask():
    if not rag_chain:
        return jsonify({"answer": "Backend error: No PDF data found."})
    
    try:
        user_query = request.json.get("question")
        response = rag_chain.invoke(user_query)
        return jsonify({"answer": response})
    except Exception as e:
        return jsonify({"answer": f"API Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000)