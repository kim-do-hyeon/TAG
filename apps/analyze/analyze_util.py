from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd

def shorten_string(s) :
    if s == None :
        return "0"
    if len(s) > 40 :
        return s[0:35] + '...'
    else :
        return s

def insert_char_enter(string):
    return '\n'.join([string[i:i+60] for i in range(0, len(string), 60)])

def change_local_time(date_str) :
    date_format = "%Y-%m-%d %H:%M:%S"
    date_obj = datetime.strptime(date_str, date_format)
    new_date_obj = date_obj + timedelta(hours=9)
    new_date_str = new_date_obj.strftime(date_format)
    return new_date_str

def extract_body_and_scripts(filtering_data):
    tables = []
    for i in filtering_data.datas:
        data_frame = pd.DataFrame(i['Data'])  # 'Data'는 판다스 DataFrame
        
        if not data_frame.empty and 'hit_id' in data_frame.columns:
            # 각 셀에 툴팁을 적용할 수 있도록 HTML을 생성
            table_html = data_frame.to_html(classes='table table-striped', index=False, escape=False)
            
            # BeautifulSoup으로 HTML 테이블 파싱하여 각 셀에 툴팁 추가
            soup = BeautifulSoup(table_html, 'html.parser')
            rows = data_frame.to_dict(orient='records')  # DataFrame을 리스트 형식으로 변환
            
            # 테이블의 각 행과 매칭하여 'hit_id' 값을 'onclick'에 추가
            for idx, td in enumerate(soup.find_all('td')):
                full_text = td.get_text()
                row = rows[idx // len(data_frame.columns)]  # 해당 행 가져오기
                hit_id_value = row.get('hit_id', '')  # hit_id 값 가져오기
                
                td['title'] = full_text  # 툴팁에 전체 텍스트 추가
                td.string = (full_text[:50] + '...') if len(full_text) > 50 else full_text  # 셀에 50자까지만 표시
                
                # hit_id 값을 'onclick' 이벤트에 삽입
                td['onclick'] = f"filterFromTable('{hit_id_value}')"

            tables.append({
                'title': i['Table'],  # 테이블 제목
                'content': str(soup)  # 툴팁이 적용된 테이블 HTML
            })
            
    result = filtering_data.filtering_data

    with open(result, 'r') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    body_content = soup.body
    scripts = soup.find_all('script')
    body_html = str(body_content)
    scripts_html = ''.join([str(script) for script in scripts])
    
    return body_html, scripts_html, tables