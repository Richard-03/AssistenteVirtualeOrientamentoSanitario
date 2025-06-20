FROM mariadb:10.11

# Copia lo script di inizializzazione
COPY init_db.sql /docker-entrypoint-initdb.d/

# Imposta i permessi corretti
RUN chmod 644 /docker-entrypoint-initdb.d/init_db.sql

# Configurazione aggiuntiva per MariaDB
ENV MARIADB_AUTO_UPGRADE=1
ENV MARIADB_DISABLE_UPGRADE_BACKUP=1

# Esposizione della porta
EXPOSE 3306