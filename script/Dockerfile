FROM python:3.8.20

WORKDIR /app

# Installa mariadb-dev e build-essential per compilare mariadb client
RUN apt-get update && apt-get install -y \
    mariadb-client \
    libmariadb-dev \
    gcc \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY popola_db.py /app/popola_db.py
COPY clienti_csv.csv /app/clienti_csv.csv
COPY medici_csv.csv /app/medici_csv.csv

RUN pip install mariadb
RUN pip install bcrypt

CMD ["python", "popola_db.py"]
