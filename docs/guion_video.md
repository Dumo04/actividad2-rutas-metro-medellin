# Guion del video (máximo 10 minutos)

Deben participar todos los integrantes. Tiempos sugeridos para 4 personas; si son menos, repartan los bloques.

| Tiempo | Quién | Qué mostrar | Qué decir (idea) |
|---|---|---|---|
| 0:00–1:00 | Integrante 1 | Presentación + mapa `docs/mapa_ruta.png` | Presentar al equipo y el problema: encontrar la mejor ruta entre dos estaciones del Metro de Medellín (metro, metrocables, tranvía y Metroplús). Explicar que se combinan una base de conocimiento en reglas y búsqueda heurística. |
| 1:00–3:00 | Integrante 2 | Archivo `conocimiento/metro_medellin.kb` | Mostrar los hechos (`tramo`, `ubicacion`, `linea`) y las 11 reglas. Explicar simetría (R2–R3), transbordo (R5), negación con `not cerrada` (R6) y la recursión de `alcanzable` (R9–R10). |
| 3:00–4:30 | Integrante 1 | `motor/logica.py` y consola | Explicar el encadenamiento hacia adelante hasta el punto fijo. Ejecutar: `python main.py -q "transbordo(X)"` y `python main.py -q "alcanzable(niquia, arvi)"`. Señalar hechos base vs. inferidos. |
| 4:30–6:30 | Integrante 3 | `motor/busqueda.py` y consola | Explicar estado, costo y heurística (haversine ÷ velocidad máxima → admisible). Ejecutar `python main.py -o "Parque Berrio" -d "La Estrella" --comparar` y leer la tabla: A* y Costo Uniforme dan el mismo óptimo (23 min), A* expande 17 nodos contra 53, y el voraz se desvía por Metroplús (43 min). |
| 6:30–8:00 | Integrante 4 | Consola + mapa | Escenarios: `-o Niquia -d "San Javier" --cerrar san_antonio` (ruta alterna por Metroplús Hospital → Cisneros), `-o Niquia -d Oriente --cerrar san_antonio` (sin ruta: el tranvía queda aislado), `--transbordo 30`. Generar el mapa con `--mapa`. |
| 8:00–9:15 | Integrante 3 | Pruebas | Ejecutar `python -m unittest discover -s tests -v` (27 OK) y mostrar el PDF `docs/Pruebas_Sistema_Rutas.pdf`. |
| 9:15–10:00 | Todos | `git log --oneline --format="%h %an %s"` | Mostrar el historial con los aportes de cada integrante y cerrar con conclusiones y limitaciones (tiempos aproximados, sin frecuencias reales). |

## Comandos en orden (para copiar durante la grabación)

```bash
python main.py --estaciones
python main.py -q "transbordo(X)"
python main.py -q "alcanzable(niquia, arvi)"
python main.py -o "La Estrella" -d "Arvi"
python main.py -o "Parque Berrio" -d "La Estrella" --comparar
python main.py -o Niquia -d "San Javier" --cerrar san_antonio
python main.py -o Niquia -d Oriente --cerrar san_antonio
python main.py -o Vallejuelos -d Universidad --transbordo 30
python main.py -o "La Estrella" -d "Arvi" --mapa docs/mapa_ruta.png
python -m unittest discover -s tests -v
git log --format="%h %an %s"
```
