import os
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def get_total_size(user_upload_cases) :
    folders = {}
    for i in user_upload_cases :
        case_folder = os.path.join(os.getcwd(), "uploads", i.user, i.case_number)
        folder_size = get_folder_size(case_folder)
        folders[case_folder] = folder_size
    total_size = sum(folders.values())
    return folders, total_size

def get_total_size_gb(total_size) :
    total_size_gb = round(total_size / (1024 ** 3), 2)
    return total_size_gb

def get_folder_percentages(folders, total_size) :
    folder_labels = [os.path.basename(folder) for folder in folders.keys()]
    folder_percentages = [(size / total_size) * 100 if total_size > 0 else 0 for size in folders.values()]
    return folder_labels, folder_percentages

def get_analyze_tool(user_upload_cases) :
    analyze_tool = {"axiom" : 0, "autopsy" : 0, "encase" : 0}
    for i in user_upload_cases :
        extensions = str(os.path.splitext(i.file)[1]).lower()
        print(extensions)
        if extensions == ".mfdb" :
            analyze_tool['axiom'] += 1
        elif extensions == ".db" :
            analyze_tool['autopsy'] += 1
        elif extensions == ".case" :
            analyze_tool["encase"] += 1
    return list(analyze_tool.keys()), list(analyze_tool.values())
