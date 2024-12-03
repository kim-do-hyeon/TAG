import json
from datetime import datetime

# JSON 파일 경로 설정
input_json_file = 'merged_sorted_data.json'  # 입력 JSON 파일 경로
output_json_file = 'filtered_data.json'      # 필터링된 데이터 저장 경로

# JSON 파일에서 데이터를 불러오는 함수
def load_json_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file '{file_path}'.")
        return None

# 특정 시간 범위에 해당하는 데이터만 추출하는 함수
def filter_data_by_time_range(data, start_time, end_time):
    filtered_data = []
    for item in data:
        # timestamp가 존재하고, 시간 형식이 올바른 경우만 필터링
        if 'timestamp' in item:
            try:
                # 시간대를 제거한 offset-naive 형식으로 변환
                timestamp = datetime.fromisoformat(item['timestamp']).replace(tzinfo=None)
                if start_time <= timestamp <= end_time:
                    filtered_data.append(item)
            except ValueError:
                print(f"Invalid timestamp format in item: {item}")
    return filtered_data

# 시간 범위 입력 및 데이터 필터링
def main():
    # JSON 파일에서 데이터 로드
    data = load_json_data(input_json_file)
    if not data:
        return

    # 사용자로부터 시간 범위 입력
    try:
        start_time_str = input("Enter start time (YYYY-MM-DD HH:MM:SS): ")
        end_time_str = input("Enter end time (YYYY-MM-DD HH:MM:SS): ")
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
    except ValueError:
        print("Invalid date format. Please use 'YYYY-MM-DD HH:MM:SS'.")
        return

    # 시간 범위에 해당하는 데이터 필터링
    filtered_data = filter_data_by_time_range(data, start_time, end_time)

    # 필터링된 데이터를 JSON 파일로 저장
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=4, default=str)

    print(f"Filtered data saved to {output_json_file}")

# 프로그램 실행
if __name__ == "__main__":
    main()
