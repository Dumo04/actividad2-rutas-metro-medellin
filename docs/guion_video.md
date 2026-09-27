ACTIVIDAD 2 - BÚSQUEDA Y SISTEMAS BASADOS EN REGLAS
Sistema inteligente de rutas - Metro de Medellín
Santiago Duque Mora y Geraldine Ríos

GUION DEL VIDEO
Duración del montaje final: 8 minutos y 4 segundos.
Diez bloques con narración de ambos integrantes y vistas del código y resultados reales.
Los tiempos siguientes corresponden al montaje final y se redondean al segundo.

CLIP 01 - SANTIAGO - PRESENTACIÓN Y OBJETIVO
Tiempo en el video: 0:00 - 0:32

Hola, soy Santiago Duque Mora y, junto con mi compañera Geraldine Ríos, presentamos la Actividad dos: Búsqueda y sistemas basados en reglas.

En este video explicaremos un sistema que busca rutas entre estaciones del Metro de Medellín. El proyecto combina reglas lógicas y algoritmos de búsqueda en Python para responder dos preguntas: qué movimientos permite la red y cuál de las rutas disponibles tiene el menor tiempo estimado. También veremos qué ocurre cuando se simula el cierre de una estación.


CLIP 02 - SANTIAGO - CARPETA Y EJECUCIÓN
Tiempo en el video: 0:32 - 1:13

En pantalla está la carpeta del proyecto abierta en Visual Studio Code. El archivo main punto py recibe los comandos. La carpeta conocimiento contiene los datos y las reglas; motor contiene la inferencia y los algoritmos; y tests reúne las pruebas automáticas.

La búsqueda funciona con la biblioteca estándar de Python. Matplotlib se utiliza para dibujar el mapa y ReportLab para generar los documentos PDF. Antes de ejecutar los ejemplos, compruebo la versión de Python y que la terminal esté ubicada en la carpeta donde se encuentra el archivo principal.

Geraldine explicará cómo se representa ese conocimiento.


CLIP 03 - GERALDINE - HECHOS Y REGLAS
Tiempo en el video: 1:13 - 2:18

Hola, soy Geraldine Ríos. Voy a explicar los hechos y las reglas del sistema.

Esta es la base de conocimiento. Contiene sesenta y seis estaciones, diez líneas y once reglas. Un hecho describe información concreta: por ejemplo, el tramo entre Niquía y Bello pertenece a la línea A y tiene un costo de dos minutos en este modelo.

Las reglas permiten deducir nueva información. Las reglas de simetría habilitan el recorrido en ambos sentidos. Otra regla identifica los transbordos cuando dos líneas distintas sirven a la misma estación.

La regla de disponibilidad considera abierta una estación que no está registrada como cerrada. Finalmente, un movimiento solo se permite cuando sus dos extremos están disponibles. Así, las reglas afectan directamente las rutas que puede utilizar el buscador.


CLIP 04 - GERALDINE - INFERENCIA Y CONSULTAS
Tiempo en el video: 2:18 - 3:13

El motor aplica encadenamiento hacia adelante. Parte de los hechos iniciales, evalúa las reglas y agrega sus conclusiones. Repite este proceso hasta que ya no aparecen hechos nuevos. Ese estado se llama punto fijo.

En la primera consulta pregunto cuáles estaciones permiten transbordos. El programa devuelve nueve resultados, entre ellos Acevedo, San Antonio y San Javier.

La segunda consulta pregunta si es posible llegar desde Niquía hasta Arví. La respuesta es verdadera. Para deducirla, las reglas de alcanzabilidad encadenan conexiones entre estaciones. Esta consulta confirma que existe un camino; la selección del de menor costo corresponde al algoritmo de búsqueda.

Santiago explicará cómo funciona esa búsqueda.


CLIP 05 - SANTIAGO - CÓMO FUNCIONA A ESTRELLA
Tiempo en el video: 3:13 - 4:04

El grafo se construye únicamente con los movimientos inferidos por las reglas. Sobre ese grafo se ejecuta A estrella.

Cada estado incluye la estación y la línea en la que se llegó. Esto permite cobrar el costo del transbordo cuando se cambia de línea. A estrella combina el costo acumulado, llamado ge de ene, con una estimación del costo restante, llamada hache de ene.

La estimación utiliza la distancia geográfica hasta el destino dividida por la velocidad máxima calculada a partir de los tramos. Con los costos positivos y la penalización de cinco minutos de este ejemplo, la estimación no sobreestima el costo restante. Así se busca el menor tiempo dentro del modelo.

Ahora Geraldine mostrará un recorrido completo.


CLIP 06 - GERALDINE - RUTA LA ESTRELLA A ARVÍ
Tiempo en el video: 4:04 - 4:45

En este primer ejemplo indico La Estrella como origen y Arví como destino. El programa propone tomar la línea A hasta Acevedo, cambiar a la línea K hasta Santo Domingo Savio y finalmente utilizar la línea L hasta Arví.

El resultado es de setenta minutos estimados: sesenta minutos de recorrido y dos transbordos de cinco minutos cada uno. El mapa ayuda a ubicar el trayecto, mientras que la consola muestra las instrucciones.

Estos valores pertenecen a una simulación académica. Los tiempos y las coordenadas son aproximados; no representan una predicción en tiempo real del servicio.

Santiago comparará las distintas estrategias de búsqueda.


CLIP 07 - SANTIAGO - COMPARACIÓN DE ALGORITMOS
Tiempo en el video: 4:45 - 5:33

Ahora comparo cuatro estrategias para ir de Parque Berrío a La Estrella. A estrella y costo uniforme encuentran una ruta de veintitrés minutos. En este caso, A estrella expande diecisiete estados y costo uniforme expande cincuenta y tres.

La búsqueda voraz expande menos estados, pero obtiene una ruta de cuarenta y tres minutos y tres transbordos. Esto muestra que explorar menos no garantiza encontrar la mejor solución.

La búsqueda en amplitud también obtiene veintitrés minutos en este ejemplo, aunque su objetivo es minimizar el número de tramos, no el tiempo total. Por eso es importante comparar tanto el costo de la ruta como el esfuerzo de búsqueda.

Geraldine mostrará qué sucede cuando cambia la disponibilidad de la red.


CLIP 08 - GERALDINE - CIERRE Y AUSENCIA DE RUTA
Tiempo en el video: 5:33 - 6:23

Sin cierres, la ruta de Niquía a San Javier pasa por San Antonio y cuesta treinta y siete minutos. Ahora agrego el parámetro cerrar para simular que San Antonio está fuera de servicio.

Las reglas excluyen los movimientos que pasan por esa estación. El sistema encuentra una alternativa: llega a Hospital por la línea A, usa Metroplús hasta Cisneros y continúa por la línea B. El nuevo costo es de cuarenta y siete minutos, con dos transbordos.

Si mantengo el cierre y cambio el destino a Oriente, el programa informa que no existe una ruta disponible. Dentro de esta red modelada, el cierre deja aislado ese sector. El sistema reconoce la restricción en lugar de proponer un recorrido imposible.


CLIP 09 - GERALDINE - PRUEBAS Y EVIDENCIA
Tiempo en el video: 6:23 - 7:14

Para comprobar el funcionamiento ejecuto la batería de pruebas automáticas. El resultado muestra veintisiete pruebas aprobadas.

Estas pruebas revisan el análisis de las reglas, la inferencia, la simetría de los tramos, los cierres y los nombres de estaciones. También comparan A estrella con costo uniforme en siete pares de origen y destino, y comprueban la heurística para tres destinos.

El documento de pruebas reúne casos y resultados. Que estas pruebas pasen respalda los escenarios evaluados, aunque no significa que se hayan probado todas las entradas posibles. Los tiempos de cómputo pueden variar según el equipo; aquí interesa verificar las rutas, sus costos y el comportamiento ante restricciones.

Para terminar, Santiago presentará las conclusiones.


CLIP 10 - SANTIAGO - ENTREGA Y CONCLUSIÓN
Tiempo en el video: 7:14 - 8:04

La entrega se completa con el código fuente, las instrucciones de ejecución, el documento de pruebas y los enlaces al repositorio y a este video. El historial de Git permite revisar quién realizó cada cambio.

Como conclusión, las reglas determinan los movimientos válidos y A estrella selecciona una ruta de menor costo entre las opciones permitidas. Al cambiar una condición, como el cierre de una estación, cambia también la solución.

El alcance es académico: no incluye todas las rutas de transporte, horarios ni información en tiempo real. Una mejora futura sería incorporar datos operativos y criterios adicionales, como accesibilidad o tarifas. En nombre de Geraldine Ríos y Santiago Duque Mora, gracias por ver esta presentación.
