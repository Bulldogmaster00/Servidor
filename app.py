import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Define o diretório onde os arquivos serão armazenados
UPLOAD_FOLDER = '/home/pi/meg_cloud_files' # Altere este caminho para onde você quer armazenar os arquivos
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER) # Cria o diretório se ele não existir

app = Flask(__name__)
CORS(app) # Habilita CORS para permitir requisições do seu front-end
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return "Servidor Meg Cloud do Raspberry Pi está rodando!"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "Nenhum arquivo na requisição"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Nenhum arquivo selecionado"}), 400
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": f"Arquivo '{filename}' enviado para a Meg Cloud!"}), 200

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify(files), 200

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"message": f"Arquivo '{filename}' excluído da Meg Cloud!"}), 200
    return jsonify({"message": "Arquivo não encontrado na Meg Cloud"}), 404

if __name__ == '__main__':
    # Rodar o servidor em todas as interfaces de rede na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
