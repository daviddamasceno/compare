# Usa uma imagem Python leve como base
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os outros arquivos do projeto
COPY . .

# Expõe a porta 8000, que é a porta que o nosso servidor vai usar
EXPOSE 8000

# Comando para iniciar o servidor Gunicorn em produção quando o container iniciar
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "app:app"]