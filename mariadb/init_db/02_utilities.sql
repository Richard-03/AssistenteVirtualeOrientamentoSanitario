USE user_db;


-- CREAZIONE VIEW CORRETTE
DROP VIEW IF EXISTS view_appuntamento_attivo;
CREATE VIEW view_appuntamento_attivo AS
SELECT
    a.id AS id_appuntamento,
    c.id AS id_cliente,
    c.nome AS nome_cliente,
    c.cognome AS cognome_cliente,
    m.id AS id_medico,
    m.nome AS nome_medico,
    m.cognome AS cognome_medico,
    a.data_registrazione AS data_registrazione,
    a.data_appuntamento AS data_appuntamento,
    a.stato AS stato_appuntamento,
    a.patologia_individuata AS patologia_individuata,
    CASE WHEN ra.id IS NOT NULL THEN 'Si' ELSE 'No' END AS ha_ranking
FROM Cliente c 
JOIN Appuntamento a ON (c.id = a.id_cliente)
JOIN Medico m ON (m.id = a.id_medico)
LEFT JOIN RankingAppuntamento ra ON (a.id = ra.id_appuntamento AND ra.stato = 'Attivo')
WHERE a.stato IN ('Prenotato', 'Effettuato') 
    AND c.stato = 'Attivo' 
    AND m.stato = 'Attivo';

-- View per visualizzare i ranking dei medici con dettagli appuntamenti
DROP VIEW IF EXISTS view_ranking_medico;
CREATE VIEW view_ranking_medico AS
SELECT
    m.id AS id_medico,
    m.nome AS nome_medico,
    m.cognome AS cognome_medico,
    s.specializzazione AS specializzazione,
    s.ranking AS ranking_medio,
    COUNT(ra.id) AS numero_valutazioni,
    AVG(ra.voto) AS voto_medio_effettivo,
    MIN(ra.voto) AS voto_minimo,
    MAX(ra.voto) AS voto_massimo
FROM Medico m
    JOIN Specializzazione s ON (m.id = s.id_medico)
    LEFT JOIN RankingAppuntamento ra ON (m.id = ra.id_medico AND ra.stato = 'Attivo')
WHERE m.stato = 'Attivo' AND s.stato = 'Attivo'
GROUP BY m.id, s.id;

DROP VIEW IF EXISTS view_dati_cliente_attivo;
CREATE VIEW view_dati_cliente_attivo AS
SELECT 
    c.id AS id_cliente,
    c.nome AS nome_cliente,
    c.cognome AS cognome_cliente,
    c.email AS email_cliente,
    c.eta AS eta,
    c.sesso AS sesso,
    c.peso AS peso,
    c.altezza AS altezza,
    i.intolleranza AS intolleranza,
    cpf.condizione_fam AS condizione_patologica_familiare,
    cpp.condizione_preg AS condizione_patologica_pregressa
FROM Cliente c 
LEFT JOIN IntolleranzaAlimentare i ON (c.id = i.id_cliente AND i.stato = 'Attivo')
LEFT JOIN CondizioniPatologicheFamiliari cpf ON (c.id = cpf.id_cliente AND cpf.stato = 'Attivo')
LEFT JOIN CondizioniPatologichePregresse cpp ON (c.id = cpp.id_cliente AND cpp.stato = 'Attivo')
WHERE c.stato = 'Attivo';

-- eliminata view MedicoSuggeritoAttivo