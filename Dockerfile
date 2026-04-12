# Usamos a versão 3.11 que é a mais estável para esse projeto
FROM python:3.11-slim

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define a pasta de trabalho dentro do servidor
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev libssl-dev && rm -rf /var/lib/apt/lists/*

# Instala as bibliotecas do Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copia o resto dos arquivos do projeto
COPY . .

# Expõe a porta que o Render vai usar
EXPOSE 10000

# Comando para iniciar o servidor com eventlet (obrigatório para Socket.io)
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:10000", "app:app"]