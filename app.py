import json
from flask import Flask, render_template, request, jsonify
import difflib # Usaremos mais funcionalidades do difflib
from deepdiff import DeepDiff

app = Flask(__name__)

def highlight_intra_line_diff(old_line, new_line):
    """
    Compara duas linhas e retorna strings HTML com as diferenças de caracteres destacadas.
    """
    matcher = difflib.SequenceMatcher(None, old_line, new_line)
    
    old_html, new_html = '', ''
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            old_html += old_line[i1:i2]
            new_html += new_line[j1:j2]
        elif tag == 'replace':
            old_html += f'<span class="highlight">{old_line[i1:i2]}</span>'
            new_html += f'<span class="highlight">{new_line[j1:j2]}</span>'
        elif tag == 'delete':
            old_html += f'<span class="highlight">{old_line[i1:i2]}</span>'
        elif tag == 'insert':
            new_html += f'<span class="highlight">{new_line[j1:j2]}</span>'
            
    return old_html, new_html

@app.route('/')
def index():
    return render_template('index.html')

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
        # Lógica para JSON permanece a mesma
        original_json = json.loads(original_content)
        altered_json = json.loads(altered_content)
        # ... (código do JSON diff omitido para brevidade, pois não muda)
        diff = DeepDiff(original_json, altered_json, view='text', verbose_level=2)
        result_data['diff_type'] = "JSON/Objeto"

        if diff:
            result_data['diff_lines_original'] = [{'content': str(diff), 'type': 'none', 'line_num': 1}]
            result_data['diff_lines_altered'] = [{'content': '', 'type': 'none', 'line_num': 1}]
        else:
            result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
            result_data['diff_lines_altered'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
        
        # O summary para JSON pode ser melhorado se necessário
        result_data['summary'] = {'removals': 0, 'additions': 0, 'total_lines_original': 1, 'total_lines_altered': 1}
        return jsonify(result_data)

    except json.JSONDecodeError:
        # LÓGICA ATUALIZADA PARA TEXTO PLANO
        original_lines = original_content.splitlines()
        altered_lines = altered_content.splitlines()
        
        diff_lines = list(difflib.ndiff(original_lines, altered_lines))
        
        o_line_num, a_line_num = 0, 0
        removals, additions = 0, 0
        
        i = 0
        while i < len(diff_lines):
            line = diff_lines[i]
            
            if line.startswith('  '): # Contexto
                o_line_num += 1
                a_line_num += 1
                result_data['diff_lines_original'].append({'content': line[2:], 'type': 'context', 'line_num': o_line_num})
                result_data['diff_lines_altered'].append({'content': line[2:], 'type': 'context', 'line_num': a_line_num})
                i += 1
            elif line.startswith('- ') and (i + 1 < len(diff_lines)) and diff_lines[i+1].startswith('+ '):
                # Par de remoção/adição -> Mudança de linha
                old_line = line[2:]
                new_line = diff_lines[i+1][2:]
                
                highlighted_old, highlighted_new = highlight_intra_line_diff(old_line, new_line)
                
                removals += 1
                additions += 1
                o_line_num += 1
                a_line_num += 1
                
                result_data['diff_lines_original'].append({'content': highlighted_old, 'type': 'removed', 'line_num': o_line_num})
                result_data['diff_lines_altered'].append({'content': highlighted_new, 'type': 'added', 'line_num': a_line_num})
                i += 2 # Pula as duas linhas processadas
            elif line.startswith('- '): # Apenas remoção
                removals += 1
                o_line_num += 1
                result_data['diff_lines_original'].append({'content': line[2:], 'type': 'removed', 'line_num': o_line_num})
                result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''})
                i += 1
            elif line.startswith('+ '): # Apenas adição
                additions += 1
                a_line_num += 1
                result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''})
                result_data['diff_lines_altered'].append({'content': line[2:], 'type': 'added', 'line_num': a_line_num})
                i += 1
            elif line.startswith('? '):
                # A linha '?' do ndiff é informativa, mas nossa lógica de highlight já a substitui.
                i += 1
        
        if not removals and not additions:
            if not original_lines and not altered_lines:
                result_data['diff_lines_original'] = [{'content': 'Nenhuma diferença encontrada.', 'type': 'none', 'line_num': ''}]
            else: # Repopula se não houver diff
                 result_data['diff_lines_original'] = [] # Limpa para evitar duplicatas
                 for idx, line_content in enumerate(original_lines):
                    result_data['diff_lines_original'].append({'content': line_content, 'type': 'context', 'line_num': idx + 1})
                    result_data['diff_lines_altered'].append({'content': altered_lines[idx], 'type': 'context', 'line_num': idx + 1})


        result_data['summary'] = {
            'removals': removals,
            'additions': additions,
            'total_lines_original': len(original_lines),
            'total_lines_altered': len(altered_lines)
        }
        
        return jsonify(result_data)