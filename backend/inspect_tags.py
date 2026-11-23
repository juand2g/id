import sys
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3

# Ruta a una canción de prueba (cámbiala por una tuya real que haya pasado por Rekordbox)
filename = "data/library/202501/WACK MF.mp3" 

try:
    # Intento 1: Etiquetas fáciles (Estándar)
    tags = EasyID3(filename)
    print("--- ETIQUETAS ESTÁNDAR (EasyID3) ---")
    print(f"BPM: {tags.get('bpm', 'No encontrado')}")
    print(f"Key (Tonalidad): {tags.get('initialkey', 'No encontrado')}")
    print(f"Género: {tags.get('genre', 'No encontrado')}")

    # Intento 2: Etiquetas crudas (A veces Rekordbox guarda en campos raros)
    raw_tags = ID3(filename)
    print("\n--- ETIQUETAS CRUDAS (ID3) ---")
    for key in raw_tags.keys():
        if "TBPM" in key or "TKEY" in key: # Filtramos solo BPM y Key
            print(f"{key}: {raw_tags[key]}")

except Exception as e:
    print(f"Error leyendo: {e}")
