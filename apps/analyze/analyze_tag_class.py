import json
import datetime
import re
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.exc import OperationalError
import sys
import urllib.parse
from sqlalchemy import text

class LogTagger:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.patterns = {
            "Edge_Chromium_Web_Visits": {
                "Title": [
                    ("Web_Search", re.compile(r'(.*?\s-\s.*검색)'))             
                    # 기타 Title 패턴 추가 가능
                ],
                "URL": [
                    #Proton Mail 
                    ("Proton_Mail_Home_Page", re.compile(r'https:\/\/proton\.me\/mail')),
                    ("Proton_Mail_Login", re.compile(r'https:\/\/account\.proton.*')),
                    ("Proton_Mail_Login_Session", re.compile(r'https:\/\/mail\.proton\.me\/login#')),
                    ("Proton_Mail_Login_Session_Expired", re.compile(r'https:\/\/account\.proton\.me\/authorize\?app=proton-mail&state=.*reason=session-expired')),
                    ("Proton_Mail_Trash", re.compile(r'https:\/\/mail\.proton\.me.*trash')),
                    ("Proton_Mail_Archive", re.compile(r'https:\/\/mail\.proton\.me.*archive')),
                    ("Proton_Mail_All_Sent", re.compile(r'https:\/\/mail\.proton\.me.*all-sent')),
                    ("Proton_Mail_All_Drafts", re.compile(r'https:\/\/mail\.proton\.me.*all-drafts')),
                    ("Proton_Mail_Inbox", re.compile(r'https:\/\/mail\.proton\.me.*inbox')),
                    #Google
                    ("Google_Login_Service_Endpoint", re.compile(r'https:\/\/accounts\.google\.com\/ServiceLogin\?')),
                    ("Google_Login_Interactive_Endpoint", re.compile(r'https:\/\/accounts\.google\.com\/InteractiveLogin\?')),
                    ("Google_Redirection", re.compile(r'https:\/\/www\.google\.com\/url\?q=')),
                    #Gmail
                    ("Google_Mail_Inbox", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*ogbl\/\?pli=1$')),
                    ("Google_Mail_Inbox", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#inbox$')),
                    ("Google_Mail_Sent", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#sent$')),
                    ("Google_Mail_Drafts", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#drafts$')),
                    ("Google_Mail_trash", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#trash$')),
                    ("Google_Mail_Starred", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#starred$')),
                    ("Google_Mail_Open_Mail", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/[a-zA-Z]+$')),
                    ("Google_Mail_Mail_Write", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\?compose=.*$')),
                    ("Google_Mail_Drive_Sharing", re.compile(r'https:\/\/mail\.google\.com\/drivesharing.*?shareService=mail')),
                    ("Google_Mail_Create_New_mail", re.compile(r'https:\/\/mail\.google\.com\/.*\?compose=new')),
                    #Google Drive
                    ("Google_Drive_Main", re.compile(r'https:\/\/drive\.google\.com\/drive\/home')),
                    ("Google_Drive_My_Drive", re.compile(r'https:\/\/drive\.google\.com\/drive\/my-drive')),
                    ("Google_Drive_Folder", re.compile(r'https:\/\/drive\.google\.com\/drive\/folders')),
                    #Mega
                    ("Mega_Drive_Login", re.compile(r'https:\/\/mega\.nz\/login')),
                    ("Mega_Drive_Main", re.compile(r'https:\/\/mega\.nz\/fm')), #폴더를 들어가도 똑같음
                    #Dropbox
                    ("Dropbox_Drive_Drive", re.compile(r'^https:\/\/www\.dropbox\.com\/home$')),
                    ("Dropbox_Drive_Client_Login", re.compile(r'https:\/\/www\.dropbox\.com\/desktop\/oauth2\?code=.*&state=.*')),
                    #One Drive
                    ("One_Drive_Login", re.compile(r'https:\/\/onedrive\.live\.com\/login\/')),
                    ("One_Drive_Folder", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=.*&cid=.*')),
                    ("One_Drive_Main", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=root&cid=.*')),
                    #Outlook Mail
                    ("Outlook_Mail_Login", re.compile(r'https:\/\/login\.live\.com\/ppsecure\/post\.srf\?cobrandid=.*&uaid=.*&pid=.*&opid=.*&route=.*')),
                    ("Outlook_Mail_Sent", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/sentitems\?')),
                    ("Outlook_Mail_Drafts", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/drafts\?')),
                    ("Outlook_Mail_Trash", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/deleteditems\?')),
                    #Naver
                    ("Naver_Login", re.compile(r'https:\/\/nid\.naver\.com\/nidlogin\.login')),
                    #Naver Mail
                    ("Naver_Mail_Write_Session", re.compile(r'https:\/\/mail\.naver\.com\/write')),
                    ("Naver_Mail_Write", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new')),
                    ("Naver_Mail_Write_Done", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new\/done')),
                    ("Naver_Mail_Self_Sent", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new?\type=toMe')),
                    ("Naver_Mail_All_Mail", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/-1')),
                    ("Naver_Mail_Inbox", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/0')),
                    ("Naver_Mail_Sent", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/1')),
                    ("Naver_Mail_Receipt_Confirmation", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/2')),
                    ("Naver_Mail_Drafts", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/3')),
                    ("Naver_Mail_Trash", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/4')),
                    ("Naver_Mail_Self_Sent_Mailbox", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/6')),
                    #Naver Mybox
                    ("Naver_Mybox_Main", re.compile(r'https:\/\/mybox\.naver\.com\/#\/my')),
                    ("Naver_Mybox_Main", re.compile(r'^https:\/\/mybox\.naver\.com\/#\/$')),
                    ("Naver_Mybox_Recent_Update", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/update')),
                    ("Naver_Mybox_Recent_Access", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/access')),
                    ("Naver_Mybox_Protect", re.compile(r'https:\/\/mybox\.naver\.com\/#\/protect')),
                    ("Naver_Mybox_Shared", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/shared')),
                    ("Naver_Mybox_Sharing", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/sharing')),
                    #Naver Blog
                    ("Naver_Blog_Main", re.compile(r'https:\/\/blog\.naver\.com\/')),
                    ("Naver_Blog_Write", re.compile(r'https:\/\/blog\.naver\.com\/.*\?Redirect=Write')),
                    ("Naver_Blog_Write", re.compile(r'https:\/\/blog\.naver\.com\/.*\/postwrite')),
                    ("Naver_Blog_Issuance", re.compile(r'https:\/\/blog\.naver\.com\/PostView\.naver\?blogId=.*&Redirect=View&logNo=.*&categoryNo=.*&isAfterWrite=true&isMrblogPost=.*&isHappyBeanLeverage=.*&contentLength=.*')),
                    #Kakao Mail
                    ("Kakao_Mail_Login", re.compile(r'https:\/\/logins\.daum\.net\/accounts\/kakaossotokenlogin\.do\?redirect=true&ssotoken=.*&url=')),
                    ("Kakao_Mail_Inbox", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/INBOX$')),
                    ("Kakao_Mail_Sent", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/SENT$')),
                    ("Kakao_Mail_Trash", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/TRASH$')),
                    ("Kakao_Mail_Write", re.compile(r'https:\/\/mail\.kakao\.com\/top\/.*\?composer')),
                    #Daum
                    ("Daum_Mail_Login", re.compile(r'https:\/\/accounts\.kakao\.com\/weblogin\/sso_login\.html\?only=daum&continue=https%3A%2F%2Fmail\.daum\.net&type=ksso')),
                    ("Daum_Mail_Inbox", re.compile(r'^https:\/\/mail\.daum\.net\/top\/INBOX$')),
                    ("Daum_Mail_Write", re.compile(r'https:\/\/mail\.daum\.net\/top\/.*\?composer')),
                    ("Daum_Mail_Sent", re.compile(r'^https:\/\/mail\.daum\.net\/top\/SENT$')),
                    ("Daum_Mail_Draft", re.compile(r'^https:\/\/mail\.daum\.net\/top\/DRAFT$')),
                    ("Daum_Mail_Trash", re.compile(r'^https:\/\/mail\.daum\.net\/top\/TRASH$')),
                    #Nate
                    ("Nate_Mail_Write", re.compile(r'https:\/\/mail.*\.nate\.com\/#write\/\?act=new')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Nate_Mail_Inbox", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=10')),
                    ("Nate_Mail_Sent", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=30')),
                    ("Nate_Mail_Draft", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=40')),
                    ("Nate_Mail_Trash", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=1&mboxid=50')),
                    #Tistory
                    ("Tistory_Blog_Login", re.compile(r'https:\/\/www\.tistory\.com\/auth\/kakao\/redirect\?code=.*')),
                    ("Tistory_Blog_Manage", re.compile(r'https:\/\/.*\.tistory\.com\/manage\/.*')),
                    ("Tistory_Blog_Post", re.compile(r'https:\/\/.*\.tistory\.com\/manage\/newpost.*')),
                    ("Tistory_Blog_Post", re.compile(r'^https:\/\/.*\.tistory\.com\/manage\/post$')),
                    #Velog
                    ("Velog_Blog_Login", re.compile(r'https:\/\/velog\.io\/email-login\?code=.*')),
                    ("Velog_Blog_New_Post", re.compile(r'^https:\/\/velog\.io\/write$')),
                    ("Velog_Blog_Post", re.compile(r'https:\/\/velog\.io\/write\?id=.*')),
                    #ETC
                    ("File_Web_Access", re.compile(r'file:\/\/\/[A-Za-z]:\/(?:[^\/\n]+\/)*[^\/\n]+?\.[a-zA-Z0-9]+')),
                    ("Short_URL_Service", re.compile(r'\b(https?://)?(bit\.ly|tinyurl\.com|goo\.gl|t\.co|is\.gd|ow\.ly)/[a-zA-Z0-9]+\b')),
                    ("VPN_Service", re.compile(r'\b(vpn|secure|proxy|anon|connect)\.[a-zA-Z0-9.-]+\b')),
                    ("Use_Proxy_Server_PORT", re.compile(r':\b(8080|3128|8888|8000|8081|8118)\b')),
                    ("NAS_Quick_Connect_Server", re.compile(r'https:\/\/quickconnect\.to\/[a-zA-Z0-9]+(?:\/[^\s]*)?')),
                    ("NAS_C2_Synology_Server", re.compile(r'https:\/\/c2\.synology\.com\/[^\s]*')),
                    ("IP_Address_Server", re.compile(r'https:\/\/(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/[^\s]*'))
                    # 기타 URL 패턴 추가 가능
                ],
                "Title": [
                    ("Mega_Drive_File_Upload", re.compile(r'MEGA ↑ (100|[1-9]?[0-9])%'))
                ]
            },
            "Chrome_Web_Visits": {
                "Title": [
                    ("Web_Search", re.compile(r'(.*?\s-\s.*검색)'))             
                    # 기타 Title 패턴 추가 가능
                ],
                "URL": [
                    #Proton Mail 
                    ("Proton_Mail_Home_Page", re.compile(r'https:\/\/proton\.me\/mail')),
                    ("Proton_Mail_Login", re.compile(r'https:\/\/account\.proton.*')),
                    ("Proton_Mail_Login_Session", re.compile(r'https:\/\/mail\.proton\.me\/login#')),
                    ("Proton_Mail_Login_Session_Expired", re.compile(r'https:\/\/account\.proton\.me\/authorize\?app=proton-mail&state=.*reason=session-expired')),
                    ("Proton_Mail_Trash", re.compile(r'https:\/\/mail\.proton\.me.*trash')),
                    ("Proton_Mail_Archive", re.compile(r'https:\/\/mail\.proton\.me.*archive')),
                    ("Proton_Mail_All_Sent", re.compile(r'https:\/\/mail\.proton\.me.*all-sent')),
                    ("Proton_Mail_All_Drafts", re.compile(r'https:\/\/mail\.proton\.me.*all-drafts')),
                    ("Proton_Mail_Inbox", re.compile(r'https:\/\/mail\.proton\.me.*inbox')),
                    #Google
                    ("Google_Login_Service_Endpoint", re.compile(r'https:\/\/accounts\.google\.com\/ServiceLogin\?')),
                    ("Google_Login_Interactive_Endpoint", re.compile(r'https:\/\/accounts\.google\.com\/InteractiveLogin\?')),
                    ("Google_Redirection", re.compile(r'https:\/\/www\.google\.com\/url\?q=')),
                    #Gmail
                    ("Google_Mail_Inbox", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*ogbl\/\?pli=1$')),
                    ("Google_Mail_Inbox", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#inbox$')),
                    ("Google_Mail_Sent", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#sent$')),
                    ("Google_Mail_Drafts", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#drafts$')),
                    ("Google_Mail_trash", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#trash$')),
                    ("Google_Mail_Starred", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#starred$')),
                    ("Google_Mail_Open_Mail", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/[a-zA-Z]+$')),
                    ("Google_Mail_Mail_Write", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\?compose=.*$')),
                    ("Google_Mail_Drive_Sharing", re.compile(r'https:\/\/mail\.google\.com\/drivesharing.*?shareService=mail')),
                    ("Google_Mail_Create_New_mail", re.compile(r'https:\/\/mail\.google\.com\/.*\?compose=new')),
                    #Google Drive
                    ("Google_Drive_Main", re.compile(r'https:\/\/drive\.google\.com\/drive\/home')),
                    ("Google_Drive_My_Drive", re.compile(r'https:\/\/drive\.google\.com\/drive\/my-drive')),
                    ("Google_Drive_Folder", re.compile(r'https:\/\/drive\.google\.com\/drive\/folders')),
                    #Mega
                    ("Mega_Drive_Login", re.compile(r'https:\/\/mega\.nz\/login')),
                    ("Mega_Drive_Main", re.compile(r'https:\/\/mega\.nz\/fm')), #폴더를 들어가도 똑같음
                    #Dropbox
                    ("Dropbox_Drive_Drive", re.compile(r'^https:\/\/www\.dropbox\.com\/home$')),
                    ("Dropbox_Drive_Client_Login", re.compile(r'https:\/\/www\.dropbox\.com\/desktop\/oauth2\?code=.*&state=.*')),
                    #One Drive
                    ("One_Drive_Login", re.compile(r'https:\/\/onedrive\.live\.com\/login\/')),
                    ("One_Drive_Folder", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=.*&cid=.*')),
                    ("One_Drive_Main", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=root&cid=.*')),
                    #Outlook Mail
                    ("Outlook_Mail_Login", re.compile(r'https:\/\/login\.live\.com\/ppsecure\/post\.srf\?cobrandid=.*&uaid=.*&pid=.*&opid=.*&route=.*')),
                    ("Outlook_Mail_Sent", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/sentitems\?')),
                    ("Outlook_Mail_Drafts", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/drafts\?')),
                    ("Outlook_Mail_Trash", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/deleteditems\?')),
                    #Naver
                    ("Naver_Login", re.compile(r'https:\/\/nid\.naver\.com\/nidlogin\.login')),
                    #Naver Mail
                    ("Naver_Mail_Write_Session", re.compile(r'https:\/\/mail\.naver\.com\/write')),
                    ("Naver_Mail_Write", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new')),
                    ("Naver_Mail_Write_Done", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new\/done')),
                    ("Naver_Mail_Self_Sent", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new?\type=toMe')),
                    ("Naver_Mail_All_Mail", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/-1')),
                    ("Naver_Mail_Inbox", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/0')),
                    ("Naver_Mail_Sent", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/1')),
                    ("Naver_Mail_Receipt_Confirmation", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/2')),
                    ("Naver_Mail_Drafts", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/3')),
                    ("Naver_Mail_Trash", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/4')),
                    ("Naver_Mail_Self_Sent_Mailbox", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/6')),
                    #Naver Mybox
                    ("Naver_Mybox_Main", re.compile(r'https:\/\/mybox\.naver\.com\/#\/my')),
                    ("Naver_Mybox_Main", re.compile(r'^https:\/\/mybox\.naver\.com\/#\/$')),
                    ("Naver_Mybox_Recent_Update", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/update')),
                    ("Naver_Mybox_Recent_Access", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/access')),
                    ("Naver_Mybox_Protect", re.compile(r'https:\/\/mybox\.naver\.com\/#\/protect')),
                    ("Naver_Mybox_Shared", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/shared')),
                    ("Naver_Mybox_Sharing", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/sharing')),
                    #Naver Blog
                    ("Naver_Blog_Main", re.compile(r'https:\/\/blog\.naver\.com\/')),
                    ("Naver_Blog_Write", re.compile(r'https:\/\/blog\.naver\.com\/.*\?Redirect=Write')),
                    ("Naver_Blog_Write", re.compile(r'https:\/\/blog\.naver\.com\/.*\/postwrite')),
                    ("Naver_Blog_Issuance", re.compile(r'https:\/\/blog\.naver\.com\/PostView\.naver\?blogId=.*&Redirect=View&logNo=.*&categoryNo=.*&isAfterWrite=true&isMrblogPost=.*&isHappyBeanLeverage=.*&contentLength=.*')),
                    #Kakao Mail
                    ("Kakao_Mail_Login", re.compile(r'https:\/\/logins\.daum\.net\/accounts\/kakaossotokenlogin\.do\?redirect=true&ssotoken=.*&url=')),
                    ("Kakao_Mail_Inbox", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/INBOX$')),
                    ("Kakao_Mail_Sent", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/SENT$')),
                    ("Kakao_Mail_Trash", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/TRASH$')),
                    ("Kakao_Mail_Write", re.compile(r'https:\/\/mail\.kakao\.com\/top\/.*\?composer')),
                    #Daum
                    ("Daum_Mail_Login", re.compile(r'https:\/\/accounts\.kakao\.com\/weblogin\/sso_login\.html\?only=daum&continue=https%3A%2F%2Fmail\.daum\.net&type=ksso')),
                    ("Daum_Mail_Inbox", re.compile(r'^https:\/\/mail\.daum\.net\/top\/INBOX$')),
                    ("Daum_Mail_Write", re.compile(r'https:\/\/mail\.daum\.net\/top\/.*\?composer')),
                    ("Daum_Mail_Sent", re.compile(r'^https:\/\/mail\.daum\.net\/top\/SENT$')),
                    ("Daum_Mail_Draft", re.compile(r'^https:\/\/mail\.daum\.net\/top\/DRAFT$')),
                    ("Daum_Mail_Trash", re.compile(r'^https:\/\/mail\.daum\.net\/top\/TRASH$')),
                    #Nate
                    ("Nate_Mail_Write", re.compile(r'https:\/\/mail.*\.nate\.com\/#write\/\?act=new')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Nate_Mail_Inbox", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=10')),
                    ("Nate_Mail_Sent", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=30')),
                    ("Nate_Mail_Draft", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=40')),
                    ("Nate_Mail_Trash", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=1&mboxid=50')),
                    #Tistory
                    ("Tistory_Blog_Login", re.compile(r'https:\/\/www\.tistory\.com\/auth\/kakao\/redirect\?code=.*')),
                    ("Tistory_Blog_Manage", re.compile(r'https:\/\/.*\.tistory\.com\/manage\/.*')),
                    ("Tistory_Blog_Post", re.compile(r'https:\/\/.*\.tistory\.com\/manage\/newpost.*')),
                    ("Tistory_Blog_Post", re.compile(r'^https:\/\/.*\.tistory\.com\/manage\/post$')),
                    #Velog
                    ("Velog_Blog_Login", re.compile(r'https:\/\/velog\.io\/email-login\?code=.*')),
                    ("Velog_Blog_New_Post", re.compile(r'^https:\/\/velog\.io\/write$')),
                    ("Velog_Blog_Post", re.compile(r'https:\/\/velog\.io\/write\?id=.*')),
                    #ETC
                    ("File_Web_Access", re.compile(r'file:\/\/\/[A-Za-z]:\/(?:[^\/\n]+\/)*[^\/\n]+?\.[a-zA-Z0-9]+')),
                    ("Short_URL_Service", re.compile(r'\b(https?://)?(bit\.ly|tinyurl\.com|goo\.gl|t\.co|is\.gd|ow\.ly)/[a-zA-Z0-9]+\b')),
                    ("VPN_Service", re.compile(r'\b(vpn|secure|proxy|anon|connect)\.[a-zA-Z0-9.-]+\b')),
                    ("Use_Proxy_Server_PORT", re.compile(r':\b(8080|3128|8888|8000|8081|8118)\b')),
                    ("NAS_Quick_Connect_Server", re.compile(r'https:\/\/quickconnect\.to\/[a-zA-Z0-9]+(?:\/[^\s]*)?')),
                    ("NAS_C2_Synology_Server", re.compile(r'https:\/\/c2\.synology\.com\/[^\s]*')),
                    ("IP_Address_Server", re.compile(r'https:\/\/(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/[^\s]*'))
                    # 기타 URL 패턴 추가 가능
                ],
                "Title": [
                    ("Mega_Drive_File_Upload", re.compile(r'MEGA ↑ (100|[1-9]?[0-9])%'))
                ]
            },
            "Firefox_Web_Visits": {
                "Title": [
                    ("Web_Search", re.compile(r'(.*?\s-\s.*검색)'))             
                    # 기타 Title 패턴 추가 가능
                ],
                "URL": [
                    #Proton Mail 
                    ("Proton_Mail_Home_Page", re.compile(r'https:\/\/proton\.me\/mail')),
                    ("Proton_Mail_Login", re.compile(r'https:\/\/account\.proton.*')),
                    ("Proton_Mail_Login_Session", re.compile(r'https:\/\/mail\.proton\.me\/login#')),
                    ("Proton_Mail_Login_Session_Expired", re.compile(r'https:\/\/account\.proton\.me\/authorize\?app=proton-mail&state=.*reason=session-expired')),
                    ("Proton_Mail_Trash", re.compile(r'https:\/\/mail\.proton\.me.*trash')),
                    ("Proton_Mail_Archive", re.compile(r'https:\/\/mail\.proton\.me.*archive')),
                    ("Proton_Mail_All_Sent", re.compile(r'https:\/\/mail\.proton\.me.*all-sent')),
                    ("Proton_Mail_All_Drafts", re.compile(r'https:\/\/mail\.proton\.me.*all-drafts')),
                    ("Proton_Mail_Inbox", re.compile(r'https:\/\/mail\.proton\.me.*inbox')),
                    #Google
                    ("Google_Login_Service_Endpoint", re.compile(r'https:\/\/accounts\.google\.com\/ServiceLogin\?')),
                    ("Google_Login_Interactive_Endpoint", re.compile(r'https:\/\/accounts\.google\.com\/InteractiveLogin\?')),
                    ("Google_Redirection", re.compile(r'https:\/\/www\.google\.com\/url\?q=')),
                    #Gmail
                    ("Google_Mail_Inbox", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*ogbl\/\?pli=1$')),
                    ("Google_Mail_Inbox", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#inbox$')),
                    ("Google_Mail_Sent", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#sent$')),
                    ("Google_Mail_Drafts", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#drafts$')),
                    ("Google_Mail_trash", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#trash$')),
                    ("Google_Mail_Starred", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/#starred$')),
                    ("Google_Mail_Open_Mail", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\/[a-zA-Z]+$')),
                    ("Google_Mail_Mail_Write", re.compile(r'^https:\/\/mail\.google\.com\/mail\/.*\?compose=.*$')),
                    ("Google_Mail_Drive_Sharing", re.compile(r'https:\/\/mail\.google\.com\/drivesharing.*?shareService=mail')),
                    ("Google_Mail_Create_New_mail", re.compile(r'https:\/\/mail\.google\.com\/.*\?compose=new')),
                    #Google Drive
                    ("Google_Drive_Main", re.compile(r'https:\/\/drive\.google\.com\/drive\/home')),
                    ("Google_Drive_My_Drive", re.compile(r'https:\/\/drive\.google\.com\/drive\/my-drive')),
                    ("Google_Drive_Folder", re.compile(r'https:\/\/drive\.google\.com\/drive\/folders')),
                    #Mega
                    ("Mega_Drive_Login", re.compile(r'https:\/\/mega\.nz\/login')),
                    ("Mega_Drive_Main", re.compile(r'https:\/\/mega\.nz\/fm')), #폴더를 들어가도 똑같음
                    #Dropbox
                    ("Dropbox_Drive_Drive", re.compile(r'^https:\/\/www\.dropbox\.com\/home$')),
                    ("Dropbox_Drive_Client_Login", re.compile(r'https:\/\/www\.dropbox\.com\/desktop\/oauth2\?code=.*&state=.*')),
                    #One Drive
                    ("One_Drive_Login", re.compile(r'https:\/\/onedrive\.live\.com\/login\/')),
                    ("One_Drive_Folder", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=.*&cid=.*')),
                    ("One_Drive_Main", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=root&cid=.*')),
                    #Outlook Mail
                    ("Outlook_Mail_Login", re.compile(r'https:\/\/login\.live\.com\/ppsecure\/post\.srf\?cobrandid=.*&uaid=.*&pid=.*&opid=.*&route=.*')),
                    ("Outlook_Mail_Sent", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/sentitems\?')),
                    ("Outlook_Mail_Drafts", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/drafts\?')),
                    ("Outlook_Mail_Trash", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/deleteditems\?')),
                    #Naver
                    ("Naver_Login", re.compile(r'https:\/\/nid\.naver\.com\/nidlogin\.login')),
                    #Naver Mail
                    ("Naver_Mail_Write_Session", re.compile(r'https:\/\/mail\.naver\.com\/write')),
                    ("Naver_Mail_Write", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new')),
                    ("Naver_Mail_Write_Done", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new\/done')),
                    ("Naver_Mail_Self_Sent", re.compile(r'https:\/\/mail\.naver\.com\/.*\/new?\type=toMe')),
                    ("Naver_Mail_All_Mail", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/-1')),
                    ("Naver_Mail_Inbox", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/0')),
                    ("Naver_Mail_Sent", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/1')),
                    ("Naver_Mail_Receipt_Confirmation", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/2')),
                    ("Naver_Mail_Drafts", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/3')),
                    ("Naver_Mail_Trash", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/4')),
                    ("Naver_Mail_Self_Sent_Mailbox", re.compile(r'https:\/\/mail\.naver\.com\/.*\/folders\/6')),
                    #Naver Mybox
                    ("Naver_Mybox_Main", re.compile(r'https:\/\/mybox\.naver\.com\/#\/my')),
                    ("Naver_Mybox_Main", re.compile(r'^https:\/\/mybox\.naver\.com\/#\/$')),
                    ("Naver_Mybox_Recent_Update", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/update')),
                    ("Naver_Mybox_Recent_Access", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/access')),
                    ("Naver_Mybox_Protect", re.compile(r'https:\/\/mybox\.naver\.com\/#\/protect')),
                    ("Naver_Mybox_Shared", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/shared')),
                    ("Naver_Mybox_Sharing", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/sharing')),
                    #Naver Blog
                    ("Naver_Blog_Main", re.compile(r'https:\/\/blog\.naver\.com\/')),
                    ("Naver_Blog_Write", re.compile(r'https:\/\/blog\.naver\.com\/.*\?Redirect=Write')),
                    ("Naver_Blog_Write", re.compile(r'https:\/\/blog\.naver\.com\/.*\/postwrite')),
                    ("Naver_Blog_Issuance", re.compile(r'https:\/\/blog\.naver\.com\/PostView\.naver\?blogId=.*&Redirect=View&logNo=.*&categoryNo=.*&isAfterWrite=true&isMrblogPost=.*&isHappyBeanLeverage=.*&contentLength=.*')),
                    #Kakao Mail
                    ("Kakao_Mail_Login", re.compile(r'https:\/\/logins\.daum\.net\/accounts\/kakaossotokenlogin\.do\?redirect=true&ssotoken=.*&url=')),
                    ("Kakao_Mail_Inbox", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/INBOX$')),
                    ("Kakao_Mail_Sent", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/SENT$')),
                    ("Kakao_Mail_Trash", re.compile(r'^https:\/\/mail\.kakao\.com\/top\/TRASH$')),
                    ("Kakao_Mail_Write", re.compile(r'https:\/\/mail\.kakao\.com\/top\/.*\?composer')),
                    #Daum
                    ("Daum_Mail_Login", re.compile(r'https:\/\/accounts\.kakao\.com\/weblogin\/sso_login\.html\?only=daum&continue=https%3A%2F%2Fmail\.daum\.net&type=ksso')),
                    ("Daum_Mail_Inbox", re.compile(r'^https:\/\/mail\.daum\.net\/top\/INBOX$')),
                    ("Daum_Mail_Write", re.compile(r'https:\/\/mail\.daum\.net\/top\/.*\?composer')),
                    ("Daum_Mail_Sent", re.compile(r'^https:\/\/mail\.daum\.net\/top\/SENT$')),
                    ("Daum_Mail_Draft", re.compile(r'^https:\/\/mail\.daum\.net\/top\/DRAFT$')),
                    ("Daum_Mail_Trash", re.compile(r'^https:\/\/mail\.daum\.net\/top\/TRASH$')),
                    #Nate
                    ("Nate_Mail_Write", re.compile(r'https:\/\/mail.*\.nate\.com\/#write\/\?act=new')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Nate_Mail_Inbox", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=10')),
                    ("Nate_Mail_Sent", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=30')),
                    ("Nate_Mail_Draft", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=.*&mboxid=40')),
                    ("Nate_Mail_Trash", re.compile(r'https:\/\/mail3\.nate\.com\/#list\/\?pop3id=M&page=1&mboxid=50')),
                    #Tistory
                    ("Tistory_Blog_Login", re.compile(r'https:\/\/www\.tistory\.com\/auth\/kakao\/redirect\?code=.*')),
                    ("Tistory_Blog_Manage", re.compile(r'https:\/\/.*\.tistory\.com\/manage\/.*')),
                    ("Tistory_Blog_Post", re.compile(r'https:\/\/.*\.tistory\.com\/manage\/newpost.*')),
                    ("Tistory_Blog_Post", re.compile(r'^https:\/\/.*\.tistory\.com\/manage\/post$')),
                    #Velog
                    ("Velog_Blog_Login", re.compile(r'https:\/\/velog\.io\/email-login\?code=.*')),
                    ("Velog_Blog_New_Post", re.compile(r'^https:\/\/velog\.io\/write$')),
                    ("Velog_Blog_Post", re.compile(r'https:\/\/velog\.io\/write\?id=.*')),
                    #ETC
                    ("File_Web_Access", re.compile(r'file:\/\/\/[A-Za-z]:\/(?:[^\/\n]+\/)*[^\/\n]+?\.[a-zA-Z0-9]+')),
                    ("Short_URL_Service", re.compile(r'\b(https?://)?(bit\.ly|tinyurl\.com|goo\.gl|t\.co|is\.gd|ow\.ly)/[a-zA-Z0-9]+\b')),
                    ("VPN_Service", re.compile(r'\b(vpn|secure|proxy|anon|connect)\.[a-zA-Z0-9.-]+\b')),
                    ("Use_Proxy_Server_PORT", re.compile(r':\b(8080|3128|8888|8000|8081|8118)\b')),
                    ("NAS_Quick_Connect_Server", re.compile(r'https:\/\/quickconnect\.to\/[a-zA-Z0-9]+(?:\/[^\s]*)?')),
                    ("NAS_C2_Synology_Server", re.compile(r'https:\/\/c2\.synology\.com\/[^\s]*')),
                    ("IP_Address_Server", re.compile(r'https:\/\/(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/[^\s]*'))
                    # 기타 URL 패턴 추가 가능
                ],
                "Title": [
                    ("Mega_Drive_File_Upload", re.compile(r'MEGA ↑ (100|[1-9]?[0-9])%'))
                ]
            },
            "USB_Devices": {
                "Manufacturer": [
                    ("User_USB", re.compile(r'.*?\(Standard disk drives\)'))
                    # USB 장치 제조사와 관련된 추가 패턴 가능
                ]
            },
            "Recycle_Bin": {
                "artifact_name": [
                    ("File_Remove", re.compile(r'Recycle\sBin'))
                    # 기타 Recycle Bin 관련 패턴 추가 가능
                ]
            },
            "Edge_Chromium_Downloads": {
                "File_Name": [
                    ("Web_PDF_Download", re.compile(r'.*?\.pdf')),
                    ("Web_EXE_Download", re.compile(r'.*?\.exe')),
                    ("Web_HWP_Download", re.compile(r'.*?\.hwp')),
                    ("Web_DOC_Download", re.compile(r'.*?\.doc')),
                    ("Web_DOCS_Download", re.compile(r'.*?\.docs'))
                    # 다운로드된 파일 형식에 대한 추가 패턴 가능
                ]
            },
            "Chrome_Downloads": {
                "File_Name": [
                    ("Web_PDF_Download", re.compile(r'.*?\.pdf')),
                    ("Web_EXE_Download", re.compile(r'.*?\.exe')),
                    ("Web_HWP_Download", re.compile(r'.*?\.hwp')),
                    ("Web_DOC_Download", re.compile(r'.*?\.doc')),
                    ("Web_DOCS_Download", re.compile(r'.*?\.docs'))
                    # 다운로드된 파일 형식에 대한 추가 패턴 가능
                ]
            },
            "Chrome_Cache_Records": {
                "URL": [
                    ("Google_Drive_Upload", re.compile(r'https:\/\/drive\.google\.com.*upload')),
                    ("Naver_Mybox_File_Get_Folder", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=.*')),
                    ("Naver_Mybox_File_Get_Root", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=root')),
                    ("Naver_Blog_File_Upload", re.compile(r'https:\/\/editor-static\.pstatic\.net\/e\/basic\.desktop\/.*\/se-file-upload-layer-view\.js\?')), #직접 업로드만
                    ("Naver_Blog_Image_Upload", re.compile(r'https:\/\/blogfiles\.pstatic\.net\/')), #블로그에 포함된 여러 이미지파일들의 중복 가능성 있어서 메일 작성 후 시간대로 묶어야할듯
                    ("Tistory_Blog_File_Upload", re.compile(r'.*https:\/\/tistory\.com.*plugins\/fileUpload\/plugin\.min\.js')),
                    ("Google_Mail_File_Upload", re.compile(r'https:\/\/ssl\.gstatic\.com\/ui\/v1\/icons\/common\/x_8px\.png')),
                    ("Nate_Mail_File_Upload", re.compile(r'https:\/\/mailimg\.nate\.com\/newmail\/img\/jsfile\/mimetypes\/.*\.png')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/images\/mega\/overlay-sprite\.png\?v=bf2e646f2f83e139')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/imagery\/sprites-fm-mime-uni\.9f5adb6010bae3ce\.svg')),
                    ("One_Drive_Upload", re.compile(r'https:\/\/res-1\.cdn\.office\.net\/files\/.*\.manifest\/76\.js')),
                    ("Velog_Blog_File_Upload", re.compile(r'https:\/\/velog\.velcdn\.com\/.*\/post\/.*\/image\..*')),
                    ("Dropbox_Drive_File_Upload", re.compile(r'https:\/\/previews\.dropbox\.com\/p\/.*_img\/.*'))                                        
                    # 기타 캐시 기록 관련 URL 패턴 추가 가능
                ]
            },
            "Edge_Chromium_Cache_Records": {
                "URL": [
                    ("Google_Drive_Upload", re.compile(r'https:\/\/drive\.google\.com.*upload')),
                    ("Naver_Mybox_File_Get_Folder", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=.*')),
                    ("Naver_Mybox_File_Get_Root", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=root')),
                    ("Naver_Blog_File_Upload", re.compile(r'https:\/\/editor-static\.pstatic\.net\/e\/basic\.desktop\/.*\/se-file-upload-layer-view\.js\?')), #직접 업로드만
                    ("Naver_Blog_Image_Upload", re.compile(r'https:\/\/blogfiles\.pstatic\.net\/')), #블로그에 포함된 여러 이미지파일들의 중복 가능성 있어서 메일 작성 후 시간대로 묶어야할듯
                    ("Tistory_Blog_File_Upload", re.compile(r'.*https:\/\/tistory\.com.*plugins\/fileUpload\/plugin\.min\.js')),
                    ("Google_Mail_File_Upload", re.compile(r'https:\/\/ssl\.gstatic\.com\/ui\/v1\/icons\/common\/x_8px\.png')),
                    ("Nate_Mail_File_Upload", re.compile(r'https:\/\/mailimg\.nate\.com\/newmail\/img\/jsfile\/mimetypes\/.*\.png')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/images\/mega\/overlay-sprite\.png\?v=bf2e646f2f83e139')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/imagery\/sprites-fm-mime-uni\.9f5adb6010bae3ce\.svg')),
                    ("One_Drive_Upload", re.compile(r'https:\/\/res-1\.cdn\.office\.net\/files\/.*\.manifest\/76\.js')),
                    ("Velog_Blog_File_Upload", re.compile(r'https:\/\/velog\.velcdn\.com\/.*\/post\/.*\/image\..*')),
                    ("Dropbox_Drive_File_Upload", re.compile(r'https:\/\/previews\.dropbox\.com\/p\/.*_img\/.*'))                                        
                    # 기타 캐시 기록 관련 URL 패턴 추가 가능
                ]
            },
            "Firefox_Cache_Records": {
                "URL": [
                    ("Google_Drive_Upload", re.compile(r'https:\/\/drive\.google\.com.*upload')),
                    ("Naver_Mybox_File_Get_Folder", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=.*')),
                    ("Naver_Mybox_File_Get_Root", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=root')),
                    ("Naver_Blog_File_Upload", re.compile(r'https:\/\/editor-static\.pstatic\.net\/e\/basic\.desktop\/.*\/se-file-upload-layer-view\.js\?')), #직접 업로드만
                    ("Naver_Blog_Image_Upload", re.compile(r'https:\/\/blogfiles\.pstatic\.net\/')), #블로그에 포함된 여러 이미지파일들의 중복 가능성 있어서 메일 작성 후 시간대로 묶어야할듯
                    ("Tistory_Blog_File_Upload", re.compile(r'.*https:\/\/tistory\.com.*plugins\/fileUpload\/plugin\.min\.js')),
                    ("Google_Mail_File_Upload", re.compile(r'https:\/\/ssl\.gstatic\.com\/ui\/v1\/icons\/common\/x_8px\.png')),
                    ("Nate_Mail_File_Upload", re.compile(r'https:\/\/mailimg\.nate\.com\/newmail\/img\/jsfile\/mimetypes\/.*\.png')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/images\/mega\/overlay-sprite\.png\?v=bf2e646f2f83e139')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/imagery\/sprites-fm-mime-uni\.9f5adb6010bae3ce\.svg')),
                    ("One_Drive_Upload", re.compile(r'https:\/\/res-1\.cdn\.office\.net\/files\/.*\.manifest\/76\.js')),
                    ("Velog_Blog_File_Upload", re.compile(r'https:\/\/velog\.velcdn\.com\/.*\/post\/.*\/image\..*')),
                    ("Dropbox_Drive_File_Upload", re.compile(r'https:\/\/previews\.dropbox\.com\/p\/.*_img\/.*'))                                        
                    # 기타 캐시 기록 관련 URL 패턴 추가 가능
                ]
            },
            "Edge_Chromium_Last_Session": {
                "Title": [
                    ("Google_Login", re.compile(r'로그인\s-\sGoogle\s계정')),
                    ("Google_Mail_Inbox", re.compile(r'Inbox\s\(\d+\)\s-\s.*@gmail\.com')),
                    ("Google_Mail_Sent", re.compile(r'(Sent\sMail)\s-\s.*@gmail\.com')),
                    ("Google_Mail_Subject", re.compile(r'.*\s-\s.*@gmail\.com')),
                    ("Web_Search", re.compile(r'(.*?\s-\s.*검색)'))
                ],
                "Redirect_URL": [
                    ("Google_Redirection", re.compile(r'https:\/\/www\.google\.com\/url\?q='))
                ]
            },
            "Edge_Chromium_Current_Session": {
                "Title": [
                    ("Google_Login", re.compile(r'로그인\s-\sGoogle\s계정')),
                    ("Google_Mail_Inbox", re.compile(r'Inbox\s\(\d+\)\s-\s.*@gmail\.com')),
                    ("Google_Mail_Sent", re.compile(r'(Sent\sMail)\s-\s.*@gmail\.com')),
                    ("Google_Mail_Subject", re.compile(r'.*\s-\s.*@gmail\.com')),
                    ("Web_Search", re.compile(r'(.*?\s-\s.*검색)'))
                ],
                "Redirect_URL": [
                    ("Google_Redirection", re.compile(r'https:\/\/www\.google\.com\/url\?q='))
                ]
            },
            "MRU_Recent_Files_&_Folders": {
                "File/Folder_Name": [
                    ("MRU_File_PDF", re.compile(r'.*?\.pdf')),
                    ("MRU_Recent_Folder", re.compile(r''))
                ]
            },
            "MRU_Opened/Saved_Files": {
                "File_Name": [
                    ("MRU_File_PDF", re.compile(r'.*?\.pdf'))
                ]
            },
            "MRU_Folder_Access": {
                "Application_Name": [
                    ("MRU_Folder_Access_Chrome", re.compile(r'chrome\.exe'))
                ]
            }
        }

    def tag_log(self, df, column_name, column_patterns):
        for tag, pattern in column_patterns:
            df.loc[df[column_name].str.contains(pattern, na=False), '_TAG_'] = tag

    def process_table(self, table_name):
        try:
            # 단일 connection 컨텍스트에서 모든 작업 수행
            with self.engine.connect() as conn:
                # 데이터 조회
                query = text(f"SELECT * FROM `{table_name}`")
                print(query)
                try :
                    result = conn.execute(query)
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())
                    
                    if df.empty:
                        print(f"'{table_name}' 테이블이 비어 있습니다. 넘어갑니다.")
                        return

                    if '_TAG_' not in df.columns:
                        df['_TAG_'] = None

                    # 태그 처리
                    if table_name in self.patterns:
                        for column_name, column_patterns in self.patterns[table_name].items():
                            if column_name in df.columns:
                                self.tag_log(df, column_name, column_patterns)

                        # 결과 저장
                        # 기존 테이블 삭제
                        conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
                        conn.commit()  # 변경사항 커밋
                        
                        # 새로운 데이터 저장
                        df.to_sql(table_name, self.engine, if_exists='replace', index=False)
                        print(f"{table_name} 테이블에 태그가 추가되었습니다.")
                    else:
                        print(f"{table_name} 테이블에 대한 패턴이 정의되지 않았습니다.")
                except :
                    pass
                
        except Exception as e:
            print(f"Error processing table {table_name}: {str(e)}")
            raise  # 에러를 상위로 전파하여 디버깅 용이하게

    def apply_tags(self):
        for table_name in self.patterns:
            self.process_table(table_name)

class LogTaggerManager:
    def __init__(self, db_url):
        self.tagger_classes = {
            "1": ("기본 태깅", LogTagger)
        }
        self.db_url = db_url

    def run_tagger(self):
        """ 선택한 태거 클래스의 태깅 작업을 수행 """
        tagger_info = self.tagger_classes.get("1")
        if tagger_info is None:
            print("유효하지 않은 선택입니다. 다시 시도하세요.")
            return

        _, tagger_class = tagger_info
        tagger_instance = tagger_class(self.db_url)
        tagger_instance.apply_tags()
        print(f'DB path : {self.db_url} 에 적용되었습니다.')