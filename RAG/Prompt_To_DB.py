from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler as callback
from langchain.embeddings import OpenAIEmbeddings

# OpenAI API 키 설정
API = ""

# FAISS 벡터 DB 로드
embeddings_model = OpenAIEmbeddings(openai_api_key=API)
db_path = r"실제 DB Dir 경로"
docsearch = FAISS.load_local(db_path, embeddings_model, allow_dangerous_deserialization=True)

openai = ChatOpenAI(model_name="gpt-4",
                    streaming=True,  # 실시간 스트리밍 출력
                    callbacks=[callback()],  # 스트리밍 콜백 설정
                    temperature=0,  # 응답의 다양성을 낮춤 (결정적인 응답)
                    openai_api_key=API)

qa = RetrievalQA.from_chain_type(llm=openai,
                                 chain_type="stuff",  # 단순 응답 생성을 위한 체인 타입
                                 retriever=docsearch.as_retriever(search_type="mmr", search_kwargs={'k': 5, 'fetch_k': 10}), #10개의 문서를 선정하고 5개의 문서만 사용자에게 출력해줌
                                 return_source_documents=True)  # 원본 문서 반환

query = input("질의를 입력하세요 : ")

result = qa(query)


print("-"*100)
print(f"질문: {query}\n")
print("-"*100)
print(f"응답: {result['result']}\n")

# 검색된 문서들 출력 (출처 확인용)
for i, doc in enumerate(result['source_documents']):
    print("-"*100)
    print(f"{i+1}번째 관련 문서:\n{doc.page_content}")
    print(f"메타데이터: {doc.metadata}\n")