# Sistema inteligente de rutas – Metro de Medellín

**Actividad 3 – Inteligencia Artificial · Corporación Universitaria Iberoamericana**

Sistema basado en conocimiento que encuentra la **mejor ruta** entre dos estaciones del sistema de transporte masivo. Combina:

1. **Una base de conocimiento en reglas lógicas** (`conocimiento/metro_medellin.kb`, sintaxis tipo Prolog/Datalog) con 66 estaciones de 10 líneas del sistema (metro A y B, metrocables K, J, L, P, H y M, Tranvía de Ayacucho y Metroplús Línea 1), tramos, tiempos y 11 reglas.
2. **Un motor de inferencia** (`motor/logica.py`) con encadenamiento hacia adelante, recursión, negación estratificada (`not`) y comparaciones (`!=`). Deduce conexiones, transbordos, estaciones disponibles y alcanzabilidad.
3. **Búsqueda heurística A\*** (`motor/busqueda.py`) sobre los movimientos que infieren las reglas, comparada con Costo Uniforme, Amplitud (BFS) y Voraz.

> Modelo académico **simplificado**: las estaciones y conexiones son reales, pero los tiempos y coordenadas son aproximados. Todo se puede ajustar en el archivo `.kb` sin tocar el código.

## Integrantes

| Nombre | Aporte principal |
|---|---|
| Geraldine Ríos | Motor de inferencia y búsqueda A* |
| [Integrante 2] | Base de conocimiento (estaciones, tramos, reglas) |
| [Integrante 3] | Pruebas unitarias y documento de pruebas |
| [Integrante 4] | Interfaz de línea de comandos, mapa y video |

## Requisitos

- Python 3.8 o superior
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
python generar_pdfs.py --repo URL --video URL --integrantes "Nombre 1" "Nombre 2" ...
```

`generar_pdfs.py` ejecuta el sistema de verdad y produce:
- `docs/Pruebas_Sistema_Rutas.pdf` – casos de prueba, salidas de consola, comparación de algoritmos y resultados de las pruebas unitarias.
- `docs/Entrega_Actividad3.pdf` – documento con los enlaces del repositorio y del video.

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
- **Heurística h(n):** distancia en línea recta (haversine) al destino ÷ velocidad máxima de la red. Nunca sobreestima → **admisible y consistente**, por lo que A* devuelve la ruta óptima (se verifica en las pruebas contra Costo Uniforme).

## Trabajo en equipo con Git

Cada integrante debe hacer sus propios commits con su usuario para que el `git log` muestre su aporte:

```bash
git config user.name "Nombre Apellido"
git config user.email "correo@ejemplo.com"
git add <archivos>
git commit -m "Descripción del cambio"
git push
```

Recuerde agregar al tutor como colaborador del repositorio (GitHub: *Settings → Collaborators*).
