import json
from flask import Flask, render_template, request, jsonify
from difflib import Differ
from deepdiff import DeepDiff

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/compare', methods=['POST'])
def compare_api():
    data = request.json
    original_content = data.get('original', '')
    altered_content = data.get('altered', '')
    
    result_data = {
        'diff_lines_original': [], # Linhas para o painel original
        'diff_lines_altered': [],  # Linhas para o painel alterado
        'diff_type': "Texto",
        'summary': {}
    }

    # Tenta a comparação como JSON primeiro
    try:
        original_json = json.loads(original_content)
        altered_json = json.loads(altered_content)
        diff = DeepDiff(original_json, altered_json, view='text', verbose_level=2) # verbose_level para mais detalhes
        result_data['diff_type'] = "JSON/Objeto"

        if diff:
            # Para JSON, DeepDiff já é bem formatado, mas não temos o side-by-side nativo.
            # Vamos apresentar como um único texto formatado por enquanto.
            result_data['diff_lines_original'] = [{'content': str(diff), 'type': 'none', 'line_num': 1}]
            result_data['diff_lines_altered'] = [{'content': '', 'type': 'none', 'line_num': 1}]
            result_data['summary'] = {
                'removals': len(diff.get('type_changes', {})) + len(diff.get('iterable_item_removed', {})),
                'additions': len(diff.get('type_changes', {})) + len(diff.get('iterable_item_added', {})),
                'total_lines_original': 1, # Ajustar conforme a representação do JSON
                'total_lines_altered': 1   # Ajustar conforme a representação do JSON
            }
            if not result_data['summary']['removals'] and not result_data['summary']['additions']:
                 result_data['summary']['total_changes'] = len(diff.get('values_changed', {})) + len(diff.get('dictionary_item_added', {})) + len(diff.get('dictionary_item_removed', {})) + len(diff.get('set_item_added', {})) + len(diff.get('set_item_removed', {}))
            
        else:
            result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
            result_data['diff_lines_altered'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
            result_data['summary'] = {'removals': 0, 'additions': 0, 'total_lines_original': 1, 'total_lines_altered': 1, 'total_changes': 0}

    except json.JSONDecodeError:
        # Comparação de texto plano (usando difflib para side-by-side logic)
        d = Differ()
        original_lines = original_content.splitlines()
        altered_lines = altered_content.splitlines()
        
        diff_generator = d.compare(original_lines, altered_lines)
        
        o_line_num = 0
        a_line_num = 0
        removals = 0
        additions = 0

        # Para simular o side-by-side do git diff
        for line in diff_generator:
            if line.startswith('  '): # Contexto
                o_line_num += 1
                a_line_num += 1
                result_data['diff_lines_original'].append({'content': line[2:], 'type': 'context', 'line_num': o_line_num})
                result_data['diff_lines_altered'].append({'content': line[2:], 'type': 'context', 'line_num': a_line_num})
            elif line.startswith('- '): # Removido
                removals += 1
                o_line_num += 1
                result_data['diff_lines_original'].append({'content': line[2:], 'type': 'removed', 'line_num': o_line_num})
                result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''}) # Coluna vazia para alinhamento
            elif line.startswith('+ '): # Adicionado
                additions += 1
                a_line_num += 1
                result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''}) # Coluna vazia para alinhamento
                result_data['diff_lines_altered'].append({'content': line[2:], 'type': 'added', 'line_num': a_line_num})
            elif line.startswith('? '): # Alterado (indica mudanças de caracteres)
                # O difflib marca a linha com '?' após a linha adicionada/removida.
                # Não é necessário renderizá-la no side-by-side, pois já temos as linhas +/-
                pass
            
        # Adiciona um caso para quando não há diferenças
        if not (removals or additions) and not result_data['diff_lines_original']:
             for i, line in enumerate(original_lines):
                result_data['diff_lines_original'].append({'content': line, 'type': 'context', 'line_num': i + 1})
                result_data['diff_lines_altered'].append({'content': altered_lines[i], 'type': 'context', 'line_num': i + 1})
             
             if not original_lines and not altered_lines: # Se ambos estão vazios
                result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': ''}]
                result_data['diff_lines_altered'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': ''}]
                result_data['summary'] = {'removals': 0, 'additions': 0, 'total_lines_original': 0, 'total_lines_altered': 0, 'total_changes': 0}
             else:
                result_data['summary'] = {'removals': 0, 'additions': 0, 'total_lines_original': o_line_num, 'total_lines_altered': a_line_num, 'total_changes': 0}
        else:
            result_data['summary'] = {
                'removals': removals,
                'additions': additions,
                'total_lines_original': o_line_num,
                'total_lines_altered': a_line_num
            }


    return jsonify(result_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) # Habilite debug para ver erros durante o desenvolvimento