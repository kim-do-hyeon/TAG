import os
from langchain.document_loaders import PyPDFLoader as pdfloader
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler as callback
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter as rctp
from langchain_community.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import FAISS
import tiktoken
import fitz

#벡터 DB 위치
db_path = "faiss_DB"

#API 키 설정
API = ""

#임베딩 모델 설정
embeddings_model = OpenAIEmbeddings(openai_api_key = API)

# 코사인 유사도 측정 함수
def cos_sim(A, B):
    return dot(A, B) / (norm(A) * norm(B))

# 토큰 길이 측정 함수
tokenizer = tiktoken.get_encoding("cl100k_base")
def tiktoken_len(text):
    tokens = tokenizer.encode(text)
    return len(tokens)

# 파일 포맷 입력 받기
file_format = input("파일 포맷을 입력해주세요 (ex. pdf = pdf, txt = txt) : ")

if file_format == "pdf":
    pdf_path = input(r"DB에 저장할 PDF 파일경로 입력 : ")
    file_split_format = int(input("문서의 분할 형식을 입력해주세요 (ex. 1 = 기본, 2 = 2중 컬럼 분할) : "))

    if file_split_format == 1:
        # 스플릿 형식 설정
        text_splitter = rctp(
            separators=["."],  
            chunk_size=500,  
            chunk_overlap=250, 
            length_function=tiktoken_len 
        )
    
        # 기본 PDF 로드 및 텍스트 분할
        loader = pdfloader(pdf_path)
        pages = loader.load_and_split()  # 모든 문서 로드
        texts = text_splitter.split_documents(pages)  # 문서 분할
        documents = [Document(page_content=text.page_content, metadata={"source": pdf_path, "page": i+1}) for i, text in enumerate(texts)]
        
    elif file_split_format == 2:
        # 스플릿 형식 설정
        text_splitter = rctp(
            separators=["."],  
            chunk_size=250,  
            chunk_overlap=125, 
            length_function=tiktoken_len 
        )

        # 2중 컬럼 PDF 처리
        doc = fitz.open(pdf_path)
        all_text = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # 페이지 로드
            page_rect = page.rect           # 페이지 크기 가져오기 (x0, y0, x1, y1)

            # 좌측 컬럼 텍스트 추출 (페이지의 절반 왼쪽 부분)
            left_column = page_rect.x0, page_rect.y0, (page_rect.x0 + page_rect.x1) / 2, page_rect.y1
            left_column_text = page.get_text("text", clip=fitz.Rect(*left_column))

            # 우측 컬럼 텍스트 추출 (페이지의 절반 오른쪽 부분)
            right_column = (page_rect.x0 + page_rect.x1) / 2, page_rect.y0, page_rect.x1, page_rect.y1
            right_column_text = page.get_text("text", clip=fitz.Rect(*right_column))

            comb_text = left_column_text + "\n" + right_column_text
            all_text.append(comb_text)

        # 추출된 텍스트를 Document 객체로 변환
        documents = [Document(page_content=page, metadata={"source": pdf_path, "page": i+1}) for i, page in enumerate(all_text)]

        # 문서 분할
        texts = text_splitter.split_documents(documents)

elif file_format == "txt":
    text_splitter = rctp(
        separators=["\n"], 
        chunk_size=500, 
        chunk_overlap=250, 
        length_function=tiktoken_len
    )
    
    # TEXT 문서 로드
    text_path = input(r"DB에 저장할 TEXT 파일경로 입력 : ")
    loader = TextLoader(text_path, encoding='utf-8')
    documents = loader.load()  # 텍스트 문서 로드

    # 문서 분할
    texts = text_splitter.split_documents(documents)

# 분할된 문서를 로드하여 처리
print(f"총 {len(texts)}개의 문서가 분할되었습니다.")


# FAISS DB가 이미 존재하는지 확인
if os.path.exists(db_path):
    # 기존 DB 불러오기
    print("기존 DB를 불러오고 있습니다...")
    docsearch = FAISS.load_local(db_path, embeddings_model, allow_dangerous_deserialization=True)
    print("기존 DB가 성공적으로 불러와졌습니다.")
    
    # 새로운 문서 임베딩 후 DB에 추가
    print("새로운 문서를 기존 DB에 추가 중입니다...")
    docsearch.add_documents(documents)
else:
    # 새로 DB 생성
    print("새로운 DB를 생성 중입니다...")
    docsearch = FAISS.from_documents(documents, embeddings_model)

# FAISS DB를 로컬에 저장 (덮어쓰기 또는 새로 저장)
docsearch.save_local(db_path)

print(f"FAISS DB가 {db_path}에 저장되었습니다.")

