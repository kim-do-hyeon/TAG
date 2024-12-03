# log_tagger.py
import re
import json
import datetime
import openai
import urllib.parse

class LogTagger:
    def __init__(self, data):
        self.data = data
        self.patterns = {
            "google_login_pattern": re.compile(r'로그인\s-\sGoogle\s계정'),
            "gmail_inbox_pattern": re.compile(r'Inbox\s\(\d+\)\s-\s.*@gmail\.com'),
            "gmail_sentmail_pattern": re.compile(r'(Sent\sMail)\s-\s.*@gmail\.com'),
            "gmail_subject_pattern": re.compile(r'.*\s-\s.*@gmail\.com'),
            "search_pattern": re.compile(r'(.*?\s-\s.*검색)'),
            "pdf_pattern": re.compile(r'.*?\.pdf'),
            "usb_device_pattern": re.compile(r'.*?\(Standard disk drives\)'),
            "remove_pattern": re.compile(r'Recycle\sBin'),
            "tistory_pattern": re.compile(r'https?://[\w-]+\.tistory\.com/[\w-]+'),
            "web_pdf_download_pattern": re.compile(r'.*?\.pdf'),
            "web_exe_download_pattern": re.compile(r'.*?\.exe'),
            "web_hwp_download_pattern": re.compile(r'.*?\.hwp'),
            "web_doc_download_pattern": re.compile(r'.*?\.doc'),
            "web_docs_download_pattern": re.compile(r'.*?\.docs'),
            "gmail_drive_sharing_pattern": re.compile(r'https:\/\/mail\.google\.com\/drivesharing.*?shareService=mail'),
            "google_drive_upload_pattern": re.compile(r'https:\/\/drive\.google\.com.*?upload\?'),
            "new_mail_create_pattern": re.compile(r'https:\/\/mail\.google\.com\/.*?inbox\?compose=new'),
            "google_redirection_pattern": re.compile(r'https:\/\/www\.google\.com\/url\?q='),
            "file_web_access": re.compile(r'file:\/\/\/[A-Za-z]:\/(?:[^\/\n]+\/)*[^\/\n]+?\.[a-zA-Z0-9]+'),
            "mega_drive_pattern": re.compile(r'https\/\/mega\.nz'),
            "dropbox_drive_pattern": re.compile(r'https\/\/www\.dropbox\.com\/'),
            "short_url_service_pattern": re.compile(r'\b(https?://)?(bit\.ly|tinyurl\.com|goo\.gl|t\.co|is\.gd|ow\.ly)/[a-zA-Z0-9]+\b'),
            "vpn_service_pattern": re.compile(r'\b(vpn|secure|proxy|anon|connect)\.[a-zA-Z0-9.-]+\b'),
            "proxy_server_port_pattern": re.compile(r':\b(8080|3128|8888|8000|8081|8118)\b'),
            "nas_quickconnect_pattern": re.compile(r'https:\/\/quickconnect\.to\/[a-zA-Z0-9]+(?:\/[^\s]*)?'),
            "nas_c2synology_pattern": re.compile(r'https:\/\/c2\.synology\.com\/[^\s]*'),
            "personal_ip_server_pattern": re.compile(r'https:\/\/(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/[^\s]*'),
            "naver_mybox_file_get_pattern": re.compile(r'https:\/\/api\.mybox\.naver\.com\/service\/vault\/file\/get\?'),
            "proton_mail_archive_pattern": re.compile(r'https:\/\/mail\.proton\.me.*archive'),
            "proton_mail_all_sent_pattern": re.compile(r'https:\/\/mail\.proton\.me.*all-sent'),
            "proton_mail_account_pattern": re.compile(r'https:\/\/account\.proton.*'),
            "proton_mail_all_drafts_pattern": re.compile(r'https:\/\/mail\.proton\.me.*all-drafts'),
            "proton_mail_inbox_pattern": re.compile(r'https:\/\/mail\.proton\.me.*inbox')
        }

    def tag_edge_chromium_web_visits(self, log):
        title_value = log.get("Title")
        url_value = log.get("URL")
        if not title_value or not url_value:
            return
        if self.patterns["google_login_pattern"].search(title_value):
            log['_Tag_'] = 'Google_Login'
        elif self.patterns["gmail_inbox_pattern"].search(title_value):
            log['_Tag_'] = 'Gmail_Inbox'
        elif self.patterns["gmail_sentmail_pattern"].search(title_value):
            log['_Tag_'] = 'Gmail_Sent'
        elif self.patterns["gmail_subject_pattern"].search(title_value):
            log['_Tag_'] = 'Gmail_Subject'
        elif self.patterns["search_pattern"].search(title_value):
            log['_Tag_'] = 'Web_Search'
        # elif self.patterns["pdf_pattern"].search(title_value):
        #     log['_Tag_'] = 'Web_PDF'
        if self.patterns["proton_mail_account_pattern"].search(url_value):
            log['_Tag_'] = 'Proton_Mail_Account'
        if self.patterns["proton_mail_archive_pattern"].search(url_value):
            log['_Tag_'] = 'Proton_Mail_Archive'
        if self.patterns["proton_mail_all_sent_pattern"].search(url_value):
            log['_Tag_'] = 'Proton_Mail_All_Sent'
        if self.patterns["proton_mail_all_drafts_pattern"].search(url_value):
            log['_Tag_'] = 'Proton_Mail_All_Drafts'
        if self.patterns["proton_mail_inbox_pattern"].search(url_value):
            log['_Tag_'] = 'Proton_Mail_Inbox'
        if self.patterns["gmail_drive_sharing_pattern"].search(url_value):
            log['_Tag_'] = 'Gmail_Drive_Sharing'
        elif self.patterns["new_mail_create_pattern"].search(url_value):
            log['_Tag_'] = 'Gmail_Create_New_mail'
        if self.patterns["google_redirection_pattern"].search(url_value):
            log['_Tag_'] = 'Google_Redirection'
        if self.patterns["file_web_access"].search(url_value):
            log['_Tag_'] = 'File_Web_Access'
        if self.patterns["mega_drive_pattern"].search(url_value):
            log['_Tag_'] = 'Mega_Drive'
        if self.patterns["dropbox_drive_pattern"].search(url_value):
            log['_Tag_'] = 'Dropbox_Drive'
        if self.patterns["short_url_service_pattern"].search(url_value):
            log['_Tag_'] = 'Short_URL_Service'
        if self.patterns["vpn_service_pattern"].search(url_value):
            log['_Tag_'] = 'VPN_Service'
        if self.patterns["proxy_server_port_pattern"].search(url_value):
            log['_Tag_'] = 'Use_Proxy_Server_PORT'
        if self.patterns["nas_quickconnect_pattern"].search(url_value):
            log['_Tag_'] = 'NAS_Quick_Connect_Server'
        if self.patterns["nas_c2synology_pattern"].search(url_value):
            log['_Tag_'] = 'NAS_C2_Synology_Server'
        if self.patterns["personal_ip_server_pattern"].search(url_value):
            log['_Tag_'] = 'IP_Address_Server'


    def tag_Edge_Chromium_Cache_Records(self, log):
        url_value = log.get("URL")
        if url_value is None:
            return
        if self.patterns["google_drive_upload_pattern"].search(url_value):
            log['_Tag_'] = 'Google_Drive_Upload'
        if self.patterns["naver_mybox_file_get_pattern"].search(url_value):
            log['_Tag_'] = 'Naver_MyBox_File_Get'

    def tag_usb_device(self, log):
        manufacturer_value = log.get("Manufacturer")
        if manufacturer_value is None:
            return
        if self.patterns["usb_device_pattern"].search(manufacturer_value):
            log['_Tag_'] = 'User_USB'

    def tag_recycle_bin(self, log):
        artifact_name_value = log.get("artifact_name")
        if artifact_name_value is None:
            return
        if self.patterns["remove_pattern"].search(artifact_name_value):
            log['_Tag_'] = 'File_Remove'

    def tag_edge_chromium_current_Last_session(self, log):
        title_value = log.get("Title")
        URL_value = log.get("URL")
        redirect_url_value = log.get("Redirect_URL")
        if not title_value or not URL_value:  # 두 값 중 하나라도 None이면 처리하지 않음
            return
        if self.patterns["google_login_pattern"].search(title_value):
            log['_Tag_'] = 'Google_Login'
        elif self.patterns["gmail_inbox_pattern"].search(title_value):
            log['_Tag_'] = 'Gmail_Inbox'
        elif self.patterns["gmail_sentmail_pattern"].search(title_value):
            log['_Tag_'] = 'Gmail_Sent'
        elif self.patterns["gmail_subject_pattern"].search(title_value):
            log['_Tag_'] = 'Gmail_Subject'
        elif self.patterns["search_pattern"].search(title_value):
            log['_Tag_'] = 'Web_Search'
        elif self.patterns["pdf_pattern"].search(title_value):
            log['_Tag_'] = 'Web_PDF'
        if self.patterns["tistory_pattern"].search(URL_value):
            log['_Tag_'] = 'Tistory_Blog'
        if self.patterns["google_redirection_pattern"].search(redirect_url_value):
            log['_Tag_'] = 'Google_Redirection'

    def tag_edge_chromium_downloads(self, log):
        file_name_value = log.get("File_Name")
        if file_name_value is None:
            return
        if self.patterns["web_pdf_download_pattern"].search(file_name_value):
            log['_Tag_'] = 'Web_PDF_Download'
        elif self.patterns["web_exe_download_pattern"].search(file_name_value):
            log['_Tag_'] = 'Web_EXE_Download'
        elif self.patterns["web_hwp_download_pattern"].search(file_name_value):
            log['_Tag_'] = 'Web_HWP_Download'
        elif self.patterns["web_doc_download_pattern"].search(file_name_value):
            log['_Tag_'] = 'Web_DOC_Download'
        elif self.patterns["web_docs_download_pattern"].search(file_name_value):
            log['_Tag_'] = 'Web_DOCS_Download'

    def apply_tags(self):
        for top_level_key, top_level_value in self.data.items():
            if top_level_key == "Edge_Chromium_Web_Visits":
                for log in top_level_value:
                    self.tag_edge_chromium_web_visits(log)
            elif top_level_key == "USB_Devices":
                for log in top_level_value:
                    self.tag_usb_device(log)
            elif top_level_key == "Recycle_Bin":
                for log in top_level_value:
                    self.tag_recycle_bin(log)
            elif top_level_key == "Edge_Chromium_Current_Session":
                for log in top_level_value:
                    self.tag_edge_chromium_current_Last_session(log) 
            elif top_level_key == "Edge_Chromium_Last_Session":
                for log in top_level_value:
                    self.tag_edge_chromium_current_Last_session(log)
            elif top_level_key == "Edge_Chromium_Downloads":
                for log in top_level_value:
                    self.tag_edge_chromium_downloads(log)
            elif top_level_key == "Chrome_Downloads":
                for log in top_level_value:
                    self.tag_edge_chromium_downloads(log)
            elif top_level_key == "Edge_Chromium_Cache_Records":
                for log in top_level_value:
                    self.tag_Edge_Chromium_Cache_Records(log)
            elif top_level_key == "Chrome_Cache_Records":
                for log in top_level_value:
                    self.tag_Edge_Chromium_Cache_Records(log)
            elif top_level_key == "Chrome_Web_Visits":
                for log in top_level_value:
                    self.tag_edge_chromium_web_visits(log)                   

    def save_data(self, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        print(f"태그가 추가된 데이터가 {output_path}에 저장되었습니다.")

# LogTagger_1 클래스 - 그룹화된 이메일과 PDF 다운로드 처리
class LogTagger_1:
    def __init__(self, data):
        if isinstance(data, (dict, list)):
            self.data = data
        else:
            raise TypeError("데이터 형식이 잘못되었습니다. 리스트 또는 딕셔너리가 필요합니다.")

    def parse_datetime(self, dt_str):
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_gmail_subjects(self):
        """ 모든 'Gmail_Subject' 태그를 가진 딕셔너리 리스트 반환 """
        gmail_logs = []
        for log in self.data.get("Edge_Chromium_Web_Visits", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'Gmail_Subject' and log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    gmail_logs.append(log)
        return gmail_logs

    def find_web_pdf_downloads(self):
        """ 모든 'Web_PDF_Download' 태그를 가진 딕셔너리 리스트 반환 """
        pdf_logs = []
        for log in self.data.get("Edge_Chromium_Downloads", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'Web_PDF_Download' and log.get('Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    pdf_logs.append(log)
        return pdf_logs

    def group_email_to_pdf_downloads(self):
        """ 시간순으로 Gmail_Subject와 Web_PDF_Download를 순차적으로 그룹화하는 함수 """
        # 'Edge_Chromium_Web_Visits' 또는 다른 키에서 로그 데이터를 추출해야 함
        logs = []
        for key in ['Edge_Chromium_Web_Visits', 'Edge_Chromium_Downloads']:  # 여러 키가 있을 경우 포함
            if key in self.data:
                logs.extend(self.data[key])
        
        # 로그 데이터를 시간순으로 정렬
        logs = sorted(logs, key=lambda x: self.parse_datetime(x.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)', x.get('Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)'))))

        grouped_downloads = []
        current_gmail_log = None

        for log in logs:
            if log.get('_Tag_') == 'Gmail_Subject':
                current_gmail_log = log
            elif log.get('_Tag_') == 'Web_PDF_Download' and current_gmail_log:
                grouped_downloads.append({
                    'gmail_log': current_gmail_log,
                    'pdf_log': log
                })
                current_gmail_log = None

        return grouped_downloads
    def apply_tags(self):
        # 이 부분에서 결과가 한 번만 출력되도록 조정
        grouped_logs = self.group_email_to_pdf_downloads()
        if grouped_logs:
            print("Gmail_Subject 이후의 Web_PDF_Download 그룹화 결과:")
            print(json.dumps(grouped_logs, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

#검색기록 키워드 추출
class LogTagger_1_1:
    def __init__(self, data):
        if isinstance(data, (dict, list)):
            self.data = data
        else:
            raise TypeError("데이터 형식이 잘못되었습니다. 리스트 또는 딕셔너리가 필요합니다.")

    def parse_datetime(self, dt_str):
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_gmail_new_mail(self):
        """ 모든 'Gmail_Create_New_mail' 태그를 가진 딕셔너리 리스트 반환 """
        gmail_logs = []
        for log in self.data.get("Edge_Chromium_Web_Visits", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'Gmail_Create_New_mail' and log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    gmail_logs.append(log)
        return gmail_logs

    def find_gmail_drive_sharing(self):
        """ 모든 'Gmail_Drive_Sharing' 태그를 가진 딕셔너리 리스트 반환 """
        pdf_logs = []
        for log in self.data.get("Edge_Chromium_Web_Visits", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'Gmail_Drive_Sharing' and log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    pdf_logs.append(log)
        return pdf_logs

    def group_gmail_to_drive_sharing(self):
        """ Gmail_Create_New_mail과 Gmail_Drive_Sharing을 시간순으로 그룹화 """
        logs = []
        for key in ['Edge_Chromium_Web_Visits']:  # 여러 키가 있을 경우 추가 가능
            if key in self.data:
                logs.extend(self.data[key])
        
        # 로그 데이터를 시간순으로 정렬
        logs = sorted(logs, key=lambda x: self.parse_datetime(x.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)', x.get('Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)'))))

        grouped_logs = []
        current_gmail_log = None

        for log in logs:
            if log.get('_Tag_') == 'Gmail_Create_New_mail':
                current_gmail_log = log
            elif log.get('_Tag_') == 'Gmail_Drive_Sharing' and current_gmail_log:
                grouped_logs.append({
                    'gmail_log': current_gmail_log,
                    'drive_sharing_log': log
                })
                current_gmail_log = None

        return grouped_logs

    def apply_tags(self):
        """ 그룹화된 결과를 적용하여 출력 """
        grouped_logs = self.group_gmail_to_drive_sharing()
        if grouped_logs:
            print("Gmail_Create_New_mail 이후의 Gmail_Drive_Sharing 그룹화 결과:")
            print(json.dumps(grouped_logs, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

class LogTagger_1_2:
    def __init__(self, data):
        if isinstance(data, (dict, list)):
            self.data = data
        else:
            raise TypeError("데이터 형식이 잘못되었습니다. 리스트 또는 딕셔너리가 필요합니다.")

    def parse_datetime(self, dt_str):
        """문자열 형식의 날짜/시간을 datetime 객체로 변환"""
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_gmail_subjects(self):
        """모든 'Gmail_Subject' 태그를 가진 딕셔너리 리스트 반환"""
        gmail_logs = []
        for log in self.data.get("Edge_Chromium_Web_Visits", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'Gmail_Subject' and log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    gmail_logs.append(log)
        return gmail_logs

    def find_google_redirection(self):
        """모든 'Google_Redirection' 태그를 가진 딕셔너리 리스트 반환"""
        redirection_logs = []
        for log in self.data.get("Edge_Chromium_Last_Session", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'Google_Redirection' and log.get('Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    redirection_logs.append(log)
        return redirection_logs

    def group_gmail_to_redirection(self):
        """시간순으로 Gmail_Subject와 Google_Redirection을 순차적으로 그룹화하는 함수"""
        logs = []
        for key in ['Edge_Chromium_Web_Visits', 'Edge_Chromium_Last_Session']:
            if key in self.data:
                logs.extend(self.data[key])

        # 로그 데이터를 시간순으로 정렬
        logs = sorted(logs, key=lambda x: self.parse_datetime(
            x.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)', x.get('Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'))))

        grouped_logs = []
        current_gmail_log = None

        for log in logs:
            if log.get('_Tag_') == 'Gmail_Subject':
                current_gmail_log = log
            elif log.get('_Tag_') == 'Google_Redirection' and current_gmail_log:
                grouped_logs.append({
                    'gmail_log': current_gmail_log,
                    'redirection_log': log
                })
                current_gmail_log = None

        return grouped_logs 

    def apply_tags(self):
        """그룹화된 결과를 적용하여 출력"""
        grouped_logs = self.group_gmail_to_redirection()
        if grouped_logs:
            print("Gmail_Subject 이후의 Google_Redirection 그룹화 결과:")
            print(json.dumps(grouped_logs, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

class LogTagger_1_3:
    def __init__(self, data):
        if isinstance(data, (dict, list)):
            self.data = data
        else:
            raise TypeError("데이터 형식이 잘못되었습니다. 리스트 또는 딕셔너리가 필요합니다.")

    def parse_datetime(self, dt_str):
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_file_web_access(self):
        """ 모든 'File_Web_Access' 태그를 가진 딕셔너리 리스트 반환 """
        file_web_access_logs = []
        for log in self.data.get("Edge_Chromium_Web_Visits", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'File_Web_Access' and log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    file_web_access_logs.append(log)
        return file_web_access_logs

    def find_pdf_file_web_access(self):
        """ 모든 '.pdf'로 끝나는 'File_Web_Access' 로그 파싱 """
        pdf_logs = []
        file_web_access_logs = self.find_file_web_access()
        
        for log in file_web_access_logs:
            url_value = log.get('URL', '')  # URL 값을 가져옴
            if url_value.endswith('.pdf'):
                pdf_logs.append(log)    
        return pdf_logs

    def extract_pdf_filename(self, url):
        """URL에서 .pdf 파일명을 추출"""
        return url.split("/")[-1] if url.endswith('.pdf') else None

    def find_matching_pdf_document(self):
        """시간순으로 File_Web_Access와 PDF_Document 로그를 그룹화하는 함수"""
        logs = []
        # Edge_Chromium_Web_Visits에서 File_Web_Access 로그 추가
        logs.extend(self.find_pdf_file_web_access())

        # 로그 데이터를 시간순으로 정렬
        logs = sorted(logs, key=lambda x: self.parse_datetime(x.get("Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)")))
        grouped_logs = []
        
        for pdf_log in logs:
            # URL 인코딩된 파일명을 추출하고 디코딩
            encoded_pdf_filename = self.extract_pdf_filename(pdf_log.get('URL', ''))
            pdf_filename = urllib.parse.unquote(encoded_pdf_filename)  # URL 디코딩

            visit_datetime_str = pdf_log.get("Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)")
            visit_datetime = self.parse_datetime(visit_datetime_str)

            # PDF_Document에서 Filename이 일치하는 로그를 찾음
            for document in self.data.get("PDF_Documents", []):
                if document.get('Filename') == pdf_filename:
                    fs_last_accessed_str = document.get("File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)")
                    fs_last_accessed_datetime = self.parse_datetime(fs_last_accessed_str)

                    # File_System_Last_Accessed_Date가 웹 방문 날짜보다 이전인 경우
                    if fs_last_accessed_datetime and visit_datetime and visit_datetime > fs_last_accessed_datetime:
                        grouped_logs.append({
                            'pdf_document_access_log': document,
                            'pdf_web_access_log': pdf_log
                        })
                    break  # 첫 번째 일치하는 로그를 찾으면 반복 중단

        return grouped_logs


    def apply_tags(self):
        """ 그룹화된 결과를 적용하여 출력 """
        matching_documents = self.find_matching_pdf_document()
        if matching_documents:
            print("File_Web_Access 로그와 일치하는 PDF_Document 그룹화 결과:")
            print(json.dumps(matching_documents, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

class LogTagger_1_4:
    def __init__(self, data):
        if isinstance(data, (dict, list)):
            self.data = data
        else:
            raise TypeError("데이터 형식이 잘못되었습니다. 리스트 또는 딕셔너리가 필요합니다.")
    
    def parse_datetime(self, dt_str):
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_naver_mybox_file_get(self):
        """ 모든 'naver_mybox_file_get' 태그를 가진 딕셔너리 리스트 반환 """
        naver_mybox_file_get_logs = []
        for log in self.data.get("Edge_Chromium_Cache_Records", []):
            if isinstance(log, dict):
                if log.get('_Tag_') == 'Naver_MyBox_File_Get' and log.get('Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    naver_mybox_file_get_logs.append(log)
        return naver_mybox_file_get_logs

    def find_mru_recent_files_and_folders(self):
        """ MRU_Recent_Files_&Folders 테이블에서 모든 로그 반환 """
        return self.data.get("MRU_Recent_Files_&Folders", [])

    def group_naver_mybox_and_mru_logs(self):
        """ 
        Naver_MyBox_File_Get 태그와 MRU_Recent_Files_&Folders 로그를 비교하여 
        Last_Visited_Date와 Registry_Key_Modified_Date가 1초 이내에 있는 로그 그룹화 
        """
        result = []
        naver_logs = self.find_naver_mybox_file_get()
        mru_logs = self.find_mru_recent_files_and_folders()

        for naver_log in naver_logs:
            naver_time_str = naver_log.get('Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)')
            naver_time = self.parse_datetime(naver_time_str)

            if naver_time is None:
                continue

            for mru_log in mru_logs:
                mru_time_str = mru_log.get('Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)')
                mru_time = self.parse_datetime(mru_time_str)

                if mru_time is None:
                    continue

                # 두 시간의 차이를 계산 (1초 이내인지 확인)
                time_diff = abs((naver_time - mru_time).total_seconds())

                if time_diff <= 1:  # 1초 이내
                    result.append({
                        "naver_log": naver_log,
                        "mru_log": mru_log.get('File/Folder_Name'),
                        "time_difference": time_diff
                    })

        return result

    def apply_tags(self):
        """ 그룹화된 결과를 적용하여 출력 """
        grouped_logs = self.group_naver_mybox_and_mru_logs()
        if grouped_logs:
            print("Naver_MyBox_File_Get와 MRU_Recent_Files_&Folders 그룹화 결과:")
            for log in grouped_logs:
                print(json.dumps(log, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")


class LogTagger_2:
    def parse_datetime(self, dt_str):
        """문자열 형식의 날짜/시간을 datetime 객체로 변환"""
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_web_search_keywords(self):
        """ 'Web_Search' 태그를 가진 로그에서 검색 키워드를 추출하고 시간순으로 정렬 """
        web_search_keyword_log = []
        for log in self.data.get("Edge_Chromium_Web_Visits", []):
            if isinstance(log, dict):
                title_value = log.get('Title')  # 타이틀 값을 가져옴
                if log.get('_Tag_') == 'Web_Search' and log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    # " - 검색" 앞의 문자열 추출
                    keyword = title_value.split(" - 검색")[0] if " - 검색" in title_value else None
                    if keyword:
                        log['Search_Keyword'] = keyword  # 추출한 키워드를 새로운 키로 추가
                    web_search_keyword_log.append(log)

        # 시간순으로 정렬 (Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)을 기준으로)
        web_search_keyword_log.sort(key=lambda x: self.parse_datetime(x['Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)']))

        # 시간순으로 나열된 키워드 출력
        for log in web_search_keyword_log:
            keyword = log.get('Search_Keyword', 'No Keyword')
            date_visited = log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)', 'No Date')
            print(f"{keyword}")

        return web_search_keyword_log, keyword
    
    def find_gmail_subject_keywords(self):
        """ 'Web_Search' 태그를 가진 로그에서 검색 키워드를 추출하고 시간순으로 정렬 """
        gmail_subject_keyword_log = []
        for log in self.data.get("Edge_Chromium_Web_Visits", []):
            if isinstance(log, dict):
                title_value = log.get('Title')  # 타이틀 값을 가져옴
                if log.get('_Tag_') == 'Gmail_Subject' and log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)') is not None:
                    match = re.match(r"(.+?)\s-\s[\w.-]+@[\w.-]+", title_value)
                    if match:
                        keyword = match.group(1)  # 이메일 앞부분의 텍스트만 추출
                        log['Search_Keyword'] = keyword  # 추출한 키워드를 새로운 키로 추가
                        gmail_subject_keyword_log.append(log)

        # 시간순으로 정렬 (Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)을 기준으로)
        gmail_subject_keyword_log.sort(key=lambda x: self.parse_datetime(x['Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)']))

        # 시간순으로 나열된 키워드 출력
        for log in gmail_subject_keyword_log:
            keyword = log.get('Search_Keyword', 'No Keyword')
            date_visited = log.get('Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)', 'No Date')
            print(f"{keyword}")

        return gmail_subject_keyword_log, keyword