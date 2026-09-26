"""
Estrategias de búsqueda sobre el espacio de estados de la red.

Estado  = (estacion_actual, linea_en_la_que_llegué)
Acción  = viajar por un tramo (movimiento inferido por la base de conocimiento)
Costo   = minutos del tramo + penalización si cambio de línea (transbordo)

Algoritmos:
  * A*   (búsqueda heurística informada)  -> f(n) = g(n) + h(n)
  * Costo uniforme (Dijkstra)             -> f(n) = g(n)
  * Amplitud (BFS)                        -> minimiza número de paradas
  * Voraz primero-el-mejor (Greedy)       -> f(n) = h(n)

Heurística h(n): distancia en línea recta (haversine) hasta el destino dividida
por la velocidad máxima observada en la red. Como ningún tramo es más rápido
que esa velocidad, h nunca sobreestima el costo real -> es ADMISIBLE y
CONSISTENTE, por lo que A* garantiza la ruta óptima.
"""
from __future__ import annotations

import heapq
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

Estado = Tuple[str, Optional[str]]


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


@dataclass
class Paso:
    desde: str
    hasta: str
    linea: str
    minutos: float
    transbordo: bool


@dataclass
class Resultado:
    algoritmo: str
    encontrada: bool
    pasos: List[Paso] = field(default_factory=list)
    costo: float = 0.0
    nodos_expandidos: int = 0
    nodos_generados: int = 0
    tiempo_ms: float = 0.0

    @property
    def estaciones(self) -> List[str]:
        if not self.pasos:
            return []
        return [self.pasos[0].desde] + [p.hasta for p in self.pasos]

    @property
    def transbordos(self) -> int:
        return sum(1 for p in self.pasos if p.transbordo)

    @property
    def paradas(self) -> int:
        return len(self.pasos)

    @property
    def minutos_viaje(self) -> float:
        return sum(p.minutos for p in self.pasos)


class Buscador:
    """Ejecuta los algoritmos sobre un grafo {estacion: [(vecina, linea, min)]}."""

    def __init__(self, grafo: Dict[str, List[Tuple[str, str, float]]],
                 coordenadas: Dict[str, Tuple[float, float]],
                 penalizacion: float):
        self.grafo = grafo
        self.coord = coordenadas
        self.penalizacion = penalizacion
        # Velocidad máxima (km/min) de la red -> garantiza heurística admisible.
        self.vmax = max(
            (haversine_km(coordenadas[a], coordenadas[b]) / t
             for a, vecinos in grafo.items() for b, _, t in vecinos if t > 0),
            default=1.0,
        ) or 1.0

    # -- heurística --------------------------------------------------------
    def heuristica(self, estacion: str, destino: str) -> float:
        return haversine_km(self.coord[estacion], self.coord[destino]) / self.vmax

    # -- sucesores ---------------------------------------------------------
    def _sucesores(self, estado: Estado):
        estacion, linea = estado
        for vecina, l, t in self.grafo.get(estacion, ()):
            cambio = linea is not None and l != linea
            costo = t + (self.penalizacion if cambio else 0)
            yield (vecina, l), costo, Paso(estacion, vecina, l, t, cambio)

    # -- plantilla genérica de búsqueda con cola de prioridad --------------
    def _mejor_primero(self, nombre: str, origen: str, destino: str,
                       prioridad: Callable[[float, str], float]) -> Resultado:
        t0 = time.perf_counter()
        res = Resultado(nombre, False)
        if origen not in self.grafo or destino not in self.grafo:
            res.tiempo_ms = (time.perf_counter() - t0) * 1000
            return res
        inicio: Estado = (origen, None)
        g: Dict[Estado, float] = {inicio: 0.0}
        padre: Dict[Estado, Tuple[Estado, Paso]] = {}
        contador = 0  # desempate estable
        frontera = [(prioridad(0.0, origen), contador, inicio)]
        cerrados = set()
        while frontera:
            _, _, estado = heapq.heappop(frontera)
            if estado in cerrados:
                continue
            cerrados.add(estado)
            res.nodos_expandidos += 1
            if estado[0] == destino:
                res.encontrada = True
                res.costo = g[estado]
                res.pasos = self._reconstruir(padre, estado)
                break
            for sig, costo, paso in self._sucesores(estado):
                nuevo_g = g[estado] + costo
                if sig not in cerrados and nuevo_g < g.get(sig, math.inf):
                    g[sig] = nuevo_g
                    padre[sig] = (estado, paso)
                    contador += 1
                    res.nodos_generados += 1
                    heapq.heappush(frontera, (prioridad(nuevo_g, sig[0]), contador, sig))
        res.tiempo_ms = (time.perf_counter() - t0) * 1000
        return res

    @staticmethod
    def _reconstruir(padre, estado) -> List[Paso]:
        pasos = []
        while estado in padre:
            estado, paso = padre[estado]
            pasos.append(paso)
        return list(reversed(pasos))

    # -- algoritmos públicos -----------------------------------------------
    def a_estrella(self, origen: str, destino: str) -> Resultado:
        return self._mejor_primero("A*", origen, destino,
                                   lambda g, e: g + self.heuristica(e, destino))

    def costo_uniforme(self, origen: str, destino: str) -> Resultado:
        return self._mejor_primero("Costo uniforme", origen, destino, lambda g, e: g)

    def voraz(self, origen: str, destino: str) -> Resultado:
        return self._mejor_primero("Voraz (greedy)", origen, destino,
                                   lambda g, e: self.heuristica(e, destino))

    def amplitud(self, origen: str, destino: str) -> Resultado:
        """BFS sobre estaciones: encuentra la ruta con MENOS paradas."""
        t0 = time.perf_counter()
        res = Resultado("Amplitud (BFS)", False)
        if origen not in self.grafo or destino not in self.grafo:
            return res
        padre: Dict[str, Tuple[str, str, float]] = {}
        visitados = {origen}
        cola = deque([origen])
        while cola:
            actual = cola.popleft()
            res.nodos_expandidos += 1
            if actual == destino:
                res.encontrada = True
                break
            for vecina, l, t in self.grafo[actual]:
                if vecina not in visitados:
                    visitados.add(vecina)
                    padre[vecina] = (actual, l, t)
                    res.nodos_generados += 1
                    cola.append(vecina)
        if res.encontrada:
            cadena, nodo = [], destino
            while nodo in padre:
                previo, l, t = padre[nodo]
                cadena.append((previo, nodo, l, t))
                nodo = previo
            cadena.reverse()
            linea = None
            for previo, nodo, l, t in cadena:
                cambio = linea is not None and l != linea
                res.pasos.append(Paso(previo, nodo, l, t, cambio))
                res.costo += t + (self.penalizacion if cambio else 0)
                linea = l
        res.tiempo_ms = (time.perf_counter() - t0) * 1000
        return res
