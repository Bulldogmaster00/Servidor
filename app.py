import os
import shutil
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv # Importa load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Este arquivo (.env) deve estar no mesmo diretório que app.py
load_dotenv()

app = Flask(__name__)
CORS(app) # Habilita CORS para todas as rotas

# --- Configurações ---
# O diretório onde os arquivos serão armazenados no Raspberry Pi.
# Pega o caminho do UPLOAD_FOLDER do arquivo .env.
# Se não estiver definido no .env, usa '/home/pi/meg_cloud_files' como padrão.
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/home/pi/meg_cloud_files')

# Senha de administrador para acesso, lida do arquivo .env
# Certifique-se de definir ADMIN_PASSWORD no seu arquivo .env
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Verifica se o UPLOAD_FOLDER existe, caso contrário, tenta criá-lo
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
        print(f"Diretório de upload '{UPLOAD_FOLDER}' criado com sucesso.")
    except OSError as e:
        print(f"Erro ao criar o diretório de upload '{UPLOAD_FOLDER}': {e}")
        print("Verifique as permissões ou se o caminho é válido para o seu 'Frozen OS'.")
        # Se o diretório não puder ser criado, a aplicação pode não funcionar corretamente.

# --- Rotas da API ---

@app.route('/')
def home():
    return "Servidor Meg Cloud do Raspberry Pi está rodando!"

@app.route('/login', methods=['POST'])
def login():
    """
    Endpoint para autenticação do usuário.
    Recebe a senha via POST e verifica contra a senha definida no .env.
    """
    data = request.get_json()
    password = data.get('password')

    if not ADMIN_PASSWORD:
        # Isso é um erro de configuração do servidor, não do usuário.
        return jsonify({"message": "Erro no servidor: Senha de administrador não configurada no .env"}), 500

    if password == ADMIN_PASSWORD:
        return jsonify({"message": "Login bem-sucedido!"}), 200
    else:
        return jsonify({"message": "Senha incorreta."}), 401

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para upload de arquivos.
    """
    if 'file' not in request.files:
        return jsonify({"message": "Nenhum arquivo na requisição"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Nenhum arquivo selecionado"}), 400

    if file:
        try:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            return jsonify({"message": f"Arquivo '{file.filename}' enviado com sucesso!"}), 200
        except Exception as e:
            return jsonify({"message": f"Erro ao salvar o arquivo: {e}"}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """
    Endpoint para listar todos os arquivos e diretórios no UPLOAD_FOLDER.
    Retorna uma uma lista de objetos com nome e tipo (arquivo/diretório).
    """
    try:
        items = []
        for item_name in os.listdir(UPLOAD_FOLDER):
            item_path = os.path.join(UPLOAD_FOLDER, item_name)
            if os.path.isfile(item_path):
                items.append({"name": item_name, "type": "file"})
            elif os.path.isdir(item_path):
                items.append({"name": item_name, "type": "directory"})
        return jsonify(items), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao listar arquivos: {e}"}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Endpoint para download de um arquivo específico.
    """
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"message": "Arquivo não encontrado."}), 404
    except Exception as e:
        return jsonify({"message": f"Erro ao baixar arquivo: {e}"}), 500

@app.route('/delete/<item_name>', methods=['DELETE'])
def delete_item(item_name):
    """
    Endpoint para exclusão de um arquivo ou diretório (recursivamente).
    """
    try:
        item_path = os.path.join(UPLOAD_FOLDER, item_name)
        if os.path.exists(item_path):
            if os.path.isfile(item_path):
                os.remove(item_path)
                return jsonify({"message": f"Arquivo '{item_name}' excluído com sucesso!"}), 200
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path) # Exclui diretório e seu conteúdo
                return jsonify({"message": f"Pasta '{item_name}' excluída com sucesso!"}), 200
        else:
            return jsonify({"message": "Item não encontrado."}), 404
    except Exception as e:
        return jsonify({"message": f"Erro ao excluir '{item_name}': {e}"}), 500

@app.route('/create_folder', methods=['POST'])
def create_folder():
    """
    Endpoint para criar uma nova pasta.
    """
    data = request.get_json()
    folder_name = data.get('folder_name')

    if not folder_name:
        return jsonify({"message": "Nome da pasta não fornecido."}), 400

    folder_path = os.path.join(UPLOAD_FOLDER, folder_name)

    if os.path.exists(folder_path):
        return jsonify({"message": f"Pasta '{folder_name}' já existe."}), 409 # Conflict
    
    try:
        os.makedirs(folder_path)
        return jsonify({"message": f"Pasta '{folder_name}' criada com sucesso!"}), 201 # Created
    except Exception as e:
        return jsonify({"message": f"Erro ao criar pasta: {e}"}), 500

# Endpoint para servir arquivos para visualização (sem download forçado)
@app.route('/view/<filename>', methods=['GET'])
def view_file(filename):
    """
    Endpoint para visualizar um arquivo diretamente no navegador.
    Não força o download, permitindo que o navegador exiba imagens/vídeos.
    """
    try:
        return send_from_directory(UPLOAD_FOLDER, filename) # Sem as_attachment=True
    except FileNotFoundError:
        return jsonify({"message": "Arquivo não encontrado."}), 404
    except Exception as e:
        return jsonify({"message": f"Erro ao visualizar arquivo: {e}"}), 500


if __name__ == '__main__':
    # Esta parte só é executada se o script for rodado diretamente (para testes).
    # Para produção, use Gunicorn ou similar, conforme configurado no serviço systemd.
    app.run(host='0.0.0.0', port=5000)
