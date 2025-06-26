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
    IN p_appuntamento TIMESTAMP
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
        AND stato = 'Eliminato'
    LIMIT 1;
    
    IF existing_id > 0 THEN
        -- Se esiste un record eliminato, riattivalo come 'Attivo' (slot libero)
        UPDATE Agenda 
        SET stato = 'Attivo', id_cliente = NULL
        WHERE id = existing_id;
        
        COMMIT;
        
        SELECT 
            existing_id AS id_appuntamento,
            'Slot riattivato come disponibile' AS messaggio,
            p_id_medico AS id_medico,
            p_appuntamento AS appuntamento,
            'Attivo' AS stato;
    ELSE
        -- Verifica che non esista già un appuntamento attivo/prenotato con gli stessi dati
        IF EXISTS (
            SELECT 1 FROM Agenda 
            WHERE id_medico = p_id_medico 
                AND appuntamento = p_appuntamento 
                AND stato IN ('Attivo', 'Prenotato')
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Slot già esistente per questi parametri';
        END IF;
        
        -- Verifica che il medico esista e sia attivo
        IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = p_id_medico AND stato = 'Attivo') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non trovato o non attivo';
        END IF;
        
        -- Verifica che la data dell'appuntamento sia futura
        IF p_appuntamento <= NOW() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "La data dell'appuntamento deve essere futura";
        END IF;
        
        -- Inserisci il nuovo slot come 'Attivo' (disponibile)
        INSERT INTO Agenda (
            id_medico,
            appuntamento,
            id_cliente,
            stato
        ) VALUES (
            p_id_medico,
            p_appuntamento,
            NULL,
            'Attivo'
        );
        
        COMMIT;
        
        SELECT 
            LAST_INSERT_ID() AS id_appuntamento,
            'Nuovo slot disponibile creato' AS messaggio,
            p_id_medico AS id_medico,
            p_appuntamento AS appuntamento,
            'Attivo' AS stato;
    END IF;
    
END//

DELIMITER ;

-- Procedure per eliminare logicamente un appuntamento dall'agenda e dalla tabella Appuntamento
DELIMITER //
DROP PROCEDURE IF EXISTS elimina_appuntamento_logico//
CREATE PROCEDURE elimina_appuntamento_logico(
    IN p_id_appuntamento INT
)
BEGIN
    DECLARE appuntamento_count INT DEFAULT 0;
    DECLARE agenda_count INT DEFAULT 0;
    DECLARE v_id_cliente INT;
    DECLARE v_id_medico INT;
    DECLARE v_data_appuntamento TIMESTAMP;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Verifica che l'appuntamento esista nella tabella Appuntamento e sia attivo
    SELECT COUNT(*), id_cliente, id_medico, data_appuntamento 
    INTO appuntamento_count, v_id_cliente, v_id_medico, v_data_appuntamento
    FROM Appuntamento
    WHERE id = p_id_appuntamento AND stato IN ('Prenotato', 'Effettuato');

    IF appuntamento_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o già eliminato';
    END IF;

    -- Elimina logicamente l'appuntamento dalla tabella Appuntamento
    UPDATE Appuntamento
    SET stato = 'Eliminato'
    WHERE id = p_id_appuntamento;

    -- Verifica se esiste un record corrispondente nell'Agenda e lo elimina logicamente
    SELECT COUNT(*) INTO agenda_count
    FROM Agenda
    WHERE id_cliente = v_id_cliente 
      AND id_medico = v_id_medico 
      AND appuntamento = v_data_appuntamento 
      AND stato IN ('Attivo', 'Prenotato');

    IF agenda_count > 0 THEN
        UPDATE Agenda
        SET stato = 'Eliminato'
        WHERE id_cliente = v_id_cliente 
          AND id_medico = v_id_medico 
          AND appuntamento = v_data_appuntamento 
          AND stato IN ('Attivo', 'Prenotato');
    END IF;

    COMMIT;

    SELECT
        p_id_appuntamento AS id_appuntamento_eliminato,
        'Appuntamento eliminato logicamente da entrambe le tabelle' AS messaggio;

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

DROP PROCEDURE IF EXISTS completa_appuntamento//

CREATE PROCEDURE completa_appuntamento(
    IN p_id_appuntamento INT,
    IN p_diagnosi VARCHAR(255)
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
        patologia_individuata = p_diagnosi
    WHERE id = p_id_appuntamento 
        AND stato = 'Prenotato';
    
    -- Verifica se l'update è stato effettuato
    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o non in stato Prenotato';
    END IF;
    
    -- Lo slot in Agenda rimane 'Prenotato' per mantenere la traccia storica
    -- Non modifichiamo la tabella Agenda per appuntamenti completati
    
    COMMIT;
    
    SELECT 
        p_id_appuntamento AS id_appuntamento_completato,
        'Appuntamento completato con successo' AS messaggio,
        p_diagnosi AS diagnosi_inserita;
END//

DELIMITER ;

-- Procedure per aggiungere un ranking a un appuntamento
DELIMITER //

DROP PROCEDURE IF EXISTS aggiungi_ranking_appuntamento//

CREATE PROCEDURE aggiungi_ranking_appuntamento(
    IN p_id_appuntamento INT,
    IN p_voto DECIMAL(3,2),
    IN p_commento_ranking TEXT
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
    WHERE id = p_id_appuntamento AND stato = 'Effettuato';
    
    IF medico_id_var IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o non ancora effettuato';
    END IF;
    
    -- Verifica che non ci sia già un ranking per questo appuntamento
    IF EXISTS (SELECT 1 FROM RankingAppuntamento WHERE id_appuntamento = p_id_appuntamento AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ranking già presente per questo appuntamento';
    END IF;
    
    -- Inserisci il ranking
    INSERT INTO RankingAppuntamento (id_appuntamento, id_medico, voto, commento)
    VALUES (p_id_appuntamento, medico_id_var, p_voto, p_commento_ranking);
    
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

DELIMITER ;

DELIMITER //
-- Procedure per ottenere dati anonimizzati di un paziente casuale senza ranking
CREATE PROCEDURE get_paziente_random_senza_ranking(
    IN p_id_medico INT
)
BEGIN
    DECLARE appuntamento_random INT DEFAULT 0;
    DECLARE paziente_id INT DEFAULT 0;
    
    -- Seleziona un appuntamento casuale effettuato dal medico senza ranking
    SELECT a.id, a.id_cliente INTO appuntamento_random, paziente_id
    FROM Appuntamento a
    WHERE a.id_medico = p_id_medico 
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


DELIMITER ;

-- PROCEDURE AGGIUNTIVE PER GESTIRE LO STATO

-- Procedure per "eliminare" logicamente un cliente
DELIMITER //
CREATE PROCEDURE elimina_cliente_logico(
    IN p_id_cliente INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Elimina logicamente il cliente
    UPDATE Cliente SET stato = 'Eliminato' WHERE id = p_id_cliente;
    
    -- Elimina logicamente tutte le sue intolleranze
    UPDATE IntolleranzaAlimentare SET stato = 'Eliminato' WHERE id_cliente = p_id_cliente;
    
    -- Elimina logicamente tutte le sue condizioni pregresse
    UPDATE CondizioniPatologichePregresse SET stato = 'Eliminato' WHERE id_cliente = p_id_cliente;
    
    -- Elimina logicamente tutte le sue condizioni familiari
    UPDATE CondizioniPatologicheFamiliari SET stato = 'Eliminato' WHERE id_cliente = p_id_cliente;
    
    -- Elimina logicamente tutti i suoi appuntamenti
    UPDATE Appuntamento SET stato = 'Eliminato' WHERE id_cliente = p_id_cliente;
    
    COMMIT;
END//

-- Procedure per riattivare un cliente
CREATE PROCEDURE riattiva_cliente(
    IN p_id_cliente INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Riattiva il cliente
    UPDATE Cliente SET stato = 'Attivo' WHERE id = p_id_cliente;
    
    -- Riattiva tutte le sue intolleranze
    UPDATE IntolleranzaAlimentare SET stato = 'Attivo' WHERE id_cliente = p_id_cliente;
    
    -- Riattiva tutte le sue condizioni pregresse
    UPDATE CondizioniPatologichePregresse SET stato = 'Attivo' WHERE id_cliente = p_id_cliente;
    
    -- Riattiva tutte le sue condizioni familiari
    UPDATE CondizioniPatologicheFamiliari SET stato = 'Attivo' WHERE id_cliente = p_id_cliente;
    
    COMMIT;
END//

-- Procedure per eliminare logicamente un medico
CREATE PROCEDURE elimina_medico_logico(
    IN p_id_medico INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Elimina logicamente il medico
    UPDATE Medico SET stato = 'Eliminato' WHERE id = p_id_medico;
    
    -- Elimina logicamente tutte le sue specializzazioni
    UPDATE Specializzazione SET stato = 'Eliminato' WHERE id_medico = p_id_medico;
    
    -- Elimina logicamente la sua agenda
    UPDATE Agenda SET stato = 'Eliminato' WHERE id_medico = p_id_medico;
    
    -- Elimina logicamente tutti i suoi appuntamenti futuri
    UPDATE Appuntamento SET stato = 'Eliminato' 
    WHERE id_medico = p_id_medico AND data_appuntamento > NOW();
    
    COMMIT;
END//

DELIMITER ;



-- Procedure modificata per prenotare un nuovo appuntamento verificando disponibilità in Agenda
DELIMITER //

DROP PROCEDURE IF EXISTS prenota_appuntamento//

CREATE PROCEDURE prenota_appuntamento(
    IN p_id_cliente INT,
    IN p_id_medico INT,
    IN p_data_app TIMESTAMP
)
BEGIN
    DECLARE slot_agenda_id INT DEFAULT 0;
    DECLARE slot_stato VARCHAR(20) DEFAULT '';
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Verifica che cliente e medico siano attivi
    IF NOT EXISTS (SELECT 1 FROM Cliente WHERE id = p_id_cliente AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente non trovato o non attivo';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = p_id_medico AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non trovato o non attivo';
    END IF;
    
    -- Verifica che il medico sia verificato
    IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = p_id_medico AND stato = 'Attivo' AND verificato = 1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non verificato';
    END IF;
    
    -- Verifica che la data sia futura
    IF p_data_app <= NOW() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "La data dell'appuntamento deve essere futura";
    END IF;
    
    -- Verifica disponibilità nella tabella Agenda e ottieni l'ID del slot
    SELECT id, stato INTO slot_agenda_id, slot_stato
    FROM Agenda 
    WHERE id_medico = p_id_medico 
        AND appuntamento = p_data_app 
    LIMIT 1;
    
    -- Se non esiste nessun slot per quella data/ora
    IF slot_agenda_id = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Slot non disponibile: il medico non ha orari disponibili in questa data e ora';
    END IF;
    
    -- Se lo slot esiste ma non è 'Attivo' (disponibile)
    IF slot_stato != 'Attivo' THEN
        IF slot_stato = 'Prenotato' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Slot non disponibile: già prenotato da un altro cliente';
        ELSE
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Slot non disponibile: stato non valido';
        END IF;
    END IF;
    
    -- Verifica che il cliente non abbia già un appuntamento nello stesso momento
    IF EXISTS (
        SELECT 1 FROM Agenda a
        WHERE a.id_cliente = p_id_cliente 
            AND a.appuntamento = p_data_app 
            AND a.stato = 'Prenotato'
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Il cliente ha già un appuntamento prenotato in questa data e ora';
    END IF;
    
    -- Verifica che il cliente non abbia già un appuntamento prenotato con lo stesso medico
    IF EXISTS (
        SELECT 1 FROM Appuntamento a
        WHERE a.id_cliente = p_id_cliente 
            AND a.id_medico = p_id_medico 
            AND a.stato = 'Prenotato'
            AND a.data_appuntamento > NOW()
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Il cliente ha già un appuntamento prenotato con questo medico';
    END IF;
    
    -- Inserisci l'appuntamento nella tabella Appuntamento
    INSERT INTO Appuntamento (id_cliente, id_medico, data_appuntamento, stato)
    VALUES (p_id_cliente, p_id_medico, p_data_app, 'Prenotato');
    
    -- Aggiorna lo slot in Agenda da 'Attivo' a 'Prenotato'
    UPDATE Agenda 
    SET stato = 'Prenotato', id_cliente = p_id_cliente
    WHERE id = slot_agenda_id;
    
    COMMIT;
    
    SELECT 
        LAST_INSERT_ID() AS nuovo_appuntamento_id,
        slot_agenda_id AS id_slot_agenda,
        'Appuntamento prenotato con successo' AS messaggio,
        p_data_app AS data_appuntamento,
        p_id_medico AS id_medico,
        p_id_cliente AS id_cliente;
END//

DELIMITER ;

-- Procedure aggiuntiva per ottenere gli slot disponibili di un medico in un determinato giorno
DELIMITER //

DROP PROCEDURE IF EXISTS get_slot_disponibili_medico//

CREATE PROCEDURE get_slot_disponibili_medico(
    IN p_id_medico INT,
    IN p_data_giorno DATE,
    IN p_ora_inizio TIME,
    IN p_ora_fine TIME,
    IN p_durata_slot INT
)
BEGIN
    -- Imposta i valori di default se i parametri sono NULL
    SET p_ora_inizio = COALESCE(p_ora_inizio, '09:00:00');
    SET p_ora_fine = COALESCE(p_ora_fine, '18:00:00');
    SET p_durata_slot = COALESCE(p_durata_slot, 30);
    
    -- Verifica che il medico esista e sia attivo e verificato
    IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = p_id_medico AND stato = 'Attivo' AND verificato = 1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non trovato, non attivo o non verificato';
    END IF;
    
    -- Verifica che la data non sia nel passato
    IF p_data_giorno < CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Non è possibile verificare disponibilità per date passate';
    END IF;
    
    -- Restituisci tutti gli slot disponibili (stato 'Attivo') per il medico nel giorno specificato
    SELECT 
        a.id AS id_slot,
        DATE(a.appuntamento) AS data_appuntamento,
        TIME(a.appuntamento) AS ora_appuntamento,
        a.appuntamento AS datetime_completo,
        a.stato AS stato_slot,
        'Disponibile per prenotazione' AS descrizione
    FROM Agenda a
    WHERE a.id_medico = p_id_medico 
        AND DATE(a.appuntamento) = p_data_giorno
        AND a.stato = 'Attivo'
        AND a.appuntamento > NOW()
        AND TIME(a.appuntamento) BETWEEN p_ora_inizio AND p_ora_fine
    ORDER BY a.appuntamento;
END//

DELIMITER ;


-- Procedure per ottenere tutti gli appuntamenti occupati di un medico in un giorno
DELIMITER //

DROP PROCEDURE IF EXISTS get_appuntamenti_medico_giorno//

CREATE PROCEDURE get_appuntamenti_medico_giorno(
    IN p_id_medico INT,
    IN p_data_giorno DATE
)
BEGIN
    -- Verifica che il medico esista
    IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = p_id_medico AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non trovato o non attivo';
    END IF;
    
    SELECT 
        a.id AS id_agenda,
        a.appuntamento AS datetime_appuntamento,
        DATE(a.appuntamento) AS data_appuntamento,
        TIME(a.appuntamento) AS ora_appuntamento,
        CONCAT(c.nome, ' ', c.cognome) AS nome_cliente,
        c.email AS email_cliente,
        a.stato AS stato_slot
    FROM Agenda a
    JOIN Cliente c ON a.id_cliente = c.id
    WHERE a.id_medico = p_id_medico 
        AND DATE(a.appuntamento) = p_data_giorno
        AND a.stato = 'Attivo'
    ORDER BY a.appuntamento;
END//

DELIMITER ;

-- Procedure per cancellare un appuntamento (elimina sia da Appuntamento che da Agenda)
DELIMITER //

DROP PROCEDURE IF EXISTS cancella_appuntamento_completo//

CREATE PROCEDURE cancella_appuntamento_completo(
    IN p_id_appuntamento INT
)
BEGIN
    DECLARE medico_id_var INT;
    DECLARE cliente_id_var INT;
    DECLARE data_app_var TIMESTAMP;
    DECLARE slot_agenda_id INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Ottieni i dati dell'appuntamento
    SELECT id_medico, id_cliente, data_appuntamento 
    INTO medico_id_var, cliente_id_var, data_app_var
    FROM Appuntamento 
    WHERE id = p_id_appuntamento AND stato = 'Prenotato';
    
    IF medico_id_var IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appuntamento non trovato o non in stato Prenotato';
    END IF;
    
    -- Ottieni l'ID del slot corrispondente in Agenda
    SELECT id INTO slot_agenda_id
    FROM Agenda 
    WHERE id_medico = medico_id_var 
        AND id_cliente = cliente_id_var 
        AND appuntamento = data_app_var 
        AND stato = 'Prenotato'
    LIMIT 1;
    
    -- Elimina logicamente l'appuntamento
    UPDATE Appuntamento 
    SET stato = 'Eliminato'
    WHERE id = p_id_appuntamento;
    
    -- Riporta lo slot da 'Prenotato' a 'Attivo' (disponibile)
    IF slot_agenda_id > 0 THEN
        UPDATE Agenda 
        SET stato = 'Attivo', id_cliente = NULL
        WHERE id = slot_agenda_id;
    END IF;
    
    COMMIT;
    
    SELECT 
        p_id_appuntamento AS id_appuntamento_cancellato,
        slot_agenda_id AS id_slot_liberato,
        'Appuntamento cancellato e slot liberato' AS messaggio,
        medico_id_var AS id_medico,
        cliente_id_var AS id_cliente,
        data_app_var AS data_appuntamento;
END//

DELIMITER ;
/*
ESEMPI DI UTILIZZO:

-- 1. Prenotare un appuntamento
CALL prenota_appuntamento(1, 1, '2024-12-20 14:30:00');

-- 2. Verificare slot disponibili per un medico in un giorno
CALL get_slot_disponibili_medico(1, '2024-12-20', '09:00:00', '18:00:00', 30);

-- 3. Vedere tutti gli appuntamenti di un medico in un giorno
CALL get_appuntamenti_medico_giorno(1, '2024-12-20');

-- 4. Cancellare un appuntamento
CALL cancella_appuntamento_completo(1);

-- 5. Tentare di prenotare uno slot già occupato (dovrebbe dare errore)
CALL prenota_appuntamento(2, 1, '2024-12-20 14:30:00');
*/

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

DELIMITER //

CREATE PROCEDURE get_giorni_disponibili_medico(
    IN p_id_medico INT
)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM Medico WHERE id = p_id_medico AND stato = 'Attivo' AND verificato = 1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Medico non trovato o non verificato';
    END IF;

    SELECT
      DATE(appuntamento) AS giorno,
      TIME(appuntamento) AS orario
    FROM Agenda
    WHERE id_medico = p_id_medico
      AND stato = 'Attivo'
      AND appuntamento > NOW()
      AND id_cliente IS NULL
    ORDER BY giorno, orario;
END //


DELIMITER ;

-- Procedure per eliminare logicamente una chat
DELIMITER //
DROP PROCEDURE IF EXISTS elimina_chat_logico//
CREATE PROCEDURE elimina_chat_logico(
    IN p_id_chat INT
)
BEGIN
    DECLARE chat_count INT DEFAULT 0;
    DECLARE v_id_cliente INT;
    DECLARE v_numero_chat INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Verifica che la chat esista e sia attiva
    SELECT COUNT(*), id_cliente, numero_chat 
    INTO chat_count, v_id_cliente, v_numero_chat
    FROM Chat
    WHERE id = p_id_chat AND stato = 'Attivo';

    IF chat_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Chat non trovata o già eliminata';
    END IF;

    -- Elimina logicamente la chat
    UPDATE Chat
    SET stato = 'Eliminato'
    WHERE id = p_id_chat;

    COMMIT;

    SELECT
        p_id_chat AS id_chat_eliminata,
        v_id_cliente AS id_cliente,
        v_numero_chat AS numero_chat,
        'Chat eliminata logicamente' AS messaggio;

END//
DELIMITER ;

-- Procedure per eliminare logicamente tutte le chat di un cliente
DELIMITER //
DROP PROCEDURE IF EXISTS elimina_tutte_chat_cliente//
CREATE PROCEDURE elimina_tutte_chat_cliente(
    IN p_id_cliente INT
)
BEGIN
    DECLARE chat_count INT DEFAULT 0;
    DECLARE cliente_exists INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Verifica che il cliente esista
    SELECT COUNT(*) INTO cliente_exists
    FROM Cliente
    WHERE id = p_id_cliente AND stato = 'Attivo';

    IF cliente_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente non trovato o non attivo';
    END IF;

    -- Conta le chat attive del cliente
    SELECT COUNT(*) INTO chat_count
    FROM Chat
    WHERE id_cliente = p_id_cliente AND stato = 'Attivo';

    IF chat_count = 0 THEN
        SELECT
            p_id_cliente AS id_cliente,
            0 AS chat_eliminate,
            'Nessuna chat attiva trovata per questo cliente' AS messaggio;
    ELSE
        -- Elimina logicamente tutte le chat del cliente
        UPDATE Chat
        SET stato = 'Eliminato'
        WHERE id_cliente = p_id_cliente AND stato = 'Attivo';

        SELECT
            p_id_cliente AS id_cliente,
            chat_count AS chat_eliminate,
            CONCAT('Eliminate logicamente ', chat_count, ' chat del cliente') AS messaggio;
    END IF;

    COMMIT;

END//
DELIMITER ;

-- Procedure per eliminare logicamente una conversazione completa (stesso numero_chat)
DELIMITER //
DROP PROCEDURE IF EXISTS elimina_conversazione_logico//
CREATE PROCEDURE elimina_conversazione_logico(
    IN p_id_cliente INT,
    IN p_numero_chat INT
)
BEGIN
    DECLARE chat_count INT DEFAULT 0;
    DECLARE cliente_exists INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Verifica che il cliente esista
    SELECT COUNT(*) INTO cliente_exists
    FROM Cliente
    WHERE id = p_id_cliente AND stato = 'Attivo';

    IF cliente_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente non trovato o non attivo';
    END IF;

    -- Conta le chat attive per quella conversazione
    SELECT COUNT(*) INTO chat_count
    FROM Chat
    WHERE id_cliente = p_id_cliente 
      AND numero_chat = p_numero_chat 
      AND stato = 'Attivo';

    IF chat_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Conversazione non trovata o già eliminata';
    END IF;

    -- Elimina logicamente tutte le chat della conversazione
    UPDATE Chat
    SET stato = 'Eliminato'
    WHERE id_cliente = p_id_cliente 
      AND numero_chat = p_numero_chat 
      AND stato = 'Attivo';

    COMMIT;

    SELECT
        p_id_cliente AS id_cliente,
        p_numero_chat AS numero_chat,
        chat_count AS messaggi_eliminati,
        CONCAT('Conversazione eliminata logicamente (', chat_count, ' messaggi)') AS messaggio;

END//
DELIMITER ;

-- Procedure per ottenere tutti gli appuntamenti di un cliente
DELIMITER //

DROP PROCEDURE IF EXISTS get_appuntamenti_cliente//
DELIMITER //

CREATE PROCEDURE get_appuntamenti_cliente(
    IN p_id_cliente INT
)
BEGIN
    -- Verifica che il cliente esista e sia attivo
    IF NOT EXISTS (SELECT 1 FROM Cliente WHERE id = p_id_cliente AND stato = 'Attivo') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cliente non trovato o non attivo';
    END IF;
    
    -- Restituisce tutti gli appuntamenti del cliente con le informazioni del medico
    SELECT 
        a.id AS id_appuntamento,
        a.data_appuntamento,
        DATE(a.data_appuntamento) AS data_appuntamento_date,
        TIME(a.data_appuntamento) AS ora_appuntamento,
        a.stato AS stato_appuntamento,
        a.patologia_individuata,
        a.data_registrazione AS data_prenotazione,
        
        -- Informazioni del medico
        m.id AS id_medico,
        CONCAT(m.nome, ' ', m.cognome) AS nome_completo_medico,
        m.nome AS nome_medico,
        m.cognome AS cognome_medico,
        m.email AS email_medico,
        m.telefono AS telefono_medico,
        m.url_sito AS sito_medico,
        m.indirizzo AS indirizzo_medico,
        m.citta AS citta_medico,
        
        -- Specializzazioni del medico (concatenate)
        GROUP_CONCAT(DISTINCT s.specializzazione SEPARATOR ', ') AS specializzazioni_medico,
        
        -- Ranking medio del medico
        COALESCE(AVG(s.ranking), 0.00) AS ranking_medio_medico,
        
        -- Informazioni se l'appuntamento ha già un ranking
        CASE 
            WHEN ra.id IS NOT NULL THEN 'Si'
            ELSE 'No'
        END AS ha_ranking,
        ra.voto AS voto_dato,
        ra.commento AS commento_ranking,
        ra.data_ranking,
        
        -- Informazioni temporali utili
        CASE 
            WHEN a.data_appuntamento > NOW() THEN 'Futuro'
            WHEN a.data_appuntamento <= NOW() AND a.stato = 'Prenotato' THEN 'Passato (non effettuato)'
            WHEN a.stato = 'Effettuato' THEN 'Completato'
            WHEN a.stato = 'Eliminato' THEN 'Cancellato'
            ELSE 'Altro'
        END AS status_temporale,
        
        DATEDIFF(a.data_appuntamento, CURDATE()) AS giorni_da_oggi,
        
        -- Indicatore se è possibile cancellare (solo appuntamenti futuri prenotati)
        CASE 
            WHEN a.data_appuntamento > NOW() AND a.stato = 'Prenotato' THEN 'Si'
            ELSE 'No'
        END AS cancellabile
        
    FROM Appuntamento a
    JOIN Medico m ON a.id_medico = m.id
    LEFT JOIN Specializzazione s ON (m.id = s.id_medico AND s.stato = 'Attivo')
    LEFT JOIN RankingAppuntamento ra ON (a.id = ra.id_appuntamento AND ra.stato = 'Attivo')
    
    WHERE a.id_cliente = p_id_cliente 
        AND a.stato IN ('Prenotato', 'Effettuato', 'Eliminato')
        
    GROUP BY 
        a.id, a.data_appuntamento, a.stato, a.patologia_individuata, a.data_registrazione,
        m.id, m.nome, m.cognome, m.email, m.telefono, m.url_sito, m.indirizzo, m.citta,
        ra.id, ra.voto, ra.commento, ra.data_ranking
        
    ORDER BY 
        a.data_appuntamento DESC, a.data_registrazione DESC;
END//

DELIMITER ;
