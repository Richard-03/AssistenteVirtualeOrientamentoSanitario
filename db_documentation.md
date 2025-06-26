# STORED PROCEDURE
## Inserire Cliente
###  CALL insert_cliente_completo(c_nome, c_cognome, c_indirizzo, c_citta, c_email, c_password, c_eta, c_sesso, c_peso, c_altezza, intolleranze, condizioni_pregresse, condizioni_familiari, farmaci);
Inserisce un Cliente gestendo le sue tabelle ausiliari. I campi multipli vanno messi tra doppi apici separati tra virgole.
Ciò vale per intolleranze, condizioni_pregresse, condizioni_familiari ed farmaci.
Tali campi sono anche facoltativi.

## Inserire Medico
### CALL insert_medico_completo(m_nome, m_cognome, m_codice_fiscale, m_numero_albo, m_citta_ordine, m_data_iscrizione_albo, m_citta, m_email, m_password, m_telefono, m_url_sito, m_indirizzo, m_specializzazioni, m_coordinate);
Inserisce un Medico gestendo la sua tabella di Specializzazione. I campi multipli vanno messi tra doppi apici separati tra virgole.
Ciò vale per m_specializzazioni e m_coordinate.

## Creare nuova Chat
### CALL insert_chat(p_id_cliente, p_domanda, p_risposta, p_reparto_consigliato, p_id_medico)
Autoesplicativo. Verifica che il Cliente associato sia Attivo.

## Scrivere su vecchia Chat
### CALL insert_chat(p_id_cliente, p_numero_chat, p_domanda, p_risposta, p_reparto_consigliato, p_id_medico);
Autoesplicativo.






## Inserire appuntamento in Agenda (lato Medico)
### CALL insert_appuntamento(p_id_medico, p_appuntamento, p_id_cliente);
Autoesplicativo. Se 

CAPIRE COME GESTIRE CLIENTE A PRIORI






## Eliminare logicamente appuntamento in Agenda (lato Medico)
### CALL elimina_appuntamento_logico(p_id_appuntamento);
Autoesplicativo.

## Riattiva appuntamento in Agenda (lato Medico)
### CALL riattiva_appuntamento(p_id_appuntamento);
Autoesplicativo.

## Eliminare logicamente appuntamenti in Agenda associati ad un Medico
### CALL elimina_appuntamenti_medico(p_id_medico);
Autoesplicativo.

## Eliminare logicamente appuntamenti in Agenda associati ad un Cliente
### CALL elimina_appuntamenti_cliente(p_id_cliente);
Autoesplicativo.

## Completare un Appuntamento con diagnosi
### CALL completa_appuntamento(p_id_appuntamento, p_diagnosi);
Autoesplicativo.
SI POTREBBE AGGIUNGERE GESTIONI FARMACI (DA MODIFICARE ANCHE STRUTTURA DB).

## Aggiungere una recenzione ad un Appuntamento
### CALL aggiungi_ranking_appuntamento(p_id_appuntamento, p_voto, p_commento_ranking);
Autoesplicativo.

## Ottenere dati anonimizzati di un Appuntamento senza ranking
### CALL get_paziente_random_senza_ranking(p_id_medico);
Autoesplicativo.

## Eliminare logicamentoe un Cliente
### CALL elimina_cliente_logico(p_id_cliente);
Autoesplicativo.

## Riattivare un Cliente
### CALL riattiva_cliente(p_id_cliente);
Autoesplicativo.

## Eliminare logicamentoe un Medico
### CALL elimina_medico_logico(p_id_medico);
Autoesplicativo.

## Prenotare un appuntamento
### CALL prenota_appuntamento(p_id_cliente, p_id_medico, p_data_app);
Prenota un appuntamento in Appuntamento sulla base delle disponibilità di Medico esplresse in Agenda.

## Ottenere slot disponibili per un medico
### CALL get_slot_disponibili_medico(p_id_medico, p_data_giorno, p_ora_inizio, p_ora_fine, p_durata_slot);
INUTILE. DA COMPRENDERE IL SENSO ALL'INTERNO DEL DB.

## Ottenere appuntamenti di un medico
### CALL get_appuntamenti_medico_giorno(p_id_medico, p_data_giorno);
Autoesplicativo.

## Eliminare un appuntamento (sia da Agenda sia da Appuntamento)
### CALL cancella_appuntamento_completo(p_id_appuntamento);
Autoesplicativo.

