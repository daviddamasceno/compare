import json
from flask import Flask, render_template, request, jsonify
from difflib import Differ
from deepdiff import DeepDiff

# Inicializa a aplicação Flask
app = Flask(__name__)

@app.route('/')
def index():
    """ Rota principal que serve a página web (frontend). """
    return render_template('index.html')

@app.route('/api/compare', methods=['POST'])
def compare_api():
    """ Endpoint da API que recebe os textos e retorna a diferença. """
    data = request.json
    original_content = data.get('original', '')
    altered_content = data.get('altered', '')
    result_text = ""
    diff_type = "Texto"

    # Tenta a comparação como JSON primeiro
    try:
        original_json = json.loads(original_content)
        altered_json = json.loads(altered_content)
        diff = DeepDiff(original_json, altered_json, view='text', verbose_level=0)
        diff_type = "JSON/Objeto"
        if diff:
            result_text = diff
        else:
            result_text = "Nenhuma diferença encontrada."
    except json.JSONDecodeError:
        # Se não for JSON, compara como texto plano
        d = Differ()
        diff_lines = list(d.compare(original_content.splitlines(), altered_content.splitlines()))
        
        has_diff = any(line.startswith('+ ') or line.startswith('- ') or line.startswith('? ') for line in diff_lines)

        if has_diff:
            result_text = "\n".join(diff_lines)
        else:
            result_text = "Nenhuma diferença encontrada."

    return jsonify({
        'diff': result_text,
        'type': diff_type
    })

if __name__ == '__main__':
    # Este modo é apenas para desenvolvimento local, não usado em produção.
    app.run(debug=True, port=5000)