def shorten_string(s) :
    if s == None :
        return "0"
    if len(s) > 40 :
        return s[0:35] + '...'
    else :
        return s

def insert_char_enter(string):
    return '\n'.join([string[i:i+60] for i in range(0, len(string), 60)])
