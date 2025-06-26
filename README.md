# Prossimamente:
- introduzione di un sistema di ranking
  - basato su recensioni (ritardate rispetto a un appuntamento)
- visualizzazione di una mappa in cui saranno disposti il cliente e i primi K medici per posizione, mostrando anche il loro rank
- visualizzazione di una barra laterale di prenotazione che fa da alternativa sicura alla comunicazione con il linguaggio per la prenotazione di una visita
    (l'utente potrà scegliere da una lista di consigliati secondo quella che è la categoria di medici individuata dal modello)
- gesione degli appuntamenti: il sisteam non deve permettere scelta libera al cliente, ma solo tra le date passatogli, fornite direttamente da un medico, quindi il modello deve proporre solo quelle fasce orarie
- migliorare la robustezza dei prompt e delle risposte
- gestire tutti gli errori:
  - i redirect di un errore non dovranno mai portare su una pagina bianca con {message: errore di qualche tipo}
