class Ext_Info :
    def __init__(self) :
        self.docs_exts = ['hwp', 'hwpx', 'pptx', 'ppt', 'doc', 'docx', 'show', 'xlsx', 'pdf']
        self.exeXdocs = {
            "POWERPNT.EXE" : ['pptx', 'ppt'],
            "HWP.EXE" : ['hwp', 'hwpx'],
            "WINWORD.EXE" : ['docx', 'doc'],
            "HPDF.EXE" : ['pdf'],
            "MSEDGE.EXE" : ['pdf'],
            "CHROME.EXE" : ['pdf']
        }