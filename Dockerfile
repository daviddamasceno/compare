# Estágio 1: Base Python
FROM python:3.11-slim as base

# Evita que o Python escreva arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que o output do Python seja enviado diretamente, sem buffer
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Estágio 2: Imagem final
FROM base

WORKDIR /app

# Copia os arquivos da aplicação
COPY . .

# Expõe a porta que o Gunicorn irá usar
EXPOSE 8000

# Comando para iniciar o servidor Gunicorn em produção
# --workers 3: Um bom número de processos para uma aplicação pequena
# --bind 0.0.0.0:8000: Permite que o container seja acessado de fora
# app:app: Aponta para o objeto 'app' dentro do arquivo 'app.py'
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "app:app"]