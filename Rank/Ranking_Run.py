from Rank_Embedding import TagPriorityGenerator  # 태그 우선순위 생성기
import json
from datetime import datetime

class TagPriorityManager:
    """
    태그 데이터와 설명을 기반으로 우선순위 분석을 관리하는 클래스
    """

    def __init__(self, tagged_data_path, priority_data_path, tags=None):
        """
        생성자에서 태그 데이터를 로드하고 우선순위 데이터를 불러옵니다.
        
        Parameters:
        tagged_data_path (str): 태그된 데이터를 저장한 JSON 파일 경로
        priority_data_path (str): 우선순위 데이터를 저장한 JSON 파일 경로
        tags (dict): 분석에 필요한 태그와 설명을 포함한 딕셔너리 (선택적, 기본값 None)     
        """
        self.tagged_data_path = tagged_data_path  # 태그된 데이터 파일 경로
        self.priority_data_path = priority_data_path  # 우선순위 데이터 파일 경로
        self.tags = tags  # 태그 데이터, 전달되지 않으면 None
        self.tagged_data = self.load_json(self.tagged_data_path)  # 태그된 데이터를 로드
        self.priority_data = self.load_json(self.priority_data_path)  # 우선순위 데이터를 로드

    def load_json(self, file_path):
        """
        JSON 파일을 읽어오는 함수.
        
        Parameters:
        file_path (str): 파일 경로
        
        Returns:
        dict: 파일의 JSON 데이터를 딕셔너리로 반환
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def find_dicts_with_tag_key(self):
        """
        태그된 데이터를 순회하면서 `_Tag_`로 끝나는 키를 찾고, 해당 딕셔너리와 태그 값을 리스트로 반환합니다.
        
        Returns:
        list: 태그된 데이터와 매칭된 태그를 리스트로 반환
        """
        results = []
        for key, value in self.tagged_data.items():
            if isinstance(value, list):
                for entry in value:
                    if isinstance(entry, dict):
                        for sub_key in entry:
                            if "_Tag_" in sub_key:
                                matched_tag = entry[sub_key]  # _Tag_ 키의 값을 matched_tag에 저장
                                results.append((entry, matched_tag))  # matched_tag와 함께 추가
                                break  # 해당 dict에서 원하는 키를 찾았으면 나머지는 확인하지 않음
        return results

    def extract_relevant_data(self, artifact_to_date_key):
        """
        태그된 데이터를 시간 정보와 함께 추출합니다.
        
        Parameters:
        artifact_to_date_key (dict): artifact_name에 따른 시간 정보를 저장한 키 맵핑
        
        Returns:
        list: 각 항목의 hit_id, artifact_name, date_key, date_value, matched_tag가 포함된 리스트
        """
        tagged_data = self.find_dicts_with_tag_key()
        result = []
        
        for entry, matched_tag in tagged_data:
            artifact_name = entry.get("artifact_name")
            if artifact_name in artifact_to_date_key:
                date_key = artifact_to_date_key[artifact_name]

                # USB Devices와 같이 여러 날짜 필드가 있을 때 처리
                if isinstance(date_key, list):
                    for key in date_key:
                        if key in entry and entry[key]:
                            result.append((entry["hit_id"], artifact_name, key, entry[key], matched_tag))
                else:
                    if date_key in entry and entry[date_key]:
                        result.append((entry["hit_id"], artifact_name, date_key, entry[date_key], matched_tag))

        # 결과를 시간순으로 정렬
        result.sort(key=lambda x: datetime.strptime(x[3], "%Y-%m-%d %H:%M:%S.%f"))
        return result

    def group_by_priority(self, matched_tag, result):
        """
        매칭된 태그에 따른 우선순위를 기반으로 결과를 그룹화합니다.
        
        Parameters:
        matched_tag (str): 매칭된 태그
        result (list): 태그가 포함된 리스트
        
        Returns:
        dict: 우선순위에 따라 그룹화된 결과
        """
        priority_groups = {}

        # 해당 matched_tag의 tag_ranking을 가져옴
        if matched_tag in self.priority_data:
            ranking_data = self.priority_data[matched_tag]["tag_ranking"]

            # 우선순위에 따라 그룹화
            for rank, next_tag in ranking_data.items():
                priority_groups[rank] = []
                for hit_id, artifact_name, date_key, date_value, tag in result:
                    if tag == next_tag:
                        priority_groups[rank].append([hit_id, artifact_name, date_key, date_value, tag])

        return priority_groups

    def print_grouped_result(self, matched_tag, priority_groups):
        """
        그룹화된 결과를 출력하는 함수
        
        Parameters:
        matched_tag (str): 매칭된 태그
        priority_groups (dict): 우선순위별로 그룹화된 결과
        """
        print(f"\nTag: {matched_tag}")
        for rank, group in priority_groups.items():
            print(f"Rank {rank}:")
            if group:
                for item in group:
                    hit_id, artifact_name, date_key, date_value, tag = item
                    print(f"  - hit_id: {hit_id}, artifact_name: {artifact_name}, date_key: {date_key}, date_value: {date_value}, matched_tag: {tag}")
            else:
                print(f"  - No results for Rank {rank}")

    def run_priority_analysis(self, artifact_to_date_key):
        """
        우선순위 분석을 실행하는 함수. 태그 데이터를 분석하여 우선순위별로 그룹화된 결과를 출력합니다.
        
        Parameters:
        artifact_to_date_key (dict): artifact_name에 따른 시간 정보 맵핑
        """
        result = self.extract_relevant_data(artifact_to_date_key)

        # 그룹화된 결과 출력
        for hit_id, artifact_name, date_key, date_value, matched_tag in result:
            priority_groups = self.group_by_priority(matched_tag, result)
            if priority_groups:
                self.print_grouped_result(matched_tag, priority_groups)


# 메인 실행 부분
if __name__ == "__main__":
    # OpenAI API 키 설정
    api_key = "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"

    # 시나리오 텍스트 예시
    scenario_text = "파일이 Gmail Drive를 통해 외부로 유출될 가능성이 있습니다."

    # 태그와 설명을 포함한 딕셔너리
    tags = {
        "Gmail_Drive_Sharing" : "Gmail을 통한 Google Drive 파일 링크 공유.",
        "Gmail_Create_New_mail" : "Gmail에서의 새로운 메일 작성.",
        "File_Web_Access" : "웹 브라우저를 통한 디스크 내 파일 실행.",
        "Mega_Drive" : "익명 클라우드 파일공유 서비스인 Mega 웹 페이지 방문.",
        "Dropbox_Drive" : "익명 클라우드 파일공유 서비스인 DropBox 웹 페이지 방문.",
        "Short_URL_Service" : "짧은 URL 서비스를 사용중인 웹 사이트 접속.",
        "VPN_Service" : "VPN과 관련된 문자열을 가진 URL 패턴의 사이트 접속.",
        "Use_Proxy_Server_PORT" : "프록시 서버의 포트를 사용하는 웹 사이트 접속.",
        "NAS_Quick_Connect_Server" : "Quick Connect 서버의 파일 공유 웹 사이트 접속.",
        "NAS_C2_Synology_Server" : "C2 Synology 서버의 파일공유 웹 사이트 접속.",
        "IP_Address_Server" : "개인 IPv4의 형식을 가진 IP 서버 웹 사이트 접속.",
        "Google_Drive_Upload" : "Google Drive를 이용한 파일 업로드.",
        "User_USB" : "디스크 이미지 내 연결된 USB 이력 탐지.",
        "File_Remove" : "이미 삭제되어 Recycle Bin에 위치한 파일.",
        "Google_Login" : "Google에 로그인하는 웹 사이트 접속.",
        "Gmail_Inbox" : "Gmail 서비스 실행 시 기본으로 생기는 URL 패턴(특정 행동을 하지 않아도 Gmail 접속만으로 생성됨).",
        "Gmail_Sent" : "Gmail 서비스 중 보낸 이메일 확인 웹 사이트 접속.",
        "Gmail_Subject" : "이메일의 본문을 열람하기 위한 웹 사이트 접속 (해당 이메일의 제목이 포함된 URL 생성).",
        "Web_Search" : "검색 포털을 이용한 웹 검색 기록(검색 내역도 포함되어있음).",
        "Web_PDF" : "웹을 통한 PDF 문서 열람 웹사이트 접속.",
        "Tistory_Blog" : "Tistory 블로그 페이지 웹 사이트 접속.",
        "Google_Redirection" : "Google 관련 페이지에서 다른 URL로 리다이렉트 시 발생하는 패턴 탐지.",
        "Web_PDF_Download" : "웹을 통한 PDF 파일 다운로드.",
        "Web_EXE_Download" : "웹을 통한 EXE 파일 다운로드.",
        "Web_HWP_Download" : "웹을 통한 HWP 파일 다운로드.",
        "Web_DOC_Download" : "웹을 통한 DOC 파일 다운로드.",
        "Web_DOCS_Download" : "웹을 통한 DOCS 파일 다운로드."
    }

    # 사용자 선택에 따라 TagPriorityGenerator 실행 여부 결정
    create_priority = input("우선순위 데이터를 생성하시겠습니까? (y/n): ").strip().lower()

    if create_priority == 'y':
        # TagPriorityGenerator 인스턴스 생성
        tag_generator = TagPriorityGenerator(api_key)

        # 우선순위 데이터를 생성하고 저장
        tag_generator.save_priority_data(scenario_text, tags, output_path="tag_priority_data.json")
        print("우선순위 데이터가 생성되었습니다.")
    else:
        print("우선순위 데이터 생성이 건너뛰어졌습니다.")

    # JSON 파일 경로 설정
    tagged_data_path = 'tagged_data.json'
    priority_data_path = 'tag_priority_data.json'

    # 분석을 위한 인스턴스 생성
    tag_priority_manager = TagPriorityManager(tagged_data_path, priority_data_path, tags)

    # artifact_name에 따른 시간 정보 맵핑
    artifact_to_date_key = {
        "Edge Chromium Cache Records": "Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)",
        "Edge Chromium Downloads": "Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)",
        "Edge Chromium Last Session": "Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)",
        "Edge Chromium Web Visits": "Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)",
        "USB Devices": ["Last_Insertion_Date/Time_-_UTC_(yyyy-mm-dd)", "Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)"],
        "Recycle Bin": "Deleted_Date/Time_-_UTC_(yyyy-mm-dd)",
        "Edge Chromium Current Session": "Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)",
        "Edge Chromium Downloads": "Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)"
    }

    # 우선순위 분석 실행 여부를 사용자에게 선택
    user_choice = input("우선순위 분석을 실행하시겠습니까? (y/n): ").strip().lower()
    
    if user_choice == 'y':
        tag_priority_manager.run_priority_analysis(artifact_to_date_key)
    else:
        print("우선순위 분석이 실행되지 않았습니다.")
