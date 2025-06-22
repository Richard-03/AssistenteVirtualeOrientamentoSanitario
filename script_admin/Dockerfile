FROM python:3.8.20

WORKDIR /app

# Installa mariadb-dev e build-essential per compilare mariadb client
RUN apt-get update && apt-get install -y \
    mariadb-client \
    libmariadb-dev \
    gcc \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY . . 

RUN pip install mariadb
RUN pip install bcrypt

CMD ["python", "crea_admin.py"]
