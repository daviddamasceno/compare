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
    """Converte um objeto DeepDiff em uma string legível para humanos."""
    report_lines = []
    change_types = {
        'dictionary_item_added': "Chave Adicionada",
        'dictionary_item_removed': "Chave Removida",
        'values_changed': "Valor Alterado",
        'type_changes': "Tipo Alterado"
    }
    for change_type, friendly_name in change_types.items():
        if change_type in diff:
            report_lines.append(f"--- {friendly_name} ---")
            items = diff[change_type]
            if isinstance(items, dict):
                for path, change in items.items():
                    report_lines.append(f"Em '{path}': de '{change['old_value']}' para '{change['new_value']}'")
            else:
                for path in items:
                    report_lines.append(str(path))
            report_lines.append("")
    if not report_lines:
        return "Nenhuma diferença encontrada."
    return "\n".join(report_lines)

def highlight_intra_line_diff(old_line, new_line):
    """Compara duas strings e retorna HTML com as diferenças destacadas."""
    matcher = difflib.SequenceMatcher(None, old_line, new_line)
    def escape(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    old_html, new_html = '', ''
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_fragment, new_fragment = escape(old_line[i1:i2]), escape(new_line[j1:j2])
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
    """Serve a página principal."""
    try:
        with open('VERSION', 'r') as f:
            app_version = f.read().strip()
    except FileNotFoundError:
        app_version = "N/A"
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
        # --- LÓGICA EXCLUSIVA PARA PROPERTIES (JÁ ESTÁ CORRETA) ---
        logging.info("Comparação de 'Properties' solicitada.")
        try:
            def normalize_properties_text(text):
                return re.sub(r'(?<!\\)\n', r'\\n', text)

            p_original, p_altered = Properties(), Properties()
            p_original.load(BytesIO(normalize_properties_text(original_content).encode('utf-8')))
            p_altered.load(BytesIO(normalize_properties_text(altered_content).encode('utf-8')))
            original_dict = p_original.properties
            altered_dict = p_altered.properties
            
            original_keys = [k for k, v in p_original.items()]
            altered_keys = [k for k, v in p_altered.items()]
            
            key_matcher = difflib.SequenceMatcher(None, original_keys, altered_keys)
            o_line_num, a_line_num, removals, additions, changes = 0, 0, 0, 0, 0

            for tag, i1, i2, j1, j2 in key_matcher.get_opcodes():
                if tag == 'equal':
                    # Opcional: se quiser ver linhas iguais no modo properties, descomente o bloco abaixo
                    # for i in range(i1, i2):
                    #     o_line_num += 1; a_line_num += 1
                    #     key = original_keys[i]; value = original_dict[key]
                    #     result_data['diff_lines_original'].append({'content': f"{key} = {value}", 'type': 'context', 'line_num': o_line_num})
                    #     result_data['diff_lines_altered'].append({'content': f"{key} = {value}", 'type': 'context', 'line_num': a_line_num})
                    pass # Atualmente, ignoramos linhas iguais no modo properties
                else:
                    old_block_keys = original_keys[i1:i2]
                    new_block_keys = altered_keys[j1:j2]
                    sub_matcher = difflib.SequenceMatcher(None, old_block_keys, new_block_keys)
                    for sub_tag, old_i1, old_i2, new_i1, new_i2 in sub_matcher.get_opcodes():
                        if sub_tag == 'equal':
                             for i in range(old_i1, old_i2):
                                o_line_num += 1; a_line_num += 1
                                key = old_block_keys[i]
                                old_value, new_value = original_dict[key], altered_dict[key]
                                changes += 1; removals += 1; additions += 1
                                h_old, h_new = highlight_intra_line_diff(old_value, new_value)
                                result_data['diff_lines_original'].append({'content': f"{key} = {h_old}", 'type': 'removed', 'line_num': o_line_num})
                                result_data['diff_lines_altered'].append({'content': f"{key} = {h_new}", 'type': 'added', 'line_num': a_line_num})
                        else:
                            temp_old_keys = old_block_keys[old_i1:old_i2]
                            temp_new_keys = new_block_keys[new_i1:new_i2]
                            for old_key, new_key in zip_longest(temp_old_keys, temp_new_keys):
                                if old_key is not None:
                                    o_line_num += 1; removals += 1
                                    result_data['diff_lines_original'].append({'content': f"{old_key} = {original_dict[old_key]}", 'type': 'removed', 'line_num': o_line_num})
                                    result_data['diff_lines_altered'].append({'content': '', 'type': 'empty', 'line_num': ''})
                                if new_key is not None:
                                    a_line_num += 1; additions += 1
                                    result_data['diff_lines_original'].append({'content': '', 'type': 'empty', 'line_num': ''})
                                    result_data['diff_lines_altered'].append({'content': f"{new_key} = {altered_dict[new_key]}", 'type': 'added', 'line_num': a_line_num})
            
            result_data['diff_type'] = "Java Properties"
            result_data['summary'] = {'removals': removals, 'additions': additions, 'changes': changes}
            if not removals and not additions and not changes:
                 result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
                 result_data['diff_lines_altered'] = []
            return jsonify(result_data)
        except Exception as e:
            logging.error(f"Falha ao analisar como Properties: {e}", exc_info=True)
            error_result = {'diff_lines_original': [{'content': f"Erro ao analisar o arquivo como .properties:\n{e}", 'type': 'error'}], 'summary': {}}
            return jsonify(error_result), 400
    
    else: # --- FLUXO PADRÃO (JSON OU TEXTO) CORRIGIDO ---
        is_json = False
        try:
            original_obj = json.loads(original_content)
            altered_obj = json.loads(altered_content)
            # Se a análise for bem-sucedida para ambos e não forem strings puras, é JSON
            if not (isinstance(original_obj, str) and isinstance(altered_obj, str)):
                is_json = True
        except Exception:
            is_json = False # Se qualquer um falhar, não é JSON

        if is_json:
            logging.info("Entradas identificadas como JSON.")
            result_data['diff_type'] = "JSON"
            diff = DeepDiff(original_obj, altered_obj)
            if diff:
                logging.info(f"Análise JSON bem-sucedida. Encontradas {len(diff)} categorias de diferenças.")
                result_data['diff_lines_original'] = [{'content': format_deepdiff(diff), 'type': 'context', 'line_num': 1}]
                result_data['summary'] = {'removals': len(diff.get('dictionary_item_removed', [])), 'additions': len(diff.get('dictionary_item_added', [])), 'changes': len(diff.get('values_changed', [])) + len(diff.get('type_changes', []))}
            else:
                logging.info("Análise JSON bem-sucedida. Nenhuma diferença encontrada.")
                result_data['diff_lines_original'] = [{'content': "Nenhuma diferença encontrada.", 'type': 'none', 'line_num': 1}]
        
        else: # Se não for JSON, é texto simples
            logging.info("Recorrendo à comparação de texto simples.")
            result_data['diff_type'] = "Texto"
            original_lines = original_content.splitlines()
            altered_lines = altered_content.splitlines()
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