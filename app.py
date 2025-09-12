import json
from flask import Flask, render_template, request, jsonify
import difflib
from deepdiff import DeepDiff
from itertools import zip_longest
from jproperties import Properties # Nova importação

app = Flask(__name__)

# A função highlight_intra_line_diff permanece a mesma
def highlight_intra_line_diff(old_line, new_line):
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
        'summary': {'removals': 0, 'additions': 0, 'changes': 0}
    }

    # --- NOVA LÓGICA DE DETECÇÃO AUTOMÁTICA ---

    # 1. TENTAR COMO JSON
    try:
        original_obj = json.loads(original_content)
        altered_obj = json.loads(altered_content)
        result_data['diff_type'] = "JSON"
        
        diff = DeepDiff(original_obj, altered_obj, view='text')
        if diff:
            result_data['diff_lines_original'] = [{'content': str(diff), 'type': 'context', 'line_num': 1}]
            # Preenche o summary com dados do DeepDiff
            summary = {
                'removals': len(diff.get('dictionary_item_removed', [])),
                'additions': len(diff.get('dictionary_item_added', [])),
                'changes': len(diff.get('values_changed', []))
            }
            result_data['summary'] = summary
        else:
            result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
        
        return jsonify(result_data)

    except (json.JSONDecodeError, TypeError):
        # Se não for JSON, continua para a próxima tentativa
        pass

    # 2. TENTAR COMO PROPRIEDADES JAVA
    try:
        # A biblioteca jproperties funciona com objetos 'file-like', então usamos StringIO
        from io import StringIO
        
        p_original = Properties()
        p_original.load(StringIO(original_content))
        
        p_altered = Properties()
        p_altered.load(StringIO(altered_content))

        # DeepDiff funciona perfeitamente com os objetos Properties
        diff = DeepDiff(p_original.properties, p_altered.properties, view='text')
        result_data['diff_type'] = "Java Properties"

        if diff:
            result_data['diff_lines_original'] = [{'content': str(diff), 'type': 'context', 'line_num': 1}]
            summary = {
                'removals': len(diff.get('dictionary_item_removed', [])),
                'additions': len(diff.get('dictionary_item_added', [])),
                'changes': len(diff.get('values_changed', []))
            }
            result_data['summary'] = summary
        else:
            result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]

        return jsonify(result_data)
        
    except Exception:
        # Se falhar como properties, continua para o fallback final
        pass
    
    # 3. FALLBACK PARA TEXTO SIMPLES (LÓGICA ANTERIOR)
    result_data['diff_type'] = "Texto"
    original_lines = original_content.splitlines()
    altered_lines = altered_content.splitlines()
    matcher = difflib.SequenceMatcher(None, original_lines, altered_lines)
    # ... (toda a lógica de diff de texto que já tínhamos)
    o_line_num, a_line_num, removals, additions = 0, 0, 0, 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # ...
            for i in range(i1, i2):
                o_line_num += 1; a_line_num += 1
                line = original_lines[i]
                result_data['diff_lines_original'].append({'content': line, 'type': 'context', 'line_num': o_line_num})
                result_data['diff_lines_altered'].append({'content': line, 'type': 'context', 'line_num': a_line_num})
        else:
            old_block = original_lines[i1:i2]
            new_block = altered_lines[j1:j2]
            for old_line, new_line in zip_longest(old_block, new_block):
                if old_line is not None: o_line_num += 1; removals += 1
                if new_line is not None: a_line_num += 1; additions += 1
                if old_line is not None and new_line is not None:
                    h_old, h_new = highlight_intra_line_diff(old_line, new_line)
                    result_data['diff_lines_original'].append({'content': h_old, 'type': 'removed', 'line_num': o_line_num})
                    result_data['diff_lines_altered'].append({'content': h_new, 'type': 'added', 'line_num': a_line_num})
                elif old_line is not None:
                    result_data['diff_lines_original'].append({'content': old_line, 'type': 'removed', 'line_num': o_line_num})
                    result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''})
                elif new_line is not None:
                    result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''})
                    result_data['diff_lines_altered'].append({'content': new_line, 'type': 'added', 'line_num': a_line_num})

    if not original_content and not altered_content:
        result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': ''}]
    result_data['summary'] = {
        'removals': removals, 'additions': additions, 'changes': 0,
        'total_lines_original': len(original_lines),
        'total_lines_altered': len(altered_lines)
    }
    return jsonify(result_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)