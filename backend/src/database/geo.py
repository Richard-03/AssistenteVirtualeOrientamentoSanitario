from .database import get_cursor
import mariadb

from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut
import time
import os
from typing import Dict, Optional, Tuple, List, Any
import folium

MAP_FILENAME = "..", "data", "mappa_medici.html"


# TODO: SPOSTARE QUESTA FUNZIONE NELLE INTERAZIONI DI CHAT PERCHé QUI NON è PIù LOGIAMENTE CONNESSA
def fetch_drs_info(specialization: str = None) -> List[Dict[str, str]]:
    """
    Retrieve info about doctors about:
    - id
    - nome
    - cognome
    - id_specializzazione
    - specializzazione
    - indirizzo
    - latitudine
    - lognitudine
    - ranking
    Args:
        specialization (str): filter by specifying a particular field of medicine
    Returns:
        (List[Dict[str, str]]): collection of doctors data
    """
    result = None
    with get_cursor() as cursor:
        cursor: mariadb.Cursor
        # TODO: io faccio il join, da modificare: più utile se si fa una view e poi si cattura l'informazione dalla view
        if not specialization: 
            cursor.execute("SELECT m.id, m.nome, m.cognome, s.id, s.specializzazione, s.indirizzo, s.latitudine, s.longitudine, s.ranking FROM Medico m LEFT JOIN Specializzazione s ON m.id = s.id_medico")
        else:
            cursor.execute("SELECT m.id, m.nome, m.cognome, s.id, s.specializzazione, s.indirizzo, s.latitudine, s.longitudine, s.ranking FROM Medico m LEFT JOIN Specializzazione s ON m.id = s.id_medico WHERE s.specializzazione = ?", (specialization,))
        result = cursor.fetchall()
        # TODO: prendo queste informazioni, in realtà si può pensare di prendere solo id e indirizzo perche è noto che quando questa funzione viene lanciato latitudine e longitudine sono a valore nullo/0
        position_data = [{
            "id": tup[0],
            "nome": tup[1],
            "cognome": tup[2],
            "id_specializzazione": tup[3],
            "specializzazione": tup[4],
            "indirizzo": tup[5],
            "latitudine": float(tup[6]), 
            "longitudine": float(tup[7]),
            "ranking": float(tup[8])
        } for tup in result]
        return position_data
    


def get_coordinates(address: str, max_attempts: int = 5, single_timeout:int = 5) -> Tuple[float, float]:
    """
    Computes coordinates using geopy given a specific existing address.
    Args:
        cached_coords (Dict[str, Tuple[float, float]]): 
        address (str): existing address to geolocalize
        max_attempts (int, optional): max number of trials to connect to the service. Defaults to 5.
        single_timeout (int, optional): interval between a request and the following one. Defaults to 5.
    Returns:
        tuple: on success, returns coordinates of *address*; on failure is None
    """

    # oggetto che fa le ricerche, il nome è obbligatorio per dire "io sto facendo ricerche, chi sono io"
    geolocator = Nominatim(user_agent = "mio_servizio_geolocalizzazione_per_progetto_assistente")   

    for attempt in range(max_attempts):
        try:
            location = geolocator.geocode(address, timeout = single_timeout)
            if location:
                coord =  (location.latitude, location.longitude)
                return coord
        except GeocoderTimedOut:
            print("Fallimento, ritentando...")
            time.sleep(2**attempt)
        except Exception as e:
            print("Catturata eccezione non di connessione: ", e, type(e))
            raise
    print("Tutti i tentivi sono falliti")
    return None




# TODO: la seguente funzione deve essere runnata subito dopo che il database viene popolato
# PER ORA è USATA A LIVELLO DI TESTING IN "TESTER.PY"
def compute_coordinates():
    # esistenza file o creazione fake db
    # la variabile cached_coords è/diventa nella forma {indirizzo: (latitudine, longitudine)}

    position_data = fetch_drs_info()
    
    for dr in position_data:
        new_lat, new_long = get_coordinates(dr["indirizzo"])
        with get_cursor() as cursor:
            cursor:mariadb.Cursor

            # TODO: l'aggiornamento si può fare con sql da python o con stored procedure
            cursor.execute("UPDATE Specializzazione SET latitudine = ? , longitudine = ? WHERE Specializzazione.id = ?", (new_lat, new_long, dr["id_specializzazione"]))
    
    
    
    """

    la parte delle distanze la fai dopo, in un'altra funzione;
    nella stessa magari fai pure mappa

    """

def get_nearest_drs(client_address: str, specialization: str, latitude: Optional[float], longitude: Optional[float]) -> List[Dict[str, Any]]:
    """
    Computes distance of each doctor of the given specialization using coordinates if available else using client_address.
    Returns a list of dictionaries, each representing a doctor, with an extra field 'distanza_km', representing the distance in km from the
    coordinates used for the client. 
    """

    if not latitude or not longitude:        
        client_address_coord = get_coordinates(client_address)
    else:
        client_address_coord = (latitude, longitude)

    drs_pos_info = fetch_drs_info(specialization)
    for dr in drs_pos_info:
        dr_coord = (dr["latitudine"], dr["longitudine"])
        dr["distanza_km"] = geodesic(client_address_coord, dr_coord).km if dr_coord else float("inf")
    
    import pprint
    pprint.pprint(drs_pos_info)
    
    return sorted(drs_pos_info, key = lambda x: x["distanza_km"])
    


def create_map_html_file(client_address: str, nearest: List[Dict[str, float]], map_name:str = None, limit:int = 20) -> None:
    """
    Create an html file displaying locations on the map.
    Args:
        client_address (str): 
        nearest (List[Dict[str, float]]): sorted list of doctors
        map_name (str, optional): use this to give name, should be used to differentiate based on specialization. DO NOT specify the extension. Defaults to None.
        limit (int, optional): how many points to display on the map. By default 20.
    """
    
    client_address_coord = get_coordinates(client_address)
    # crea una mappa attorno all'indirizzo fissato
    mappa = folium.Map(location = client_address_coord, zoom_start=13)
    # marca l'indirizzo fissato
    folium.Marker(client_address_coord, tootip = "Tu sei qui", icon = folium.Icon(color='blue')).add_to(mappa)
    # seleziona i primi 5 risultati per vicinanza e esponili
    for dr in nearest[:limit]:
        dr_coord = (dr["latitudine"], dr["longitudine"])
        folium.Marker(
            dr_coord,  # coordinate
            tooltip=f"{dr['nome']} {dr['cognome']}, ({dr['specializzazione']} | {dr['indirizzo']}, {dr['distanza_km']:.2f} km)",
            icon=folium.Icon(color='red')
        ).add_to(mappa)
    """ if map_name and "." not in map_name:
        new_path = MAP_FILENAME[0], map_name, ".html"
        mappa.save(os.path.join(*new_path))
    else:
        mappa.save(os.path.join(*MAP_FILENAME)) """
    if map_name is None or "." in map_name:
        mappa.save(os.path.join(os.path.abspath(os.path.dirname(__file__)) , *MAP_FILENAME))
    else: 
        map_name += ".html"
        mappa.save(os.path.join(os.path.abspath(os.path.dirname(__file__)) , *MAP_FILENAME[:-1], map_name))
    print("Mappa salvata")

