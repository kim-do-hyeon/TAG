# 1. 문서 별로  type → score 변수 생성 & 저장
#     1. USB ⇒ 4.50 점 부여
#     2. Printer ⇒ 3.88 점 부여
#     3. Mail, Drive, Blog ⇒ 5.00 점 부여
# 2. 문서 파일 별로 final_score.json 순회하여  score 에 더하기
# 3. temp_score.json 의 각 파일 별로 1, 2 합 score 변수 형태로 달아주기
# 4. 각 문서 별 score 최대점 기준으로 하위 백분율 기존의 priority에 저장
type_score = {
    "USB":4.50,
    "Printer":3.88,
    "Mail":5.00,
    "Drive":5.00,
    "Blog":5.00
}
# 경로
temp_output_path = './temp_output.json' # (기존) 웹 업로드 시 최종 사용 json
docs_score_path = './final_score.json'  # calc_suspicion.py 결과 json
final_output_path = './final_output.json' # 현재 코드 결과 output json
# 웹 업로드 용 json 로드 (temp_output.json)
with open(temp_output_path, 'r', encoding='utf-8') as file:
    temp_output = json.load(file)
# 문서 별 rename, excessice_read 저장된 json (final_score.json) 로드
with open(docs_score_path, 'r', encoding='utf-8') as file:
    docs_score = json.load(file)
doc_total_score = []
for item in temp_output:
    # 1. row 별로 type → score 변수 생성 & 저장    
    item["score"] = type_score[item["type"]]
    # 2. row 별 문서 파일의 final_score.json 순회하여 score 에 더하기
    for doc_score in docs_score:
        if item["filename"] == doc_score["filename"][0]:
            item["score"] += doc_score["score_total"]
            break
# 4. 각 row 별 score 최대점 기준으로 하위 백분율 기존의 priority에 저장
for item in temp_output:
    doc_total_score.append(item["score"])
max_score = max(doc_total_score)
percentages = [(score / max_score) * 100 for score in doc_total_score]
for index, item in enumerate(temp_output):
    item["priority"] = percentages[index]
# 5. 저장
with open(final_output_path, 'w', encoding='utf-8') as file:
    json.dump(temp_output, file, indent=4, ensure_ascii=False, default=str)
file.close()
print("final_output.json이 저장되었습니다.")