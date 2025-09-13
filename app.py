import json
import logging
import re
import sys
from flask import Flask, render_template, request, jsonify
import difflib
from deepdiff import DeepDiff
from itertools import zip_longest
from jproperties import Properties
from io import BytesIO

# Configuração dos Logs
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

def format_deepdiff(diff):
    # ... (função sem alterações)
    report_lines = []
    change_types = {'dictionary_item_added': "Chave Adicionada", 'dictionary_item_removed': "Chave Removida", 'values_changed': "Valor Alterado", 'type_changes': "Tipo Alterado"}
    for change_type, friendly_name in change_types.items():
        if change_type in diff:
            report_lines.append(f"--- {friendly_name} ---")
            items = diff[change_type]
            if isinstance(items, dict):
                for path, change in items.items(): report_lines.append(f"Em '{path}': de '{change['old_value']}' para '{change['new_value']}'")
            else:
                for path in items: report_lines.append(str(path))
            report_lines.append("")
    if not report_lines: return "Nenhuma diferença encontrada."
    return "\n".join(report_lines)

def highlight_intra_line_diff(old_line, new_line):
    # ... (função sem alterações)
    matcher = difflib.SequenceMatcher(None, old_line, new_line)
    def escape(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    old_html, new_html = '', ''
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_fragment, new_fragment = escape(old_line[i1:i2]), escape(new_line[j1:j2])
        if tag == 'equal': old_html += old_fragment; new_html += new_fragment
        else:
            if old_fragment: old_html += f'<span class="highlight">{old_fragment}</span>'
            if new_fragment: new_html += f'<span class="highlight">{new_fragment}</span>'
    return old_html, new_html

@app.route('/')
def index():
    """Serve a página principal."""
    try:
        with open('VERSION', 'r') as f: app_version = f.read().strip()
    except FileNotFoundError: app_version = "N/A"
    return render_template('index.html', app_version=app_version)

@app.route('/api/compare', methods=['POST'])
def compare_api():
    """Endpoint principal que lida com as comparações."""
    logging.info(f"Recebida nova requisição de comparação de {request.remote_addr}")
    data = request.json
    original_content = data.get('original', '')
    altered_content = data.get('altered', '')
    is_properties = data.get('is_properties', False)
    
    result_data = {'diff_lines_original': [], 'diff_lines_altered': [], 'diff_type': "Texto", 'summary': {'removals': 0, 'additions': 0, 'changes': 0}}

    if is_properties:
        # --- LÓGICA EXCLUSIVA PARA PROPERTIES ---
        logging.info("Comparação de 'Properties' solicitada. Focando apenas nas diferenças.")
        try:
            p_original, p_altered = Properties(), Properties()
            p_original.load(BytesIO(original_content.encode('utf-8')))
            p_altered.load(BytesIO(altered_content.encode('utf-8')))
            original_dict, altered_dict = p_original.properties, p_altered.properties
            removals, additions, changes = 0, 0, 0
            all_keys = sorted(list(set(original_dict.keys()) | set(altered_dict.keys())))
            line_num = 0
            for key in all_keys:
                old_value, new_value = original_dict.get(key), altered_dict.get(key)
                if old_value is not None and new_value is not None and old_value == new_value: continue
                line_num += 1
                if old_value is not None and new_value is not None:
                    changes += 1; removals += 1; additions += 1
                    h_old, h_new = highlight_intra_line_diff(old_value, new_value)
                    result_data['diff_lines_original'].append({'content': f"{key} = {h_old}", 'type': 'removed', 'line_num': line_num})
                    result_data['diff_lines_altered'].append({'content': f"{key} = {h_new}", 'type': 'added', 'line_num': line_num})
                elif old_value is not None:
                    removals += 1
                    result_data['diff_lines_original'].append({'content': f"{key} = {old_value}", 'type': 'removed', 'line_num': line_num})
                    result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''})
                elif new_value is not None:
                    additions += 1
                    result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''})
                    result_data['diff_lines_altered'].append({'content': f"{key} = {new_value}", 'type': 'added', 'line_num': line_num})
            result_data['diff_type'] = "Java Properties"
            result_data['summary'] = {'removals': removals, 'additions': additions, 'changes': changes}
            if not result_data['diff_lines_original']:
                 result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
                 result_data['diff_lines_altered'] = []
            return jsonify(result_data)
        except Exception as e:
            logging.error(f"Falha ao analisar como Properties: {e}", exc_info=True)
            error_result = {'diff_lines_original': [{'content': f"Erro ao analisar como .properties:\n{e}", 'type': 'error'}], 'summary': {}}
            return jsonify(error_result), 400
    
    else: # --- FLUXO PADRÃO (JSON OU TEXTO) ---
        try:
            logging.info("Tentando analisar entradas como JSON...")
            original_obj, altered_obj = json.loads(original_content), json.loads(altered_content)
            if isinstance(original_obj, str) and isinstance(altered_obj, str): raise TypeError("JSON resultou em strings, tratando como texto.")
            result_data['diff_type'] = "JSON"
            diff = DeepDiff(original_obj, altered_obj)
            if diff:
                logging.info(f"Análise JSON bem-sucedida. Encontradas {len(diff)} categorias de diferenças.")
                result_data['diff_lines_original'] = [{'content': format_deepdiff(diff), 'type': 'context', 'line_num': 1}]
                result_data['summary'] = {'removals': len(diff.get('dictionary_item_removed', [])), 'additions': len(diff.get('dictionary_item_added', [])), 'changes': len(diff.get('values_changed', [])) + len(diff.get('type_changes', []))}
            else:
                logging.info("Análise JSON bem-sucedida. Nenhuma diferença encontrada.")
                result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
        except Exception:
            logging.info("Não é JSON válido ou foi forçado para texto. Recorrendo à comparação de texto simples.")
            result_data['diff_type'] = "Texto" # Garante que o tipo está correto
            original_lines, altered_lines = original_content.splitlines(), altered_content.splitlines()
            matcher = difflib.SequenceMatcher(None, original_lines, altered_lines)
            o_line_num, a_line_num, removals, additions, changes = 0, 0, 0, 0, 0
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    for i in range(i1, i2):
                        o_line_num += 1; a_line_num += 1
                        result_data['diff_lines_original'].append({'content': original_lines[i], 'type': 'context', 'line_num': o_line_num})
                        result_data['diff_lines_altered'].append({'content': altered_lines[j1 + (i - i1)], 'type': 'context', 'line_num': a_line_num})
                else:
                    old_block, new_block = original_lines[i1:i2], altered_lines[j1:j2]
                    for old_line, new_line in zip_longest(old_block, new_block):
                        current_o_num, current_a_num = '', ''
                        if old_line is not None: o_line_num += 1; removals += 1; current_o_num = o_line_num
                        if new_line is not None: a_line_num += 1; additions += 1; current_a_num = a_line_num
                        if old_line is not None and new_line is not None:
                            changes += 1
                            h_old, h_new = highlight_intra_line_diff(old_line, new_line)
                            result_data['diff_lines_original'].append({'content': h_old, 'type': 'removed', 'line_num': current_o_num})
                            result_data['diff_lines_altered'].append({'content': h_new, 'type': 'added', 'line_num': current_a_num})
                        elif old_line is not None:
                            result_data['diff_lines_original'].append({'content': old_line, 'type': 'removed', 'line_num': current_o_num})
                            result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''})
                        elif new_line is not None:
                            result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''})
                            result_data['diff_lines_altered'].append({'content': new_line, 'type': 'added', 'line_num': current_a_num})
            if not original_content and not altered_content:
                result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': ''}]
            result_data['summary'] = {'removals': removals, 'additions': additions, 'changes': changes, 'total_lines_original': len(original_lines), 'total_lines_altered': len(altered_lines)}
            logging.info(f"Diff de texto concluído: {removals} remoções, {additions} adições, {changes} alterações.")
        
        return jsonify(result_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)