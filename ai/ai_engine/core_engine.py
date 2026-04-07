import os
import time
import re
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings


load_dotenv()

# --- CLOUD CONFIGURATION ---
#os.environ["PINECONE_API_KEY"] = os.getenv("PINECONE_API_KEY")
#os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
INDEX_NAME = "citizen-helper"
   
# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def normalize_query(query: str) -> str:
    """ 
    Normalizes the user query by resolving synonyms and removing punctuation.
    Used to increase retrieval recall for domain-specific Vietnamese legal terms.
    """
    query_lower = query.lower()
    synonyms = {
        r'\bxe máy\b': 'xe mô tô, xe gắn máy',
        r'\bxài\b': 'sử dụng',
        r'\blái xe\b': 'điều khiển',
        r'\bnón bảo hiểm\b': 'mũ bảo hiểm'
    }
    for pattern, replacement in synonyms.items():
        query_lower = re.sub(pattern, replacement, query_lower)
    query_lower = re.sub(r'[?!.]', '', query_lower)
    return query_lower.strip()

def initialize_cloud_brain():
    """ 
    Initializes Cloud-based services (Pinecone & Gemini). 
    Optimized for low-latency memory usage by offloading to managed services.
    """
    logging.info("Connecting to Pinecone Vector DB and Gemini API...")
    
    # 1. Initialize Embeddings (runs on CPU)
    embeddings = HuggingFaceEmbeddings(
        model_name="huyydangg/DEk21_hcmute_embedding",
        model_kwargs={'device': 'cpu'},
        huggingfacehub_api_token=os.environ.get("HF_TOKEN") 
    )

    # 2. Establish Pinecone connection for retrieval
    vector_db = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    retriever = vector_db.as_retriever(search_kwargs={"k": 15})

    # 3. Initialize Large Language Model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.1
    )

    return retriever, llm

def generate_response(user_query: str, retriever, llm) -> str:
    start_time = time.time()

    # 1. MULTI-QUERY EXPANSION
    # Enhances retrieval coverage by generating multiple search variations.
    normalized_query = normalize_query(user_query)
    queries = [
        user_query,
        normalized_query,
        f"Quy định, biểu mức thu phí, mức phạt pháp luật liên quan đến: {normalized_query}",
        f"Quy định giảm giá, miễn trừ, ngoại lệ, điều kiện thời gian cho: {normalized_query}" 
    ]

    # 2. DOCUMENT RETRIEVAL & DEDUPLICATION
    logging.info("Scanning document index on Pinecone Cloud...")
    all_docs = []
    unique_docs = {} 
    
    for q in queries:
        docs = retriever.invoke(q)
        for doc in docs[:6]:
            unique_docs[doc.page_content] = doc

    context_text = "\n\n".join(
        [f"Tài liệu {i+1}: {doc.page_content}" for i, doc in enumerate(list(unique_docs.values())[:15])]
    )

    # 3. CHAIN-OF-THOUGHT (CoT) PROMPTING
    logging.info("🧠 Gemini đang suy luận...")
    prompt = f"""Bạn là Trợ lý Pháp luật cấp cao (Citizen Helper). Bạn có khả năng phân tích luật và tính toán logic.
Dựa VÀO DUY NHẤT ngữ cảnh dưới đây để trả lời câu hỏi.

QUY TRÌNH SUY LUẬN BẮT BUỘC (CHAIN-OF-THOUGHT):
Bước 1: Tìm quy định gốc (Mức phí/mức phạt cơ bản).
Bước 2: Đối chiếu điều kiện (thời gian, hình thức nộp online/offline, đối tượng) để tìm các quy định giảm trừ, ngoại lệ trong ngữ cảnh.
Bước 3: Thực hiện tính toán từng bước (nếu có) và đưa ra kết luận con số cuối cùng.

LƯU Ý QUAN TRỌNG:
- Trình bày rõ ràng, mạch lạc, dễ hiểu.
- Tuyệt đối không tự suy diễn số liệu nếu ngữ cảnh không có.
- Bắt buộc trích dẫn rõ (Tài liệu, Điều, Khoản).
- KHÔNG dùng công thức toán học phức tạp, chỉ cần ghi phép tính đơn giản (VD: 200.000 x 90% = 180.000).

NGỮ CẢNH:
{context_text}

CÂU HỎI: {user_query}"""

    # 4. LLM INFERENCE (Fast API Execution)
    outputs = llm.invoke(prompt)
    answer = outputs.content

    execution_time = time.time() - start_time
    logging.info(f"Response generated in {execution_time:.2f} seconds.")

    return answer

if __name__ == "__main__":
    logging.info("--- CITIZEN HELPER SYSTEM BOOTING (CLOUD MODE) ---")
    
    try:
        retriever, llm = initialize_cloud_brain()

        logging.info("System ready. Running Multi-hop Reasoning Test...")
        test_query = "Tôi làm thủ tục xin cấp mới hộ chiếu phổ thông qua mạng (trực tuyến) vào tháng 6 năm 2025 thì phải nộp chính xác bao nhiêu tiền lệ phí?"
        
        response = generate_response(test_query, retriever, llm)
        
        print(f"\n{'='*70}\n[USER QUERY]: {test_query}\n{'-'*70}\n[RESPONSE]:\n{response}\n{'='*70}")

    except Exception as e:
        logging.error(f"System execution failed: {e}")