# Sistema inteligente de rutas – Metro de Medellín

**Actividad 2 - Búsqueda y sistemas basados en reglas · Corporación Universitaria Iberoamericana**

Sistema basado en conocimiento que encuentra la **mejor ruta** entre dos estaciones del sistema de transporte masivo. Combina:

1. **Una base de conocimiento en reglas lógicas** (`conocimiento/metro_medellin.kb`, sintaxis tipo Prolog/Datalog) con 66 estaciones de 10 líneas del sistema (metro A y B, metrocables K, J, L, P, H y M, Tranvía de Ayacucho y Metroplús Línea 1), tramos, tiempos y 11 reglas.
2. **Un motor de inferencia** (`motor/logica.py`) con encadenamiento hacia adelante, recursión, negación estratificada (`not`) y comparaciones (`!=`). Deduce conexiones, transbordos, estaciones disponibles y alcanzabilidad.
3. **Búsqueda heurística A\*** (`motor/busqueda.py`) sobre los movimientos que infieren las reglas, comparada con Costo Uniforme, Amplitud (BFS) y Voraz.

> Modelo académico **simplificado**: las estaciones y conexiones son reales, pero los tiempos y coordenadas son aproximados. Todo se puede ajustar en el archivo `.kb` sin tocar el código.

**Integrantes:** Santiago Duque Mora y Geraldine Ríos.

**Docente:** Sandra Isabel Rodriguez Bautista.

## Entrega académica

- [Repositorio público](https://github.com/Dumo04/actividad2-rutas-metro-medellin)
- [PDF de pruebas realizadas](docs/Pruebas_Sistema_Rutas.pdf): 10 casos funcionales y 27 pruebas unitarias.
- [PDF de entrega](docs/Entrega_Actividad2.pdf): datos del equipo y enlace al repositorio.
- [Estado de los requisitos](docs/estado_entrega.md).
- [Video explicativo en YouTube](https://www.youtube.com/watch?v=CBGlb2Fn-Ms): duración 8:04, con participación de ambos integrantes.

### Descargar y ejecutar

```bash
git clone https://github.com/Dumo04/actividad2-rutas-metro-medellin.git
cd actividad2-rutas-metro-medellin
python main.py -o "La Estrella" -d "Arví" --comparar
python -m unittest discover -s tests -v
```

También se puede usar **Code > Download ZIP**, extraerlo y abrir una terminal en la carpeta que contiene `main.py`.

## Requisitos

- Python 3.12 (versión utilizada para verificar la entrega)
- El sistema **no necesita librerías externas**. Solo el mapa (`--mapa`) y la generación de PDFs usan `matplotlib` y `reportlab`:

```bash
pip install -r requirements.txt
```

## Cómo ejecutar

```bash
# Ruta óptima con A* (se aceptan nombres con o sin tildes, o el id)
python main.py --origen "La Estrella" --destino "Arví"

# Comparar los 4 algoritmos de búsqueda
python main.py -o Niquia -d "San Javier" --comparar

# Usar otro algoritmo: astar | ucs | bfs | greedy
python main.py -o "Parque Berrio" -d "La Estrella" -a greedy

# Estaciones cerradas (la regla R6 las excluye y se recalcula todo)
python main.py -o Niquia -d "San Javier" --cerrar san_antonio

# Cambiar la penalización por transbordo (minutos)
python main.py -o Vallejuelos -d Universidad --transbordo 30

# Consultas lógicas directas a la base de conocimiento
python main.py -q "transbordo(X)"
python main.py -q "alcanzable(niquia, arvi)"
python main.py -q "conecta_lineas(linea_a, L)"
python main.py -q "sirve(L, san_antonio)"

# Listar líneas y estaciones
python main.py --estaciones

# Guardar un mapa con la ruta resaltada
python main.py -o "La Estrella" -d "Arví" --mapa docs/mapa_ruta.png

# Modo interactivo
python main.py
```

### Ejemplo de salida

```
Ruta: La Estrella  ->  Arví   [A*]
1. Tome la Línea A - Metro (Niquía - La Estrella): La Estrella -> Acevedo (17 paradas, 35 min)
2. Haga transbordo en Acevedo y tome la Línea K - Metrocable (Acevedo - Santo Domingo): Acevedo -> Santo Domingo Savio (3 paradas, 11 min)
3. Haga transbordo en Santo Domingo Savio y tome la Línea L - Metrocable Arví: Santo Domingo Savio -> Arví (1 paradas, 14 min)
 Tiempo estimado : 70 min (60 en viaje + 2 transbordo(s) x 5 min)
```

## Pruebas

```bash
python -m unittest discover -s tests -v      # 27 pruebas unitarias
python generar_pdfs.py
# Los enlaces del repositorio y del video ya están configurados.
```

`generar_pdfs.py` ejecuta el sistema de verdad y produce:
- `docs/Pruebas_Sistema_Rutas.pdf` – casos de prueba, salidas de consola, comparación de algoritmos y resultados de las pruebas unitarias.
- `docs/Entrega_Actividad2.pdf` – documento con los enlaces del repositorio y del video.

## Estructura

```
conocimiento/metro_medellin.kb Base de conocimiento: hechos + reglas lógicas
motor/logica.py                Parser y motor de inferencia (forward chaining)
motor/busqueda.py              A*, Costo uniforme, BFS y Voraz
motor/sistema.py               Une la KB con la búsqueda y explica la ruta
motor/mapa.py                  Mapa de la red (opcional, matplotlib)
main.py                        Interfaz de línea de comandos
tests/                         Pruebas unitarias
generar_pdfs.py                Genera el PDF de pruebas y el de entrega
docs/                          PDFs, mapa y guion del video
```

## Representación del conocimiento

Hechos:
```prolog
tramo(niquia, bello, linea_a, 2).            % minutos entre estaciones
ubicacion(niquia, 6.3375, -75.5440).
penalizacion_transbordo(5).
cerrada(san_antonio).                        % opcional
```

Reglas:
```prolog
conectado(X, Y, L, T) :- tramo(X, Y, L, T).
conectado(X, Y, L, T) :- tramo(Y, X, L, T).
sirve(L, X) :- conectado(X, _, L, _).
transbordo(X) :- sirve(L1, X), sirve(L2, X), L1 != L2.
disponible(X) :- estacion(X), not cerrada(X).
movimiento(X, Y, L, T) :- conectado(X, Y, L, T), disponible(X), disponible(Y).
alcanzable(X, Z) :- alcanzable(X, Y), vecina(Y, Z).
```

El grafo de búsqueda se construye **solo** con los hechos `movimiento/4` que deduce el motor.

## Búsqueda heurística

- **Estado:** (estación, línea actual) → así se puede cobrar el transbordo.
- **Costo g(n):** minutos de viaje + penalización por cada cambio de línea.
- **Heurística h(n):** distancia en línea recta (haversine) al destino ÷ velocidad máxima de la red. Con tiempos de viaje positivos y penalización de transbordo no negativa, esta cota es **admisible y consistente**. En las pruebas del modelo se contrasta el costo de A* con Costo Uniforme.

## Resultados comprobados

Los tiempos corresponden al modelo académico, no a una predicción del servicio real.

| Caso | Resultado |
|---|---|
| La Estrella → Arví | 70 min: 60 de viaje + 2 transbordos de 5 min |
| Parque Berrío → La Estrella, A* | 23 min; 17 estados expandidos |
| Mismo par, costo uniforme | 23 min; 53 estados expandidos |
| Mismo par, BFS | 23 min; 65 estaciones expandidas |
| Mismo par, voraz | 43 min; 12 estados expandidos |
| Niquía → San Javier | 37 min |
| Mismo par, San Antonio cerrada | 47 min, vía Hospital y Cisneros |
| Niquía → Oriente, San Antonio cerrada | Sin ruta disponible |

El PDF incluye las salidas reales y los detalles de las pruebas. La consulta `transbordo(X)` devuelve nueve estaciones en el escenario base.

## Historial y participación

Se conservan los ocho commits originales de Geraldine Ríos correspondientes al desarrollo del sistema. La preparación de la entrega, la actualización del guion, los nombres, las instrucciones, los enlaces y los documentos de pruebas se registra en commits posteriores de Santiago Duque Mora. No se reescribieron autores ni fechas del historial recibido.

```bash
git log --format="%h %an - %s"
```

## Pendientes para cerrar la entrega del campus

Agregar a Sandra Isabel Rodriguez Bautista como colaboradora cuando se conozca su usuario de GitHub. El repositorio público permite consultarlo, pero no sustituye ese requisito de la actividad.

El envío del PDF al campus corresponde a la entrega académica y no se realiza desde este repositorio.
