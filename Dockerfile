# Passo 1: Usar uma imagem base oficial do Python.
# Usamos a versão 'bullseye' (baseada em Debian 11) que tem boa compatibilidade de pacotes.
FROM python:3.11-bullseye

# Passo 2: Instalar as dependências do sistema operacional necessárias para o Tkinter.
# -y aceita automaticamente qualquer prompt
# python3-tk é o pacote para a biblioteca gráfica Tkinter
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Passo 3: Definir o diretório de trabalho dentro do container.
WORKDIR /app

# Passo 4: Copiar o arquivo de dependências e instalar as bibliotecas Python.
# Copiar primeiro o requirements.txt aproveita o cache do Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Passo 5: Copiar o restante do código da aplicação para o diretório de trabalho.
COPY . .

# Passo 6: Definir o comando para executar a aplicação quando o container iniciar.
CMD ["python", "main.py"]