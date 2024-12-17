import json
import datetime
import re
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.exc import OperationalError
import sys
import urllib.parse

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
                    ("OneDrive_Drive_Login", re.compile(r'https:\/\/onedrive\.live\.com\/login\/')),
                    ("OneDrive_Drive_Folder", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=.*&cid=.*')),
                    ("OneDrive_Drive_Main", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=root&cid=.*')),
                    #Outlook Mail
                    ("Outlook_Mail_Login", re.compile(r'https:\/\/login\.live\.com\/ppsecure\/post\.srf\?cobrandid=.*&uaid=.*&pid=.*&opid=.*&route=.*')),
                    ("Outlook_Mail_Sent", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/sentitems\?')),
                    ("Outlook_Mail_Drafts", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/drafts\?')),
                    ("Outlook_Mail_Trash", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/deleteditems\?')),
                    #Naver
                    ("Naver_Login", re.compile(r'https:\/\/nid\.naver\.com\/nidlogin\.login')),
                    #Naver Mail
                    ("Naver_Mail_Read", re.compile(r'https:\/\/mail\.naver\.com.*read')),
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
                    ("Mybox_Drive_Main", re.compile(r'https:\/\/mybox\.naver\.com\/#\/my')),
                    ("Mybox_Drive_Main", re.compile(r'^https:\/\/mybox\.naver\.com\/#\/$')),
                    ("Mybox_Drive_Recent_Update", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/update')),
                    ("Mybox_Drive_Recent_Access", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/access')),
                    ("Mybox_Drive_Protect", re.compile(r'https:\/\/mybox\.naver\.com\/#\/protect')),
                    ("Mybox_Drive_Shared", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/shared')),
                    ("Mybox_Drive_Sharing", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/sharing')),
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
                    #Nas
                    ("Nas_Drive_Action", re.compile(r'https:\/\/nas')),
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
                    ("OneDrive_Drive_Login", re.compile(r'https:\/\/onedrive\.live\.com\/login\/')),
                    ("OneDrive_Drive_Folder", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=.*&cid=.*')),
                    ("OneDrive_Drive_Main", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=root&cid=.*')),
                    #Outlook Mail
                    ("Outlook_Mail_Login", re.compile(r'https:\/\/login\.live\.com\/ppsecure\/post\.srf\?cobrandid=.*&uaid=.*&pid=.*&opid=.*&route=.*')),
                    ("Outlook_Mail_Sent", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/sentitems\?')),
                    ("Outlook_Mail_Drafts", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/drafts\?')),
                    ("Outlook_Mail_Trash", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/deleteditems\?')),
                    #Naver
                    ("Naver_Login", re.compile(r'https:\/\/nid\.naver\.com\/nidlogin\.login')),
                    #Naver Mail
                    ("Naver_Mail_Read", re.compile(r'https:\/\/mail\.naver\.com.*read')),
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
                    ("Mybox_Drive_Main", re.compile(r'https:\/\/mybox\.naver\.com\/#\/my')),
                    ("Mybox_Drive_Main", re.compile(r'^https:\/\/mybox\.naver\.com\/#\/$')),
                    ("Mybox_Drive_Recent_Update", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/update')),
                    ("Mybox_Drive_Recent_Access", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/access')),
                    ("Mybox_Drive_Protect", re.compile(r'https:\/\/mybox\.naver\.com\/#\/protect')),
                    ("Mybox_Drive_Shared", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/shared')),
                    ("Mybox_Drive_Sharing", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/sharing')),
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
                    #Nas
                    ("Nas_Drive_Action", re.compile(r'https:\/\/nas')),
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
                    ("OneDrive_Drive_Login", re.compile(r'https:\/\/onedrive\.live\.com\/login\/')),
                    ("OneDrive_Drive_Folder", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=.*&cid=.*')),
                    ("OneDrive_Drive_Main", re.compile(r'https:\/\/onedrive\.live\.com\/\?id=root&cid=.*')),
                    #Outlook Mail
                    ("Outlook_Mail_Login", re.compile(r'https:\/\/login\.live\.com\/ppsecure\/post\.srf\?cobrandid=.*&uaid=.*&pid=.*&opid=.*&route=.*')),
                    ("Outlook_Mail_Sent", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/sentitems\?')),
                    ("Outlook_Mail_Drafts", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/drafts\?')),
                    ("Outlook_Mail_Trash", re.compile(r'https:\/\/outlook\.live\.com\/mail\/.*\/deleteditems\?')),
                    #Naver
                    ("Naver_Login", re.compile(r'https:\/\/nid\.naver\.com\/nidlogin\.login')),
                    #Naver Mail
                    ("Naver_Mail_Read", re.compile(r'https:\/\/mail\.naver\.com.*read')),
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
                    ("Mybox_Drive_Main", re.compile(r'https:\/\/mybox\.naver\.com\/#\/my')),
                    ("Mybox_Drive_Main", re.compile(r'^https:\/\/mybox\.naver\.com\/#\/$')),
                    ("Mybox_Drive_Recent_Update", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/update')),
                    ("Mybox_Drive_Recent_Access", re.compile(r'https:\/\/mybox\.naver\.com\/#\/recent\/access')),
                    ("Mybox_Drive_Protect", re.compile(r'https:\/\/mybox\.naver\.com\/#\/protect')),
                    ("Mybox_Drive_Shared", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/shared')),
                    ("Mybox_Drive_Sharing", re.compile(r'https:\/\/mybox\.naver\.com\/#\/share\/sharing')),
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
                    #Nas
                    ("Nas_Drive_Action", re.compile(r'https:\/\/nas')),
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
                    ("Mybox_Drive_File_Get_Folder", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=.*')),
                    ("Mybox_Drive_File_Get_Root", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=root')),
                    ("Naver_Blog_File_Upload", re.compile(r'https:\/\/editor-static\.pstatic\.net\/e\/basic\.desktop\/.*\/se-file-upload-layer-view\.js\?')), #직접 업로드만
                    ("Naver_Blog_Image_Upload", re.compile(r'https:\/\/blogfiles\.pstatic\.net\/')), #블로그에 포함된 여러 이미지파일들의 중복 가능성 있어서 메일 작성 후 시간대로 묶어야할듯
                    ("Tistory_Blog_File_Upload", re.compile(r'.*https:\/\/tistory\.com.*plugins\/fileUpload\/plugin\.min\.js')),
                    ("Google_Mail_File_Upload", re.compile(r'https:\/\/ssl\.gstatic\.com\/ui\/v1\/icons\/common\/x_8px\.png')),
                    ("Nate_Mail_File_Upload", re.compile(r'https:\/\/mailimg\.nate\.com\/newmail\/img\/jsfile\/mimetypes\/.*\.png')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/images\/mega\/overlay-sprite\.png\?v=bf2e646f2f83e139')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/imagery\/sprites-fm-mime-uni\.9f5adb6010bae3ce\.svg')),
                    ("OneDrive_Drive_Upload", re.compile(r'https:\/\/res-1\.cdn\.office\.net\/files\/.*\.manifest\/76\.js')),
                    ("Velog_Blog_File_Upload", re.compile(r'https:\/\/velog\.velcdn\.com\/.*\/post\/.*\/image\..*')),
                    ("Dropbox_Drive_File_Upload", re.compile(r'https:\/\/previews\.dropbox\.com\/p\/.*_img\/.*'))                                        
                    # 기타 캐시 기록 관련 URL 패턴 추가 가능
                ]
            },
            "Edge_Chromium_Cache_Records": {
                "URL": [
                    ("Google_Drive_Upload", re.compile(r'https:\/\/drive\.google\.com.*upload')),
                    ("Mybox_Drive_File_Get_Folder", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=.*')),
                    ("Mybox_Drive_File_Get_Root", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=root')),
                    ("Naver_Blog_File_Upload", re.compile(r'https:\/\/editor-static\.pstatic\.net\/e\/basic\.desktop\/.*\/se-file-upload-layer-view\.js\?')), #직접 업로드만
                    ("Naver_Blog_Image_Upload", re.compile(r'https:\/\/blogfiles\.pstatic\.net\/')), #블로그에 포함된 여러 이미지파일들의 중복 가능성 있어서 메일 작성 후 시간대로 묶어야할듯
                    ("Tistory_Blog_File_Upload", re.compile(r'.*https:\/\/tistory\.com.*plugins\/fileUpload\/plugin\.min\.js')),
                    ("Google_Mail_File_Upload", re.compile(r'https:\/\/ssl\.gstatic\.com\/ui\/v1\/icons\/common\/x_8px\.png')),
                    ("Nate_Mail_File_Upload", re.compile(r'https:\/\/mailimg\.nate\.com\/newmail\/img\/jsfile\/mimetypes\/.*\.png')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/images\/mega\/overlay-sprite\.png\?v=bf2e646f2f83e139')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/imagery\/sprites-fm-mime-uni\.9f5adb6010bae3ce\.svg')),
                    ("OneDrive_Drive_Upload", re.compile(r'https:\/\/res-1\.cdn\.office\.net\/files\/.*\.manifest\/76\.js')),
                    ("Velog_Blog_File_Upload", re.compile(r'https:\/\/velog\.velcdn\.com\/.*\/post\/.*\/image\..*')),
                    ("Dropbox_Drive_File_Upload", re.compile(r'https:\/\/previews\.dropbox\.com\/p\/.*_img\/.*'))                                        
                    # 기타 캐시 기록 관련 URL 패턴 추가 가능
                ]
            },
            "Firefox_Cache_Records": {
                "URL": [
                    ("Google_Drive_Upload", re.compile(r'https:\/\/drive\.google\.com.*upload')),
                    ("Mybox_Drive_File_Get_Folder", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=.*')),
                    ("Mybox_Drive_File_Get_Root", re.compile(r'https:\/\/api\.mybox\.naver\.com\/service.*\/file\/get\?resourceKey=root')),
                    ("Naver_Blog_File_Upload", re.compile(r'https:\/\/editor-static\.pstatic\.net\/e\/basic\.desktop\/.*\/se-file-upload-layer-view\.js\?')), #직접 업로드만
                    ("Naver_Blog_Image_Upload", re.compile(r'https:\/\/blogfiles\.pstatic\.net\/')), #블로그에 포함된 여러 이미지파일들의 중복 가능성 있어서 메일 작성 후 시간대로 묶어야할듯
                    ("Tistory_Blog_File_Upload", re.compile(r'.*https:\/\/tistory\.com.*plugins\/fileUpload\/plugin\.min\.js')),
                    ("Google_Mail_File_Upload", re.compile(r'https:\/\/ssl\.gstatic\.com\/ui\/v1\/icons\/common\/x_8px\.png')),
                    ("Nate_Mail_File_Upload", re.compile(r'https:\/\/mailimg\.nate\.com\/newmail\/img\/jsfile\/mimetypes\/.*\.png')),
                    ("Nate_Mail_Sent_Complete", re.compile(r'https:\/\/mail3\.nate\.com\/#write\/\?act=new')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/images\/mega\/overlay-sprite\.png\?v=bf2e646f2f83e139')),
                    ("Mega_Drive_Upload", re.compile(r'https:\/\/jp\.static\.mega\.co\.nz\/4\/imagery\/sprites-fm-mime-uni\.9f5adb6010bae3ce\.svg')),
                    ("OneDrive_Drive_Upload", re.compile(r'https:\/\/res-1\.cdn\.office\.net\/files\/.*\.manifest\/76\.js')),
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
            df = pd.read_sql_table(table_name, self.engine)
            if df.empty:
                print(f"'{table_name}' 테이블이 비어 있습니다. 넘어갑니다.")
                return

        except (NoSuchTableError, ValueError):
            print(f"'{table_name}' 테이블을 찾을 수 없습니다. 넘어갑니다.")
            return

        if '_TAG_' not in df.columns:
            df['_TAG_'] = None

        for column_name, column_patterns in self.patterns[table_name].items():
            if column_name in df.columns:
                self.tag_log(df, column_name, column_patterns)

        df.to_sql(table_name, self.engine, if_exists='replace', index=False)
        print(f"{table_name} 테이블에 태그가 추가되었습니다.")

    def apply_tags(self):
        for table_name in self.patterns:
            self.process_table(table_name)

class LogTagger_1:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
    
    def parse_datetime(self, dt_str):
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_gmail_subjects(self):
        query = "SELECT * FROM Edge_Chromium_Web_Visits WHERE _TAG_ = 'Gmail_Subject'"
        gmail_logs = pd.read_sql_query(query, self.engine)
        return gmail_logs

    def find_web_pdf_downloads(self):
        query = "SELECT * FROM Edge_Chromium_Downloads WHERE _TAG_ = 'Web_PDF_Download'"
        pdf_logs = pd.read_sql_query(query, self.engine)
        return pdf_logs

    def group_email_to_pdf_downloads(self):
        gmail_logs = self.find_gmail_subjects()
        pdf_logs = self.find_web_pdf_downloads()
        
        gmail_logs['timestamp'] = gmail_logs['Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'].apply(self.parse_datetime)
        pdf_logs['timestamp'] = pdf_logs['Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)'].apply(self.parse_datetime)
        logs = pd.concat([gmail_logs, pdf_logs], ignore_index=True).sort_values(by='timestamp')

        grouped_downloads = []
        current_gmail_log = None

        for _, log in logs.iterrows():
            if log['_TAG_'] == 'Gmail_Subject':
                current_gmail_log = log
            elif log['_TAG_'] == 'Web_PDF_Download' and current_gmail_log is not None:
                gmail_log_dict = current_gmail_log.to_dict()
                pdf_log_dict = log.to_dict()

                # Timestamp를 문자열로 변환
                gmail_log_dict['timestamp'] = gmail_log_dict['timestamp'].isoformat() if gmail_log_dict['timestamp'] else None
                pdf_log_dict['timestamp'] = pdf_log_dict['timestamp'].isoformat() if pdf_log_dict['timestamp'] else None

                grouped_downloads.append({
                    'gmail_log': gmail_log_dict,
                    'pdf_log': pdf_log_dict
                })
                current_gmail_log = None

        return grouped_downloads

    def apply_tags(self):
        grouped_logs = self.group_email_to_pdf_downloads()
        if grouped_logs:
            print("Gmail_Subject 이후의 Web_PDF_Download 그룹화 결과:")
            print(json.dumps(grouped_logs, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

class LogTagger_1_1:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
    
    def parse_datetime(self, dt_str):
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_gmail_new_mail(self):
        """ 모든 'Gmail_Create_New_mail' 태그를 가진 데이터프레임 반환 """
        query = "SELECT * FROM Edge_Chromium_Web_Visits WHERE _TAG_ = 'Gmail_Create_New_mail'"
        gmail_logs = pd.read_sql_query(query, self.engine)
        return gmail_logs

    def find_gmail_drive_sharing(self):
        """ 모든 'Gmail_Drive_Sharing' 태그를 가진 데이터프레임 반환 """
        query = "SELECT * FROM Edge_Chromium_Web_Visits WHERE _TAG_ = 'Gmail_Drive_Sharing'"
        drive_sharing_logs = pd.read_sql_query(query, self.engine)
        return drive_sharing_logs

    def group_gmail_to_drive_sharing(self):
        """ Gmail_Create_New_mail과 Gmail_Drive_Sharing을 시간순으로 그룹화 """
        
        # 두 종류의 태그 로그 데이터를 불러옴
        gmail_logs = self.find_gmail_new_mail()
        drive_sharing_logs = self.find_gmail_drive_sharing()
        
        # 각 로그에 timestamp 컬럼을 추가하고 병합하여 정렬
        gmail_logs['timestamp'] = gmail_logs['Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'].apply(self.parse_datetime)
        drive_sharing_logs['timestamp'] = drive_sharing_logs['Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'].apply(self.parse_datetime)
        logs = pd.concat([gmail_logs, drive_sharing_logs], ignore_index=True).sort_values(by='timestamp')

        grouped_logs = []
        current_gmail_log = None

        for _, log in logs.iterrows():
            if log['_TAG_'] == 'Gmail_Create_New_mail':
                current_gmail_log = log
            elif log['_TAG_'] == 'Gmail_Drive_Sharing' and current_gmail_log is not None:
                gmail_log_dict = current_gmail_log.to_dict()
                drive_sharing_log_dict = log.to_dict()

                # Timestamp를 문자열로 변환
                gmail_log_dict['timestamp'] = gmail_log_dict['timestamp'].isoformat() if gmail_log_dict['timestamp'] else None
                drive_sharing_log_dict['timestamp'] = drive_sharing_log_dict['timestamp'].isoformat() if drive_sharing_log_dict['timestamp'] else None

                grouped_logs.append({
                    'gmail_log': gmail_log_dict,
                    'drive_sharing_log': drive_sharing_log_dict
                })
                current_gmail_log = None

        return grouped_logs

    def apply_tags(self):
        """ 그룹화된 결과 출력 """
        grouped_logs = self.group_gmail_to_drive_sharing()
        if grouped_logs:
            print("Gmail_Create_New_mail 이후의 Gmail_Drive_Sharing 그룹화 결과:")
            print(json.dumps(grouped_logs, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

class LogTagger_1_2:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
    
    def parse_datetime(self, dt_str):
        """문자열 형식의 날짜/시간을 datetime 객체로 변환"""
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_gmail_subjects(self):
        """모든 'Gmail_Subject' 태그를 가진 데이터프레임 반환"""
        try:
            query = "SELECT * FROM Edge_Chromium_Web_Visits WHERE _TAG_ = 'Gmail_Subject'"
            gmail_logs = pd.read_sql_query(query, self.engine)
            if 'Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)' not in gmail_logs.columns:
                print("Edge_Chromium_Web_Visits 테이블에 필요한 컬럼이 없습니다. 실행을 종료합니다.")
                sys.exit(1)
            return gmail_logs
        except OperationalError:
            print("Edge_Chromium_Web_Visits 테이블이 존재하지 않습니다. 실행을 종료합니다.")
            sys.exit(1)

    def find_google_redirection(self):
        """모든 'Google_Redirection' 태그를 가진 데이터프레임 반환"""
        try:
            query = "SELECT * FROM Edge_Chromium_Last_Session WHERE _TAG_ = 'Google_Redirection'"
            redirection_logs = pd.read_sql_query(query, self.engine)
            if 'Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)' not in redirection_logs.columns:
                print("Edge_Chromium_Last_Session 테이블에 필요한 컬럼이 없습니다. 실행을 종료합니다.")
                sys.exit(1)
            return redirection_logs
        except OperationalError:
            print("Edge_Chromium_Last_Session 테이블이 존재하지 않습니다. 실행을 종료합니다.")
            sys.exit(1)

    def group_gmail_to_redirection(self):
        """시간순으로 Gmail_Subject와 Google_Redirection을 순차적으로 그룹화하는 함수"""
        
        # 필요한 로그 데이터 불러오기
        gmail_logs = self.find_gmail_subjects()
        redirection_logs = self.find_google_redirection()
        
        # 각 로그에 timestamp 컬럼을 추가하고 병합하여 시간순 정렬
        gmail_logs['timestamp'] = gmail_logs['Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'].apply(self.parse_datetime)
        redirection_logs['timestamp'] = redirection_logs['Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'].apply(self.parse_datetime)
        logs = pd.concat([gmail_logs, redirection_logs], ignore_index=True).sort_values(by='timestamp')

        grouped_logs = []
        current_gmail_log = None

        for _, log in logs.iterrows():
            if log['_TAG_'] == 'Gmail_Subject':
                current_gmail_log = log
            elif log['_TAG_'] == 'Google_Redirection' and current_gmail_log is not None:
                gmail_log_dict = current_gmail_log.to_dict()
                redirection_log_dict = log.to_dict()

                # Timestamp를 문자열로 변환
                gmail_log_dict['timestamp'] = gmail_log_dict['timestamp'].isoformat() if gmail_log_dict['timestamp'] else None
                redirection_log_dict['timestamp'] = redirection_log_dict['timestamp'].isoformat() if redirection_log_dict['timestamp'] else None

                grouped_logs.append({
                    'gmail_log': gmail_log_dict,
                    'redirection_log': redirection_log_dict
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
    def __init__(self, db_url):
        self.engine = create_engine(db_url)

    def parse_datetime(self, dt_str):
        """문자열 형식의 날짜/시간을 datetime 객체로 변환"""
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_file_web_access(self):
        """모든 'File_Web_Access' 태그를 가진 데이터프레임 반환"""
        try:
            query = "SELECT * FROM Edge_Chromium_Web_Visits WHERE _TAG_ = 'File_Web_Access'"
            file_web_access_logs = pd.read_sql_query(query, self.engine)
            if 'Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)' not in file_web_access_logs.columns or 'URL' not in file_web_access_logs.columns:
                print("Edge_Chromium_Web_Visits 테이블에 필요한 컬럼이 없습니다. 실행을 종료합니다.")
                sys.exit(1)
            return file_web_access_logs
        except OperationalError:
            print("Edge_Chromium_Web_Visits 테이블이 존재하지 않습니다. 실행을 종료합니다.")
            sys.exit(1)

    def find_pdf_file_web_access(self):
        """ '.pdf'로 끝나는 'File_Web_Access' 로그만 필터링 """
        file_web_access_logs = self.find_file_web_access()
        pdf_logs = file_web_access_logs[file_web_access_logs['URL'].str.endswith('.pdf')]
        return pdf_logs

    def extract_pdf_filename(self, url):
        """URL에서 .pdf 파일명을 추출"""
        return url.split("/")[-1] if url.endswith('.pdf') else None

    def find_matching_pdf_document(self):
        """시간순으로 File_Web_Access와 PDF_Document 로그를 그룹화"""
        
        pdf_web_logs = self.find_pdf_file_web_access()
        try:
            pdf_documents = pd.read_sql_table("PDF_Documents", self.engine)
            if 'Filename' not in pdf_documents.columns or 'File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)' not in pdf_documents.columns:
                print("PDF_Documents 테이블에 필요한 컬럼이 없습니다. 실행을 종료합니다.")
                sys.exit(1)
        except OperationalError:
            print("PDF_Documents 테이블이 존재하지 않습니다. 실행을 종료합니다.")
            sys.exit(1)

        pdf_web_logs['timestamp'] = pdf_web_logs['Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'].apply(self.parse_datetime)
        pdf_web_logs = pdf_web_logs.sort_values(by='timestamp')

        grouped_logs = []
        for _, pdf_log in pdf_web_logs.iterrows():
            encoded_pdf_filename = self.extract_pdf_filename(pdf_log['URL'])
            pdf_filename = urllib.parse.unquote(encoded_pdf_filename)  # URL 디코딩

            visit_datetime = pdf_log['timestamp']
            matching_document = pdf_documents[pdf_documents['Filename'] == pdf_filename]

            if not matching_document.empty:
                fs_last_accessed_str = matching_document['File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)'].values[0]
                fs_last_accessed_datetime = self.parse_datetime(fs_last_accessed_str)

                # 웹 방문 날짜가 파일 시스템 접근 날짜보다 이후인 경우
                if fs_last_accessed_datetime and visit_datetime and visit_datetime > fs_last_accessed_datetime:
                    pdf_log_dict = pdf_log.to_dict()
                    document_dict = matching_document.iloc[0].to_dict()

                    # Timestamp를 문자열로 변환
                    pdf_log_dict['timestamp'] = pdf_log_dict['timestamp'].isoformat() if pdf_log_dict['timestamp'] else None
                    document_dict['File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)'] = fs_last_accessed_datetime.isoformat() if fs_last_accessed_datetime else None

                    grouped_logs.append({
                        'pdf_document_access_log': document_dict,
                        'pdf_web_access_log': pdf_log_dict
                    })

        return grouped_logs

    def apply_tags(self):
        """그룹화된 결과를 적용하여 출력"""
        grouped_logs = self.find_matching_pdf_document()
        if grouped_logs:
            print("File_Web_Access 이후의 PDF_Document 그룹화 결과:")
            print(json.dumps(grouped_logs, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

class LogTagger_1_4:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)

    def parse_datetime(self, dt_str):
        """문자열 형식의 날짜/시간을 datetime 객체로 변환"""
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_naver_mybox_file_get(self):
        """모든 'Naver_MyBox_File_Get' 태그를 가진 데이터프레임 반환"""
        try:
            query = "SELECT * FROM Edge_Chromium_Cache_Records WHERE _TAG_ = 'Naver_MyBox_File_Get'"
            naver_mybox_logs = pd.read_sql_query(query, self.engine)
            if 'Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)' not in naver_mybox_logs.columns:
                print("Edge_Chromium_Cache_Records 테이블에 필요한 컬럼이 없습니다. 실행을 종료합니다.")
                sys.exit(1)
            return naver_mybox_logs
        except OperationalError:
            print("Edge_Chromium_Cache_Records 테이블이 존재하지 않습니다. 실행을 종료합니다.")
            sys.exit(1)

    def find_mru_recent_files_and_folders(self):
        """MRU_Recent_Files_&_Folders 테이블의 모든 로그 반환"""
        try:
            mru_logs = pd.read_sql_table("MRU_Recent_Files_&_Folders", self.engine)
            if 'Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)' not in mru_logs.columns:
                print("MRU_Recent_Files_&_Folders 테이블에 필요한 컬럼이 없습니다. 실행을 종료합니다.")
                sys.exit(1)
            return mru_logs
        except OperationalError:
            print("MRU_Recent_Files_&_Folders 테이블이 존재하지 않습니다. 실행을 종료합니다.")
            sys.exit(1)

    def group_naver_mybox_and_mru_logs(self):
        """
        Naver_MyBox_File_Get 태그와 MRU_Recent_Files_&_Folders 로그를 비교하여
        Last_Visited_Date와 Registry_Key_Modified_Date가 1초 이내에 있는 로그 그룹화
        """
        result = []
        naver_logs = self.find_naver_mybox_file_get()
        mru_logs = self.find_mru_recent_files_and_folders()

        for _, naver_log in naver_logs.iterrows():
            naver_time = self.parse_datetime(naver_log.get('Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'))
            if naver_time is None:
                continue

            for _, mru_log in mru_logs.iterrows():
                mru_time = self.parse_datetime(mru_log.get('Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)'))
                if mru_time is None:
                    continue

                # 두 시간의 차이를 계산 (1초 이내인지 확인)
                time_diff = abs((naver_time - mru_time).total_seconds())

                if time_diff <= 1:  # 1초 이내
                    naver_log_dict = naver_log.to_dict()
                    mru_log_dict = mru_log.to_dict()

                    # 시간 차이를 문자열로 변환하여 저장
                    naver_log_dict['Last_Visited_Date/Time_-_UTC_(yyyy-mm-dd)'] = naver_time.isoformat()
                    mru_log_dict['Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)'] = mru_time.isoformat()

                    result.append({
                        "naver_log": naver_log_dict,
                        "mru_log": mru_log_dict,
                        "time_difference": time_diff
                    })

        return result

    def apply_tags(self):
        """그룹화된 결과를 적용하여 출력"""
        grouped_logs = self.group_naver_mybox_and_mru_logs()
        if grouped_logs:
            print("MyBox_Drive_File_Get와 MRU_Recent_Files_&_Folders 그룹화 결과:")
            for log in grouped_logs:
                print(json.dumps(log, indent=4, ensure_ascii=False))
        else:
            print("그룹화된 기록이 없습니다.")

class LogTagger_1_5:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)

    def parse_datetime(self, dt_str):
        """문자열 형식의 날짜/시간을 datetime 객체로 변환"""
        if dt_str is None:
            return None
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")

    def find_mru_folder_access_chrome(self):
        query = "SELECT * FROM MRU_Folder_Access WHERE _TAG_ = 'MRU_Folder_Access_Chrome'"
        mru_folder_access_logs = pd.read_sql_query(query, self.engine)
        # Folder_Accessed 컬럼 값을 리스트로 변환
        print("Folder_Accessed 값:", mru_folder_access_logs['Folder_Accessed'].tolist())
        return mru_folder_access_logs['Folder_Accessed'].tolist()

    def find_mru_opened_saved_files(self):
        # MRU_Folder_Access에서 Folder_Accessed 값 가져오기
        mru_folder_access_logs = self.find_mru_folder_access_chrome()
        
        # 결과를 저장할 데이터프레임 초기화
        opened_saved_files = pd.DataFrame()
        
        # 각 Folder_Accessed 값을 기준으로 MRU_Opened/Saved_Files 조회
        for folder_accessed in mru_folder_access_logs:
            # folder_accessed 값을 작은따옴표로 감싸서 쿼리 작성
            query = f"SELECT File_Path FROM 'MRU_Opened/Saved_Files' WHERE File_Path = '{folder_accessed}'"
            result = pd.read_sql_query(query, self.engine)
            print(f"쿼리 실행 결과 for '{folder_accessed}':\n", result)  # 디버깅 출력
            opened_saved_files = pd.concat([opened_saved_files, result], ignore_index=True)
        
        return opened_saved_files['File_Path']  # File_Path 컬럼만 반환

    def apply_tags(self):
            """파일 열람 기록 데이터를 불러와 출력"""
            opened_saved_files = self.find_mru_opened_saved_files()
            print(opened_saved_files)

# LogTaggerManager 클래스 정의
class LogTaggerManager:
    def __init__(self, db_url):
        self.tagger_classes = {
            "1": ("기본 태깅", LogTagger),
            "2": ("이메일에서 PDF 다운로드 그룹화", LogTagger_1),
            "3": ("Gmail과 드라이브 공유 그룹화", LogTagger_1_1),
            "4": ("Gmail과 리디렉션 그룹화", LogTagger_1_2),
            "5": ("파일 웹 접근과 PDF 문서 그룹화", LogTagger_1_3),
            "6": ("네이버 마이박스와 MRU 그룹화", LogTagger_1_4),
            "7": ("Chrome에서 MRU 폴더 접근 및 파일 열람 데이터", LogTagger_1_5)
        }
        self.db_url = db_url

    def display_options(self):
        print("사용할 태거 기능을 선택하세요:")
        for key, (desc, _) in self.tagger_classes.items():
            print(f"{key}: {desc}")

    def run_tagger(self, choice):
        """ 선택한 태거 클래스의 태깅 작업을 수행 """
        tagger_info = self.tagger_classes.get(choice)
        if tagger_info is None:
            print("유효하지 않은 선택입니다. 다시 시도하세요.")
            return

        _, tagger_class = tagger_info
        tagger_instance = tagger_class(self.db_url)
        tagger_instance.apply_tags()

# 사용 예시
db_url = r"sqlite:///C:\Users\addy0\OneDrive\바탕 화면\a\malware_main.db"
manager = LogTaggerManager(db_url)

# 사용자에게 선택지를 보여주고 입력 받기
while True:
    manager.display_options()
    choice = input("원하는 기능의 번호를 입력하세요 (종료하려면 'q'): ")
    if choice.lower() == 'q':
        print("프로그램을 종료합니다.")
        break
    manager.run_tagger(choice)