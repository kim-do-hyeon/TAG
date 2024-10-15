import sqlite3
from flask import session
import pandas as pd
import os
from pyvis.network import Network
import os, sqlite3
import pandas as pd
from pprint import pprint
from datetime import timedelta
from apps.authentication.models import Upload_Case
import ast
import json

def shorten_string(s) :
    if len(s) > 40 :
        return s[0:35] + '...'
    else :
        return s

def insert_char_enter(string):
    return '\n'.join([string[i:i+60] for i in range(0, len(string), 60)])

def modify_html_click(output_file, id_change) :
    # HTML 파일을 수정하는 코드 추가
    with open(output_file, 'r') as file:
        html_content = file.read()

    # 예를 들어, 특정 스크립트를 추가하거나 기존 스크립트를 수정할 수 있습니다.
    # 여기에 예시로 네트워크 상호작용을 추가하는 자바스크립트를 삽입
    additional_script = additional_script = """
        <script type="text/javascript">
            network.on("click", function (params) {
                if (params.nodes.length > 0) {
                    var clickedNode = params.nodes[0];
                    alert("Node " + clickedNode + " was clicked!");
                }
            });
        </script>
        """

    # 특정 위치에 스크립트 삽입 (예: </body> 태그 직전에 삽입)
    html_content = html_content.replace('</body>', additional_script + '</body>')
    html_content = html_content.replace("mynetwork", id_change)

    # 수정된 HTML 파일 다시 저장
    with open(output_file, 'w') as file:
        file.write(html_content)

def make_analyze_tag_group_graph(result_list, case_id) :
    user = session.get('username')
    case_number = Upload_Case.query.filter_by(id=case_id).first().case_number
    case_folder = os.path.join(os.getcwd(), "uploads", user, case_number)
    output_files = []
    for group_name, group_list in result_list.items() :
        for idx, group in enumerate(group_list) :
            net = Network(height="750px", width="100%", notebook=True)
            net.force_atlas_2based()
            prev_log = None
            for log, attributes in group.items() :
                title = ''
                for col, data in attributes.items() :
                    if data :
                        row = insert_char_enter(f'{col} : {str(data)}')
                        title += row + '\n\n'
                net.add_node(log, label=log, title=title, color='skyblue', shape='ellipse', size=150, font={'size' : 20})
                
                if prev_log is not None :
                    edge_label = group_name
                    net.add_edge(prev_log, log, arrows='to', label=edge_label)
                
                prev_log = log
                
                # for col, data in attributes.items() :
                #     if data :
                #         title=f'{col}\n{insert_char_enter(data)}'
                #         net.add_node(log+col, label=shorten_string(data), title=title, shape='ellipse', color='pink', size=50)
                #         net.add_edge(log, log+col)
            output_file = os.path.join(case_folder, f'{group_name}_{str(idx)}.html')
            #net.show_buttons(filter_=['physics'])
            physics_options = """
            var options = {
            "physics": {
                "forceAtlas2Based": {
                "centralGravity": 0.005,
                "springLength": 250,
                "springConstant": 0.12
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based",
                "avoidOverlap": 1
            }
            }
            """
            net.set_options(physics_options)
            net.save_graph(output_file)
            modify_html_click(output_file, f'{group_name}_{str(idx)}.html')
            print(f'Saved to {output_file}')
            output_files.append([group_name, output_file])
    return output_files