import json
from flask import Flask, render_template, request, jsonify
import difflib
from deepdiff import DeepDiff
from itertools import zip_longest

app = Flask(__name__)

def highlight_intra_line_diff(old_line, new_line):
    """
    Compara duas strings e retorna strings HTML com as diferenças de
    caracteres/palavras destacadas dentro de um <span class="highlight">.
    """
    matcher = difflib.SequenceMatcher(None, old_line, new_line)
    
    def escape(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    old_html, new_html = '', ''
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_fragment = escape(old_line[i1:i2])
        new_fragment = escape(new_line[j1:j2])
        
        if tag == 'equal':
            old_html += old_fragment
            new_html += new_fragment
        else:
            if old_fragment:
                old_html += f'<span class="highlight">{old_fragment}</span>'
            if new_fragment:
                new_html += f'<span class="highlight">{new_fragment}</span>'
            
    return old_html, new_html

@app.route('/')
def index():
    """ Rota principal que serve a página web (frontend). """
    try:
        with open('VERSION', 'r') as f:
            app_version = f.read().strip()
    except FileNotFoundError:
        app_version = "N/A"
        
    return render_template('index.html', app_version=app_version)

@app.route('/api/compare', methods=['POST'])
def compare_api():
    data = request.json
    original_content = data.get('original', '')
    altered_content = data.get('altered', '')
    
    result_data = {
        'diff_lines_original': [],
        'diff_lines_altered': [],
        'diff_type': "Texto",
        'summary': {}
    }

    try:
        # A lógica para JSON permanece a mesma
        original_json = json.loads(original_content)
        altered_json = json.loads(altered_content)
        diff = DeepDiff(original_json, altered_json, view='text', verbose_level=2)
        result_data['diff_type'] = "JSON/Objeto"
        if diff:
            result_data['diff_lines_original'] = [{'content': str(diff), 'type': 'none', 'line_num': 1}]
        else:
            result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
        result_data['summary'] = {'removals': 0, 'additions': 0}
        return jsonify(result_data)

    except json.JSONDecodeError:
        original_lines = original_content.splitlines()
        altered_lines = altered_content.splitlines()

        matcher = difflib.SequenceMatcher(None, original_lines, altered_lines)
        
        o_line_num, a_line_num = 0, 0
        removals, additions = 0, 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for i in range(i1, i2):
                    o_line_num += 1
                    a_line_num += 1
                    line_content = original_lines[i]
                    result_data['diff_lines_original'].append({'content': line_content, 'type': 'context', 'line_num': o_line_num})
                    result_data['diff_lines_altered'].append({'content': line_content, 'type': 'context', 'line_num': a_line_num})
            
            elif tag == 'delete':
                for i in range(i1, i2):
                    o_line_num += 1
                    removals += 1
                    result_data['diff_lines_original'].append({'content': original_lines[i], 'type': 'removed', 'line_num': o_line_num})
                    result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''})

            elif tag == 'insert':
                for j in range(j1, j2):
                    a_line_num += 1
                    additions += 1
                    result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''})
                    result_data['diff_lines_altered'].append({'content': altered_lines[j], 'type': 'added', 'line_num': a_line_num})

            elif tag == 'replace':
                old_block = original_lines[i1:i2]
                new_block = altered_lines[j1:j2]
                
                # --- LÓGICA DE ALINHAMENTO CORRIGIDA ---
                for old_line, new_line in zip_longest(old_block, new_block):
                    if old_line is not None and new_line is not None:
                        # Par de linhas alteradas -> aplicar diff intra-linha
                        o_line_num += 1
                        a_line_num += 1
                        removals += 1
                        additions += 1
                        highlighted_old, highlighted_new = highlight_intra_line_diff(old_line, new_line)
                        result_data['diff_lines_original'].append({'content': highlighted_old, 'type': 'removed', 'line_num': o_line_num})
                        result_data['diff_lines_altered'].append({'content': highlighted_new, 'type': 'added', 'line_num': a_line_num})
                    elif old_line is not None:
                        # Apenas linha antiga (deleção) -> Adiciona placeholder no lado direito
                        o_line_num += 1
                        removals += 1
                        result_data['diff_lines_original'].append({'content': old_line, 'type': 'removed', 'line_num': o_line_num})
                        result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''})
                    elif new_line is not None:
                        # Apenas linha nova (adição) -> Adiciona placeholder no lado esquerdo
                        a_line_num += 1
                        additions += 1
                        result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''})
                        result_data['diff_lines_altered'].append({'content': new_line, 'type': 'added', 'line_num': a_line_num})

        if not original_content and not altered_content:
            result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': ''}]

        result_data['summary'] = {
            'removals': removals,
            'additions': additions,
            'total_lines_original': len(original_lines),
            'total_lines_altered': len(altered_lines)
        }
        
        return jsonify(result_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)