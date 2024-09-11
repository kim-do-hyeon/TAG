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

# 벡터 DB 위치
db_path = "faiss_DB"

# API 키 설정
API = ""

# 임베딩 모델 설정
embeddings_model = OpenAIEmbeddings(openai_api_key=API)

# 코사인 유사도 측정 함수
def cos_sim(A, B):
    return dot(A, B) / (norm(A) * norm(B))

# 토큰 길이 측정 함수
tokenizer = tiktoken.get_encoding("cl100k_base")
def tiktoken_len(text):
    tokens = tokenizer.encode(text)
    return len(tokens)

# 설정값을 입력받는 함수
def input_option():
    separators = input("문서 분할을 위한 separators를 입력해주세요 (ex. \n, .,): ").split(',')  # 입력받은 구분자를 리스트로 변환
    chunk_size = int(input("문서 분할을 위한 chunk_size를 입력해주세요 (ex. 500): "))
    chunk_overlap = int(input("문서 분할을 위한 chunk_overlap을 입력해주세요 (ex. 250): "))
    return separators, chunk_size, chunk_overlap

# 청크 출력 함수
def print_chunks(chunks):
    print("\n--- 생성된 청크들 ---")
    for i, chunk in enumerate(chunks):
        print(f"청크 {i+1}:\n{chunk.page_content}\n")
    print(f"총 {len(chunks)}개의 청크가 생성되었습니다.")

# 재분할 또는 임베딩 여부 확인
def ask_to_continue(prompt_message):
    return input(prompt_message).strip().lower() == 'y'

# 처리 과정 반복 함수
def process_documents(file_format, documents):
    while True:
        # 스플릿 설정값 입력받기
        separators, chunk_size, chunk_overlap = input_option()

        # 스플릿 형식 설정
        text_splitter = rctp(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=tiktoken_len
        )

        # 문서 분할
        chunks = text_splitter.split_documents(documents)
        print_chunks(chunks)

        # 재분할 또는 DB 임베딩 여부 묻기
        if ask_to_continue("청크를 재분할하거나 DB에 임베딩 하시겠습니까? (y/n): "):
            return chunks
        else:
            print("청크 분할을 다시 시작합니다.")

# 파일 포맷 입력 받기
file_format = input("파일 포맷을 입력해주세요 (ex. pdf = pdf, txt = txt) : ")

if file_format == "pdf":
    pdf_path = input(r"DB에 저장할 PDF 파일경로 입력 : ")
    file_split_format = int(input("문서의 분할 형식을 입력해주세요 (ex. 1 = 기본, 2 = 2중 컬럼 분할) : "))

    if file_split_format == 1:
        # 기본 PDF 로드 및 텍스트 분할
        loader = pdfloader(pdf_path)
        pages = loader.load_and_split()  # 모든 문서 로드
        documents = [Document(page_content=text.page_content, metadata={"source": pdf_path, "page": i+1}) for i, text in enumerate(pages)]

    elif file_split_format == 2:
        # 2중 컬럼 PDF 처리
        doc = fitz.open(pdf_path)
        all_text = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # 페이지 로드
            page_rect = page.rect  # 페이지 크기 가져오기 (x0, y0, x1, y1)

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

    # 설정값 입력받고 청크 분할
    final_chunks = process_documents(file_format, documents)

elif file_format == "txt":
    # TEXT 문서 로드
    text_path = input(r"DB에 저장할 TEXT 파일경로 입력 : ")
    loader = TextLoader(text_path, encoding='utf-8')
    documents = loader.load()  # 텍스트 문서 로드

    # 설정값 입력받고 청크 분할
    final_chunks = process_documents(file_format, documents)

# 최종적으로 선택된 청크들만 FAISS DB에 임베딩
if final_chunks:
    # FAISS DB가 이미 존재하는지 확인
    if os.path.exists(db_path):
        # 기존 DB 불러오기
        print("기존 DB를 불러오고 있습니다...")
        docsearch = FAISS.load_local(db_path, embeddings_model, allow_dangerous_deserialization=True)
        print("기존 DB가 성공적으로 불러와졌습니다.")

        # 새로운 문서 임베딩 후 DB에 추가
        print("새로운 문서를 기존 DB에 추가 중입니다...")
        docsearch.add_documents(final_chunks)
    else:
        # 새로 DB 생성
        print("새로운 DB를 생성 중입니다...")
        docsearch = FAISS.from_documents(final_chunks, embeddings_model)

    # FAISS DB를 로컬에 저장 (덮어쓰기 또는 새로 저장)
    docsearch.save_local(db_path)
    print(f"FAISS DB가 {db_path}에 저장되었습니다.")
else:
    print("청크들이 FAISS DB에 임베딩되지 않았습니다.")
