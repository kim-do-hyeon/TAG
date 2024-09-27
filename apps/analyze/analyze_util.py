from datetime import datetime, timedelta

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
