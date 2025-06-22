-- Creazione del database e selezione
DROP DATABASE IF EXISTS user_db;
CREATE DATABASE IF NOT EXISTS user_db;
USE user_db;


--admin 
CREATE TABLE IF NOT EXISTS Admin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);
-- AREA PAZIENTE
CREATE TABLE IF NOT EXISTS Cliente (
    id INT AUTO_INCREMENT,
    nome VARCHAR(20) NOT NULL,
    cognome VARCHAR(20) NOT NULL,
    indirizzo VARCHAR(255),
    citta VARCHAR(100),
    email VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    eta INT NOT NULL,
    sesso ENUM('M', 'F', 'Altro') DEFAULT 'Altro',
    peso DECIMAL(5,2) NOT NULL,
    altezza DECIMAL(5,2) NOT NULL,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',

    -- Vincoli
    CONSTRAINT pk_cliente PRIMARY KEY (id),
    CONSTRAINT uq_cliente_email UNIQUE (email),
    CONSTRAINT chk_cliente_eta CHECK (eta >= 0),
    CONSTRAINT chk_cliente_sesso CHECK (sesso IN ('M', 'F', 'Altro'))
);

CREATE TABLE IF NOT EXISTS IntolleranzaAlimentare (
    id INT AUTO_INCREMENT,
    id_cliente INT NOT NULL,
    intolleranza VARCHAR(255) NOT NULL,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',

    -- Vincoli
    CONSTRAINT pk_intolleranza PRIMARY KEY (id),
    CONSTRAINT fk_intolleranza_cliente FOREIGN KEY (id_cliente)
        REFERENCES Cliente(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS CondizioniPatologichePregresse (
    id INT AUTO_INCREMENT,
    id_cliente INT NOT NULL,
    condizione_preg VARCHAR(255) NOT NULL,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',

    -- Vincoli
    CONSTRAINT pk_cppregresse PRIMARY KEY (id),
    CONSTRAINT fk_cppregresse_cliente FOREIGN KEY (id_cliente)
        REFERENCES Cliente(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS CondizioniPatologicheFamiliari (
    id INT AUTO_INCREMENT,
    id_cliente INT NOT NULL,
    condizione_fam VARCHAR(255) NOT NULL,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',

    -- Vincoli
    CONSTRAINT pk_cpfamiliari PRIMARY KEY (id),
    CONSTRAINT fk_cpfamiliari_cliente FOREIGN KEY (id_cliente)
        REFERENCES Cliente(id) ON DELETE CASCADE
);

-- AREA MEDICO
CREATE TABLE IF NOT EXISTS Medico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(20) NOT NULL,
    indirizzo VARCHAR(255) NOT NULL DEFAULT '',
    cognome VARCHAR(20) NOT NULL,
    codice_fiscale VARCHAR(16) NOT NULL,
    numero_albo VARCHAR(20) NOT NULL,
    citta_ordine VARCHAR(100),
    data_iscrizione_albo DATE NOT NULL,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    citta VARCHAR(100),
    telefono VARCHAR(20),
    url_sito VARCHAR(2083),
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',
    verificato BOOLEAN NOT NULL DEFAULT 0,

    -- Vincoli
    CONSTRAINT uq_medico_email UNIQUE (email)
    -- Gli altri vincoli come formati possono essere aggiunti se necessario
);

CREATE TABLE IF NOT EXISTS Specializzazione (
    id INT AUTO_INCREMENT,
    id_medico INT NOT NULL,
    specializzazione VARCHAR(255) NOT NULL,
    ranking DECIMAL(5,2) DEFAULT 0.00,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',
    indirizzo VARCHAR(255) NOT NULL,
    latitudine DECIMAL(10,7) NOT NULL,
    longitudine DECIMAL(10,7) NOT NULL,

    -- Vincoli
    CONSTRAINT pk_specializzazione PRIMARY KEY (id),
    CONSTRAINT fk_specializzazione_medico FOREIGN KEY (id_medico)
        REFERENCES Medico(id) ON DELETE CASCADE,
    CONSTRAINT chk_ranking CHECK (ranking >= 0 AND ranking <= 10.00)
);



CREATE TABLE IF NOT EXISTS Agenda (
    id INT AUTO_INCREMENT,
    id_medico INT NOT NULL,
    appuntamento TIMESTAMP NOT NULL,
    id_cliente INT NOT NULL,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',

    -- Vincoli
    CONSTRAINT pk_agenda PRIMARY KEY (id),
    CONSTRAINT fk_agenda_medico FOREIGN KEY (id_medico)
        REFERENCES Medico(id) ON DELETE CASCADE,
    CONSTRAINT fk_agenda_cliente FOREIGN KEY (id_cliente)
        REFERENCES Cliente(id) -- ON DELETE SET NULL
);


-- AREA CHAT
CREATE TABLE IF NOT EXISTS Chat(
    id INT AUTO_INCREMENT,
    id_cliente INT NOT NULL,
    numero_chat INT,
    domanda VARCHAR(2000),
    risposta VARCHAR(2000),
    reparto_consigliato VARCHAR(255) DEFAULT NULL,
    id_medico INT DEFAULT NULL,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',
    
    CONSTRAINT pk_chat PRIMARY KEY (id),
    CONSTRAINT fk_chat_cliente FOREIGN KEY (id_cliente) REFERENCES Cliente(id),
    CONSTRAINT fk_chat_medico FOREIGN KEY (id_medico) REFERENCES Medico(id),
    CONSTRAINT chk_numero_chat CHECK (numero_chat > 0)
);


-- AREA APPUNTAMENTO
CREATE TABLE IF NOT EXISTS Appuntamento (
    id INT AUTO_INCREMENT,
    id_cliente INT NOT NULL,
    id_medico INT NOT NULL,
    data_registrazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_appuntamento TIMESTAMP NOT NULL,
    stato ENUM('Prenotato', 'Effettuato', 'Eliminato') DEFAULT 'Prenotato',
    patologia_individuata VARCHAR(255) NULL,

    -- Vincoli
    CONSTRAINT pk_appuntamento PRIMARY KEY (id),
    CONSTRAINT fk_appuntamento_cliente FOREIGN KEY (id_cliente)
        REFERENCES Cliente(id) ON DELETE CASCADE,
    CONSTRAINT fk_appuntamento_medico FOREIGN KEY (id_medico)
        REFERENCES Medico(id) ON DELETE CASCADE,
    CONSTRAINT chk_data_appuntamento CHECK (data_appuntamento > data_registrazione),
    CONSTRAINT chk_patologia_stato CHECK (
        (stato = 'Effettuato' AND patologia_individuata IS NOT NULL) OR
        (stato IN ('Prenotato', 'Eliminato') AND patologia_individuata IS NULL)
    )
);  

-- Tabella per tracciare il ranking degli appuntamenti
CREATE TABLE IF NOT EXISTS RankingAppuntamento (
    id INT AUTO_INCREMENT,
    id_appuntamento INT NOT NULL,
    id_medico INT NOT NULL,
    voto DECIMAL(3,2) NOT NULL,
    commento TEXT,
    data_ranking TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stato ENUM('Attivo', 'Eliminato') DEFAULT 'Attivo',

    -- Vincoli
    CONSTRAINT pk_ranking_appuntamento PRIMARY KEY (id),
    CONSTRAINT fk_ranking_appuntamento FOREIGN KEY (id_appuntamento)
        REFERENCES Appuntamento(id) ON DELETE CASCADE,
    CONSTRAINT fk_ranking_medico FOREIGN KEY (id_medico)
        REFERENCES Medico(id) ON DELETE CASCADE,
    CONSTRAINT uq_ranking_appuntamento UNIQUE (id_appuntamento),
    CONSTRAINT chk_voto CHECK (voto >= 1.00 AND voto <= 10.00)
);


-- eliminata tabella MedicoSuggerito