USE user_db;




-- STORED PROCEDURE COMPLETA PER INSERIRE CLIENTE
DELIMITER //

DROP PROCEDURE IF EXISTS insert_cliente_completo//

CREATE PROCEDURE insert_cliente_completo(
    IN c_nome VARCHAR(20),
    IN c_cognome VARCHAR(20),
    IN c_indirizzo VARCHAR(255),
    IN c_citta VARCHAR(100),
    IN c_email VARCHAR(100),
    IN c_password VARCHAR(255),
    IN c_eta INT,
    IN c_sesso ENUM('M', 'F', 'Altro'),
    IN c_peso DECIMAL(5,2),
    IN c_altezza DECIMAL(5,2),
    -- Parametri per intolleranze (separati da virgola)
    IN intolleranze TEXT,
    -- Parametri per condizioni patologiche pregresse (separati da virgola)
    IN condizioni_pregresse TEXT,
    -- Parametri per condizioni patologiche familiari (separati da virgola)
    IN condizioni_familiari TEXT,
    IN farmaci TEXT
)
BEGIN
    DECLARE cliente_id INT DEFAULT 0;
    DECLARE temp_intolleranza VARCHAR(255) DEFAULT '';
    DECLARE temp_condizione_preg VARCHAR(255) DEFAULT '';
    DECLARE temp_condizione_fam VARCHAR(255) DEFAULT '';
    DECLARE comma_pos INT DEFAULT 0;
    DECLARE remaining_text TEXT DEFAULT '';
    
    -- Gestione errori
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    -- Inizio transazione
    START TRANSACTION;
    
    -- Inserimento del cliente principale
    INSERT INTO Cliente (
        nome, 
        cognome, 
        indirizzo, 
        citta, 
        email, 
        password, 
        eta, 
        sesso, 
        peso, 
        altezza,
        stato
    ) VALUES (
        c_nome, 
        c_cognome, 
        c_indirizzo, 
        c_citta, 
        c_email, 
        c_password, 
        c_eta, 
        c_sesso, 
        c_peso, 
        c_altezza,
        'Attivo'
    );
    
    -- Ottenere l'ID del cliente appena inserito
    SET cliente_id = LAST_INSERT_ID();
    
    -- Inserimento intolleranze alimentari (se presenti)
    IF intolleranze IS NOT NULL AND LENGTH(TRIM(intolleranze)) > 0 THEN
        SET remaining_text = CONCAT(TRIM(intolleranze), ',');
        
        WHILE LOCATE(',', remaining_text) > 0 DO
            SET comma_pos = LOCATE(',', remaining_text);
            SET temp_intolleranza = TRIM(SUBSTRING(remaining_text, 1, comma_pos - 1));
            SET remaining_text = SUBSTRING(remaining_text, comma_pos + 1);
            
            IF LENGTH(temp_intolleranza) > 0 THEN
                INSERT INTO IntolleranzaAlimentare (id_cliente, intolleranza, stato)
                VALUES (cliente_id, temp_intolleranza, 'Attivo');
            END IF;
        END WHILE;
    END IF;
    
    -- Inserimento condizioni patologiche pregresse (se presenti)
    IF condizioni_pregresse IS NOT NULL AND LENGTH(TRIM(condizioni_pregresse)) > 0 THEN
        SET remaining_text = CONCAT(TRIM(condizioni_pregresse), ',');
        
        WHILE LOCATE(',', remaining_text) > 0 DO
            SET comma_pos = LOCATE(',', remaining_text);
            SET temp_condizione_preg = TRIM(SUBSTRING(remaining_text, 1, comma_pos - 1));
            SET remaining_text = SUBSTRING(remaining_text, comma_pos + 1);
            
            IF LENGTH(temp_condizione_preg) > 0 THEN
                INSERT INTO CondizioniPatologichePregresse (id_cliente, condizione_preg, stato)
                VALUES (cliente_id, temp_condizione_preg, 'Attivo');
            END IF;
        END WHILE;
    END IF;
    
    -- Inserimento condizioni patologiche familiari (se presenti)
    IF condizioni_familiari IS NOT NULL AND LENGTH(TRIM(condizioni_familiari)) > 0 THEN
        SET remaining_text = CONCAT(TRIM(condizioni_familiari), ',');
        
        WHILE LOCATE(',', remaining_text) > 0 DO
            SET comma_pos = LOCATE(',', remaining_text);
            SET temp_condizione_fam = TRIM(SUBSTRING(remaining_text, 1, comma_pos - 1));
            SET remaining_text = SUBSTRING(remaining_text, comma_pos + 1);
            
            IF LENGTH(temp_condizione_fam) > 0 THEN
                INSERT INTO CondizioniPatologicheFamiliari (id_cliente, condizione_fam, stato)
                VALUES (cliente_id, temp_condizione_fam, 'Attivo');
            END IF;
        END WHILE;
    END IF;
    
    -- Confermare la transazione
    COMMIT;
    
    -- Restituire l'ID del cliente creato
    SELECT cliente_id AS nuovo_cliente_id;
    
END//

DELIMITER ;

DROP PROCEDURE IF EXISTS insert_medico_completo;

DELIMITER //
CREATE PROCEDURE insert_medico_completo(
    IN m_nome VARCHAR(20),
    IN m_cognome VARCHAR(20),
    IN m_codice_fiscale VARCHAR(16),
    IN m_numero_albo VARCHAR(20),
    IN m_citta_ordine VARCHAR(100),
    IN m_data_iscrizione_albo DATE,
    IN m_citta VARCHAR(100),
    IN m_email VARCHAR(100),
    IN m_password VARCHAR(255),
    IN m_telefono VARCHAR(20),
    IN m_url_sito VARCHAR(2083),
    IN m_indirizzo VARCHAR(255)
)
BEGIN
    DECLARE last_medico_id INT;

    START TRANSACTION;

    INSERT INTO Medico (
        nome, indirizzo, cognome, codice_fiscale, numero_albo, citta_ordine,
        data_iscrizione_albo, citta, email, password, telefono, url_sito, stato
    ) VALUES (
        m_nome, m_indirizzo, m_cognome, m_codice_fiscale, m_numero_albo, m_citta_ordine,
        m_data_iscrizione_albo, m_citta, m_email, m_password, m_telefono, m_url_sito, 'Attivo'
    );

    SET last_medico_id = LAST_INSERT_ID();

    COMMIT;

    SELECT last_medico_id AS nuovo_medico_id;
END//

DELIMITER ;


-- STORED PROCEDURE AGGIORNATA PER INSERIRE MEDICO COMPLETO CON SPECIALIZZAZIONE
DROP PROCEDURE IF EXISTS insert_medico_completo_csv;

DELIMITER //
CREATE PROCEDURE insert_medico_completo_csv(
    IN m_nome VARCHAR(20),
    IN m_cognome VARCHAR(20),
    IN m_codice_fiscale VARCHAR(16),
    IN m_numero_albo VARCHAR(20),
    IN m_citta_ordine VARCHAR(100),
    IN m_data_iscrizione_albo DATE,
    IN m_citta VARCHAR(100),
    IN m_email VARCHAR(100),
    IN m_password VARCHAR(255),
    IN m_telefono VARCHAR(20),
    IN m_url_sito VARCHAR(2083),
    IN m_indirizzo VARCHAR(255),
    -- Nuovi parametri per la specializzazione
    IN m_specializzazioni TEXT,
    IN m_coordinate VARCHAR(50) -- formato: "latitudine,longitudine"
)
BEGIN
    DECLARE last_medico_id INT;
    DECLARE comma_pos INT DEFAULT 0;
    DECLARE temp_specializzazione VARCHAR(255) DEFAULT '';
    DECLARE remaining_specializzazioni TEXT DEFAULT '';
    DECLARE latitudine_val DECIMAL(10,7) DEFAULT 0;
    DECLARE longitudine_val DECIMAL(10,7) DEFAULT 0;
    
    -- Gestione errori
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Inserimento del medico principale
    INSERT INTO Medico (
        nome, indirizzo, cognome, codice_fiscale, numero_albo, citta_ordine,
        data_iscrizione_albo, citta, email, password, telefono, url_sito, stato, verificato
    ) VALUES (
        m_nome, m_indirizzo, m_cognome, m_codice_fiscale, m_numero_albo, m_citta_ordine,
        m_data_iscrizione_albo, m_citta, m_email, m_password, m_telefono, m_url_sito, 'Attivo', 1
    );

    SET last_medico_id = LAST_INSERT_ID();

    -- Estrazione delle coordinate se fornite
    IF m_coordinate IS NOT NULL AND LENGTH(TRIM(m_coordinate)) > 0 THEN
        SET comma_pos = LOCATE(',', m_coordinate);
        IF comma_pos > 0 THEN
            SET latitudine_val = CAST(TRIM(SUBSTRING(m_coordinate, 1, comma_pos - 1)) AS DECIMAL(10,7));
            SET longitudine_val = CAST(TRIM(SUBSTRING(m_coordinate, comma_pos + 1)) AS DECIMAL(10,7));
        END IF;
    END IF;

    -- Inserimento specializzazioni (se presenti)
    IF m_specializzazioni IS NOT NULL AND LENGTH(TRIM(m_specializzazioni)) > 0 THEN
        SET remaining_specializzazioni = CONCAT(TRIM(m_specializzazioni), ',');
        
        WHILE LOCATE(',', remaining_specializzazioni) > 0 DO
            SET comma_pos = LOCATE(',', remaining_specializzazioni);
            SET temp_specializzazione = TRIM(SUBSTRING(remaining_specializzazioni, 1, comma_pos - 1));
            SET remaining_specializzazioni = SUBSTRING(remaining_specializzazioni, comma_pos + 1);
            
            IF LENGTH(temp_specializzazione) > 0 THEN
                INSERT INTO Specializzazione (
                    id_medico, 
                    specializzazione, 
                    ranking, 
                    stato, 
                    indirizzo, 
                    latitudine, 
                    longitudine
                ) VALUES (
                    last_medico_id, 
                    temp_specializzazione, 
                    0.00, 
                    'Attivo', 
                    m_indirizzo, 
                    latitudine_val, 
                    longitudine_val
                );
            END IF;
        END WHILE;
    END IF;

    COMMIT;

    SELECT last_medico_id AS nuovo_medico_id;
END//

DELIMITER ;


-- PROCEDURRE PER GESTIRE LE CHAT

-- Creazione nuova Chat
DELIMITER //

CREATE PROCEDURE insert_chat(
    IN p_id_cliente INT,
    IN p_domanda VARCHAR(2000),
    IN p_risposta VARCHAR(2000),
    IN p_reparto_consigliato VARCHAR(255),
    IN p_id_medico INT
)
BEGIN
    DECLARE v_numero_chat INT DEFAULT 1;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Calcola il prossimo numero_chat per il cliente
    SELECT COALESCE(MAX(numero_chat), 0) + 1 
    INTO v_numero_chat
    FROM Chat 
    WHERE id_cliente = p_id_cliente 
    AND stato = 'Attivo';
    
    -- Inserisce il nuovo record
    INSERT INTO Chat (
        id_cliente,
        numero_chat,
        domanda,
        risposta,
        reparto_consigliato,
        id_medico,
        stato
    ) VALUES (
        p_id_cliente,
        v_numero_chat,
        p_domanda,
        p_risposta,
        p_reparto_consigliato,
        id_medico,
        'Attivo'
    );
    
    COMMIT;
    
    -- Restituisce l'ID del record inserito e il numero_chat assegnato
    SELECT LAST_INSERT_ID() as id_inserito, v_numero_chat as numero_chat_assegnato;
    
END //

DELIMITER ;

-- Scrittura su vecchia Chat
DELIMITER //

CREATE PROCEDURE update_chat(
    IN p_id_cliente INT,
    IN p_numero_chat INT,
    IN p_domanda VARCHAR(2000),
    IN p_risposta VARCHAR(2000),
    IN p_reparto_consigliato VARCHAR(255),
    IN p_id_medico INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Inserisce sempre un nuovo record con il numero_chat specificato
    INSERT INTO Chat (
        id_cliente,
        numero_chat,
        domanda,
        risposta,
        reparto_consigliato,
        id_medico,
        stato
    ) VALUES (
        p_id_cliente,
        p_numero_chat,
        p_domanda,
        p_risposta,
        p_reparto_consigliato,
        p_id_medico,
        'Attivo'
    );
    
    COMMIT;
    
    -- Restituisce l'ID del nuovo record inserito
    SELECT 
        LAST_INSERT_ID() as id_inserito,
        p_id_cliente as id_cliente,
        p_numero_chat as numero_chat,
        p_id_medico as id_medico,
        'Nuovo messaggio aggiunto alla chat' as messaggio;
    
END //

DELIMITER ;

-- STORED PROCEDURES PER GESTIRE LA TABELLA AGENDA

-- Procedure per inserire un nuovo appuntamento in agenda
-- Se esiste già un record eliminato con gli stessi dati, lo riattiva
DELIMITER //

DROP PROCEDURE IF EXISTS insert_appuntamento//

CREATE PROCEDURE insert_appuntamento(
    IN p_id_medico INT,
    IN p_appuntamento TIMESTAMP,
    IN p_id_cliente INT
)
BEGIN
    DECLARE existing_id INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Verifica se esiste già un record con gli stessi dati ma stato 'Eliminato'
    SELECT id INTO existing_id
    FROM Agenda 
    WHERE id_medico = p_id_medico 
        AND appuntamento = p_appuntamento 
        AND id_cliente = p_id_cliente 
        AND stato = 'Eliminato'
    LIMIT 1;
    
    IF existing_id > 0 THEN
        -- Se esiste un record eliminato, riattivalo
        UPDATE Agenda 
        SET stato = 'Attivo'
        WHERE id = existing_id;
        
        COMMIT;
        
        SELECT 
            existing_id AS id_appuntamento,
            'Appuntamento riattivato' AS messaggio,
            p_id_medico AS id_medico,
            p_appuntamento AS appuntamento,
            p_id_cliente AS id_cliente;
    ELSE
        -- Verifica che non esista già un appuntamento attivo con gli stessi dati
        IF EXISTS (
            SELECT 1 FROM Agenda 
            WHERE id_medico = p_id_medico 
                AND appuntamento = p_appuntamento 
                AND id_cliente = p_id_cliente 
                AND stato = 'Attivo'
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento già esistente e attivo per questi parametri';
        END IF;
        
        -- Verifica che il medico esista e sia attivo
        IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = p_id_medico AND stato = 'Attivo') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non trovato o non attivo';
        END IF;
        
        -- Verifica che il cliente esista e sia attivo
        IF NOT EXISTS (SELECT 1 FROM Cliente WHERE id = p_id_cliente AND stato = 'Attivo') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente non trovato o non attivo';
        END IF;
        
        -- Verifica che la data dell'appuntamento sia futura
        IF p_appuntamento <= NOW() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "La data dell'appuntamento deve essere futura";
        END IF;
        
        -- Inserisci il nuovo appuntamento
        INSERT INTO Agenda (
            id_medico,
            appuntamento,
            id_cliente,
            stato
        ) VALUES (
            p_id_medico,
            p_appuntamento,
            p_id_cliente,
            'Attivo'
        );
        
        COMMIT;
        
        SELECT 
            LAST_INSERT_ID() AS id_appuntamento,
            'Nuovo appuntamento creato' AS messaggio,
            p_id_medico AS id_medico,
            p_appuntamento AS appuntamento,
            p_id_cliente AS id_cliente;
    END IF;
    
END//

DELIMITER ;


-- Procedure per eliminare logicamente un appuntamento dall'agenda
DELIMITER //

DROP PROCEDURE IF EXISTS elimina_appuntamento_logico//

CREATE PROCEDURE elimina_appuntamento_logico(
    IN p_id_appuntamento INT
)
BEGIN
    DECLARE appuntamento_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Verifica che l'appuntamento esista e sia attivo
    SELECT COUNT(*) INTO appuntamento_count
    FROM Agenda 
    WHERE id = p_id_appuntamento AND stato = 'Attivo';
    
    IF appuntamento_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o già eliminato';
    END IF;
    
    -- Elimina logicamente l'appuntamento
    UPDATE Agenda 
    SET stato = 'Eliminato'
    WHERE id = p_id_appuntamento;
    
    COMMIT;
    
    SELECT 
        p_id_appuntamento AS id_appuntamento_eliminato,
        'Appuntamento eliminato logicamente' AS messaggio;
    
END//

DELIMITER ;


-- Procedure aggiuntiva per riattivare un appuntamento eliminato
DELIMITER //

DROP PROCEDURE IF EXISTS riattiva_appuntamento//

CREATE PROCEDURE riattiva_appuntamento(
    IN p_id_appuntamento INT
)
BEGIN
    DECLARE appuntamento_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Verifica che l'appuntamento esista e sia eliminato
    SELECT COUNT(*) INTO appuntamento_count
    FROM Agenda 
    WHERE id = p_id_appuntamento AND stato = 'Eliminato';
    
    IF appuntamento_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o già attivo';
    END IF;
    
    -- Riattiva l'appuntamento
    UPDATE Agenda 
    SET stato = 'Attivo'
    WHERE id = p_id_appuntamento;
    
    COMMIT;
    
    SELECT 
        p_id_appuntamento AS id_appuntamento_riattivato,
        'Appuntamento riattivato' AS messaggio;
    
END//

DELIMITER ;


-- Procedure per eliminare logicamente tutti gli appuntamenti di un medico
DELIMITER //

DROP PROCEDURE IF EXISTS elimina_appuntamenti_medico//

CREATE PROCEDURE elimina_appuntamenti_medico(
    IN p_id_medico INT
)
BEGIN
    DECLARE appuntamenti_eliminati INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Elimina logicamente tutti gli appuntamenti attivi del medico
    UPDATE Agenda 
    SET stato = 'Eliminato'
    WHERE id_medico = p_id_medico AND stato = 'Attivo';
    
    -- Conta quanti appuntamenti sono stati eliminati
    SET appuntamenti_eliminati = ROW_COUNT();
    
    COMMIT;
    
    SELECT 
        p_id_medico AS id_medico,
        appuntamenti_eliminati AS appuntamenti_eliminati,
        'Appuntamenti del medico eliminati logicamente' AS messaggio;
    
END//

DELIMITER ;


-- Procedure per eliminare logicamente tutti gli appuntamenti di un cliente
DELIMITER //

DROP PROCEDURE IF EXISTS elimina_appuntamenti_cliente//

CREATE PROCEDURE elimina_appuntamenti_cliente(
    IN p_id_cliente INT
)
BEGIN
    DECLARE appuntamenti_eliminati INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Elimina logicamente tutti gli appuntamenti attivi del cliente
    UPDATE Agenda 
    SET stato = 'Eliminato'
    WHERE id_cliente = p_id_cliente AND stato = 'Attivo';
    
    -- Conta quanti appuntamenti sono stati eliminati
    SET appuntamenti_eliminati = ROW_COUNT();
    
    COMMIT;
    
    SELECT 
        p_id_cliente AS id_cliente,
        appuntamenti_eliminati AS appuntamenti_eliminati,
        'Appuntamenti del cliente eliminati logicamente' AS messaggio;
    
END//

DELIMITER ;








-- PROCEDURE PER GESTIRE GLI APPUNTAMENTI

-- Procedure per completare un appuntamento con diagnosi
DELIMITER //
CREATE PROCEDURE completa_appuntamento(
    IN appuntamento_id INT,
    IN diagnosi VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Aggiorna l'appuntamento come effettuato con la patologia individuata
    UPDATE Appuntamento 
    SET stato = 'Effettuato', 
        patologia_individuata = diagnosi
    WHERE id = appuntamento_id 
        AND stato = 'Prenotato';
    
    -- Verifica se l'update è stato effettuato
    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o già completato';
    END IF;
    
    COMMIT;
    
    SELECT 'Appuntamento completato con successo' AS messaggio;
END//

-- Procedure per aggiungere un ranking a un appuntamento
CREATE PROCEDURE aggiungi_ranking_appuntamento(
    IN appuntamento_id INT,
    IN voto DECIMAL(3,2),
    IN commento_ranking TEXT
)
BEGIN
    DECLARE medico_id_var INT;
    DECLARE nuovo_ranking DECIMAL(5,2);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Verifica che l'appuntamento sia effettuato
    SELECT id_medico INTO medico_id_var
    FROM Appuntamento 
    WHERE id = appuntamento_id AND stato = 'Effettuato';
    
    IF medico_id_var IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o non ancora effettuato';
    END IF;
    
    -- Verifica che non ci sia già un ranking per questo appuntamento
    IF EXISTS (SELECT 1 FROM RankingAppuntamento WHERE id_appuntamento = appuntamento_id AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ranking già presente per questo appuntamento';
    END IF;
    
    -- Inserisci il ranking
    INSERT INTO RankingAppuntamento (id_appuntamento, id_medico, voto, commento)
    VALUES (appuntamento_id, medico_id_var, voto, commento_ranking);
    
    -- Aggiorna il ranking medio del medico nella tabella Specializzazione
    SELECT AVG(ra.voto) INTO nuovo_ranking
    FROM RankingAppuntamento ra
    WHERE ra.id_medico = medico_id_var AND ra.stato = 'Attivo';
    
    UPDATE Specializzazione 
    SET ranking = nuovo_ranking
    WHERE id_medico = medico_id_var AND stato = 'Attivo';
    
    COMMIT;
    
    SELECT 'Ranking aggiunto con successo' AS messaggio, nuovo_ranking AS nuovo_ranking_medio;
END//

-- Procedure per ottenere dati anonimizzati di un paziente casuale senza ranking
CREATE PROCEDURE get_paziente_random_senza_ranking(
    IN medico_id INT
)
BEGIN
    DECLARE appuntamento_random INT DEFAULT 0;
    DECLARE paziente_id INT DEFAULT 0;
    
    -- Seleziona un appuntamento casuale effettuato dal medico senza ranking
    SELECT a.id, a.id_cliente INTO appuntamento_random, paziente_id
    FROM Appuntamento a
    WHERE a.id_medico = medico_id 
        AND a.stato = 'Effettuato'
        AND NOT EXISTS (
            SELECT 1 FROM RankingAppuntamento ra 
            WHERE ra.id_appuntamento = a.id AND ra.stato = 'Attivo'
        )
    ORDER BY RAND()
    LIMIT 1;
    
    IF appuntamento_random = 0 THEN
        SELECT 'Nessun appuntamento disponibile senza ranking per questo medico' AS messaggio;
    ELSE
        -- Restituisci dati anonimizzati del paziente
        SELECT 
            CONCAT('PAZ_', LPAD(paziente_id, 6, '0')) AS codice_paziente_anonimo,
            appuntamento_random AS id_appuntamento,
            c.eta AS eta,
            c.sesso AS sesso,
            c.peso AS peso,
            c.altezza AS altezza,
            a.data_appuntamento AS data_visita,
            a.patologia_individuata AS diagnosi,
            GROUP_CONCAT(DISTINCT i.intolleranza SEPARATOR ', ') AS intolleranze,
            GROUP_CONCAT(DISTINCT cpp.condizione_preg SEPARATOR ', ') AS condizioni_pregresse,
            GROUP_CONCAT(DISTINCT cpf.condizione_fam SEPARATOR ', ') AS condizioni_familiari
        FROM Cliente c
        JOIN Appuntamento a ON (c.id = a.id_cliente)
        LEFT JOIN IntolleranzaAlimentare i ON (c.id = i.id_cliente AND i.stato = 'Attivo')
        LEFT JOIN CondizioniPatologichePregresse cpp ON (c.id = cpp.id_cliente AND cpp.stato = 'Attivo')
        LEFT JOIN CondizioniPatologicheFamiliari cpf ON (c.id = cpf.id_cliente AND cpf.stato = 'Attivo')
        WHERE c.id = paziente_id 
            AND a.id = appuntamento_random
            AND c.stato = 'Attivo'
        GROUP BY c.id, a.id;
    END IF;
END//

-- Procedure per prenotare un nuovo appuntamento
CREATE PROCEDURE prenota_appuntamento(
    IN cliente_id INT,
    IN medico_id INT,
    IN data_app TIMESTAMP
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Verifica che cliente e medico siano attivi
    IF NOT EXISTS (SELECT 1 FROM Cliente WHERE id = cliente_id AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente non trovato o non attivo';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = medico_id AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non trovato o non attivo';
    END IF;
    
    -- Verifica che la data sia futura
    IF data_app <= NOW() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La data dell\'appuntamento deve essere futura';
    END IF;
    
    -- Inserisci l'appuntamento
    INSERT INTO Appuntamento (id_cliente, id_medico, data_appuntamento, stato)
    VALUES (cliente_id, medico_id, data_app, 'Prenotato');
    
    COMMIT;
    
    SELECT LAST_INSERT_ID() AS nuovo_appuntamento_id;
END//

DELIMITER ;

-- PROCEDURE AGGIUNTIVE PER GESTIRE LO STATO

-- Procedure per "eliminare" logicamente un cliente
DELIMITER //
CREATE PROCEDURE elimina_cliente_logico(
    IN cliente_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Elimina logicamente il cliente
    UPDATE Cliente SET stato = 'Eliminato' WHERE id = cliente_id;
    
    -- Elimina logicamente tutte le sue intolleranze
    UPDATE IntolleranzaAlimentare SET stato = 'Eliminato' WHERE id_cliente = cliente_id;
    
    -- Elimina logicamente tutte le sue condizioni pregresse
    UPDATE CondizioniPatologichePregresse SET stato = 'Eliminato' WHERE id_cliente = cliente_id;
    
    -- Elimina logicamente tutte le sue condizioni familiari
    UPDATE CondizioniPatologicheFamiliari SET stato = 'Eliminato' WHERE id_cliente = cliente_id;
    
    -- Elimina logicamente tutti i suoi appuntamenti
    UPDATE Appuntamento SET stato = 'Eliminato' WHERE id_cliente = cliente_id;
    
    COMMIT;
END//

-- Procedure per riattivare un cliente
CREATE PROCEDURE riattiva_cliente(
    IN cliente_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Riattiva il cliente
    UPDATE Cliente SET stato = 'Attivo' WHERE id = cliente_id;
    
    -- Riattiva tutte le sue intolleranze
    UPDATE IntolleranzaAlimentare SET stato = 'Attivo' WHERE id_cliente = cliente_id;
    
    -- Riattiva tutte le sue condizioni pregresse
    UPDATE CondizioniPatologichePregresse SET stato = 'Attivo' WHERE id_cliente = cliente_id;
    
    -- Riattiva tutte le sue condizioni familiari
    UPDATE CondizioniPatologicheFamiliari SET stato = 'Attivo' WHERE id_cliente = cliente_id;
    
    COMMIT;
END//

-- Procedure per eliminare logicamente un medico
CREATE PROCEDURE elimina_medico_logico(
    IN medico_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Elimina logicamente il medico
    UPDATE Medico SET stato = 'Eliminato' WHERE id = medico_id;
    
    -- Elimina logicamente tutte le sue specializzazioni
    UPDATE Specializzazione SET stato = 'Eliminato' WHERE id_medico = medico_id;
    
    -- Elimina logicamente la sua agenda
    UPDATE Agenda SET stato = 'Eliminato' WHERE id_medico = medico_id;
    
    -- Elimina logicamente tutti i suoi appuntamenti futuri
    UPDATE Appuntamento SET stato = 'Eliminato' 
    WHERE id_medico = medico_id AND data_appuntamento > NOW();
    
    COMMIT;
END//

DELIMITER ;



-- eliminate procedure per MedicoSuggerito













-- ESEMPI DI USO DELLE STORED PROCEDURE

-- Esempio 1: Cliente con intolleranze multiple
-- CALL insert_cliente_completo(
--     'Mario', 'Rossi', 'Via Roma 123', 'Milano', 'mario.rossi@email.com', 
--     'password123', 35, 'M', 75.5, 180.0,
--     'Lattosio, Glutine, Frutta secca',
--     'Diabete tipo 2, Ipertensione',
--     'Cardiopatia, Diabete'
-- );

-- Esempio 2: Cliente senza condizioni particolari
-- CALL insert_cliente_completo(
--     'Anna', 'Verdi', 'Via Garibaldi 45', 'Roma', 'anna.verdi@email.com',
--     'password456', 28, 'F', 60.0, 165.0,
--     NULL, NULL, NULL
-- );

-- Esempio 3: Inserimento medico con specializzazione
-- INSERT INTO Medico (nome, cognome, email, telefono, url_sito) 
-- VALUES ('Dott. Giovanni', 'Bianchi', 'g.bianchi@clinica.it', '+393401234567', 'https://www.clinicabianchi.it');
-- INSERT INTO Specializzazione (id_medico, specializzazione) VALUES (1, 'Gastroenterologia');

-- Esempio 4: Prenotazione appuntamento
-- CALL prenota_appuntamento(1, 1, '2024-12-15 10:00:00');

-- Esempio 5: Completamento appuntamento con diagnosi
-- CALL completa_appuntamento(1, 'Gastrite cronica, prescritto trattamento farmacologico');

-- Esempio 6: Aggiungere ranking a un appuntamento
-- CALL aggiungi_ranking_appuntamento(1, 8.5, 'Ottima professionalità, diagnosi accurata');

-- Esempio 7: Ottenere paziente casuale senza ranking per un medico
-- CALL get_paziente_random_senza_ranking(1);

-- QUERY UTILI PER ANALISI

-- Query per verificare i dati inseriti
-- SELECT * FROM view_dati_cliente_attivo WHERE id_cliente = 1;

-- Query per visualizzare tutti gli appuntamenti con stato ranking
-- SELECT * FROM view_appuntamento_attivo;

-- Query per visualizzare appuntamenti effettuati con diagnosi
-- SELECT 
--     nome_cliente, 
--     cognome_cliente, 
--     nome_medico, 
--     cognome_medico, 
--     data_appuntamento, 
--     patologia_individuata,
--     ha_ranking
-- FROM view_appuntamento_attivo 
-- WHERE stato_appuntamento = 'Effettuato';

-- Query per vedere il ranking dettagliato dei medici
-- SELECT * FROM view_ranking_medico;

-- Query per vedere tutti i ranking con commenti
-- SELECT 
--     m.nome AS nome_medico,
--     m.cognome AS cognome_medico,
--     ra.voto,
--     ra.commento,
--     ra.data_ranking,
--     a.data_appuntamento,
--     a.patologia_individuata
-- FROM RankingAppuntamento ra
-- JOIN Medico m ON ra.id_medico = m.id
-- JOIN Appuntamento a ON ra.id_appuntamento = a.id
-- WHERE ra.stato = 'Attivo'
-- ORDER BY ra.data_ranking DESC;

-- Query per trovare appuntamenti senza ranking per un medico specifico
-- SELECT 
--     a.id AS id_appuntamento,
--     a.data_appuntamento,
--     a.patologia_individuata,
--     CONCAT(c.nome, ' ', c.cognome) AS paziente
-- FROM Appuntamento a
-- JOIN Cliente c ON a.id_cliente = c.id
-- WHERE a.id_medico = 1 
--     AND a.stato = 'Effettuato'
--     AND NOT EXISTS (
--         SELECT 1 FROM RankingAppuntamento ra 
--         WHERE ra.id_appuntamento = a.id AND ra.stato = 'Attivo'
--     );


-- ESEMPI DI UTILIZZO DELLE STORED PROCEDURE

/*
-- Esempio 1: Inserire un nuovo appuntamento
CALL insert_appuntamento(1, '2024-12-20 14:30:00', 1);

-- Esempio 2: Tentare di inserire un duplicato (dovrebbe dare errore)
CALL insert_appuntamento(1, '2024-12-20 14:30:00', 1);

-- Esempio 3: Eliminare logicamente un appuntamento
CALL elimina_appuntamento_logico(1);

-- Esempio 4: Tentare di inserire lo stesso appuntamento dopo l'eliminazione (dovrebbe riattivarlo)
CALL insert_appuntamento(1, '2024-12-20 14:30:00', 1);

-- Esempio 5: Riattivare manualmente un appuntamento eliminato
CALL riattiva_appuntamento(1);

-- Esempio 6: Eliminare tutti gli appuntamenti di un medico
CALL elimina_appuntamenti_medico(1);

-- Esempio 7: Eliminare tutti gli appuntamenti di un cliente
CALL elimina_appuntamenti_cliente(1);
*/


-- QUERY UTILI PER MONITORARE LA TABELLA AGENDA

/*
-- Visualizzare tutti gli appuntamenti attivi
SELECT 
    a.id,
    CONCAT(m.nome, ' ', m.cognome) AS medico,
    a.appuntamento,
    CONCAT(c.nome, ' ', c.cognome) AS cliente,
    a.stato
FROM Agenda a
JOIN Medico m ON a.id_medico = m.id
JOIN Cliente c ON a.id_cliente = c.id
WHERE a.stato = 'Attivo'
ORDER BY a.appuntamento;

-- Visualizzare tutti gli appuntamenti (anche eliminati)
SELECT 
    a.id,
    CONCAT(m.nome, ' ', m.cognome) AS medico,
    a.appuntamento,
    CONCAT(c.nome, ' ', c.cognome) AS cliente,
    a.stato
FROM Agenda a
JOIN Medico m ON a.id_medico = m.id
JOIN Cliente c ON a.id_cliente = c.id
ORDER BY a.appuntamento, a.stato;

-- Contare appuntamenti per stato
SELECT 
    stato,
    COUNT(*) as numero_appuntamenti
FROM Agenda
GROUP BY stato;

-- Visualizzare appuntamenti futuri di un medico specifico
SELECT 
    a.id,
    a.appuntamento,
    CONCAT(c.nome, ' ', c.cognome) AS cliente,
    a.stato
FROM Agenda a
JOIN Cliente c ON a.id_cliente = c.id
WHERE a.id_medico = 1 
    AND a.appuntamento > NOW()
    AND a.stato = 'Attivo'
ORDER BY a.appuntamento;
*/