"""
Sistema inteligente de rutas: une la base de conocimiento (reglas lógicas)
con las estrategias de búsqueda.

Flujo:
  1. Cargar hechos y reglas desde conocimiento/metro_medellin.kb
  2. Agregar hechos dinámicos (estaciones cerradas, penalización elegida)
  3. Inferir (encadenamiento hacia adelante) -> movimiento/4, transbordo/1 ...
  4. Construir el grafo SOLO con los hechos `movimiento` inferidos
  5. Buscar la mejor ruta con A* (u otro algoritmo) y explicarla
"""
from __future__ import annotations

import os
import unicodedata
from typing import Dict, Iterable, List, Optional, Tuple

from .busqueda import Buscador, Resultado
from .logica import BaseConocimiento

RUTA_KB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "conocimiento", "metro_medellin.kb")


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return "".join(c if c.isalnum() else "_" for c in texto).strip("_").replace("__", "_")


class EstacionNoEncontrada(ValueError):
    def __init__(self, texto: str, sugerencias: List[str]):
        self.texto = texto
        self.sugerencias = sugerencias
        msg = f"No encontré la estación '{texto}'."
        if sugerencias:
            msg += " ¿Quiso decir: " + ", ".join(sugerencias) + "?"
        super().__init__(msg)


class SistemaRutas:
    def __init__(self, ruta_kb: str = RUTA_KB, cerradas: Iterable[str] = (),
                 penalizacion: Optional[float] = None):
        self.kb = BaseConocimiento.desde_archivo(ruta_kb)
        self.nombres: Dict[str, str] = {a: n for a, n in self.kb.hechos.get("nombre", ())}
        self.lineas: Dict[str, str] = {a: n for a, n in self.kb.hechos.get("linea", ())}

        self.cerradas = [self.resolver(c) for c in cerradas]
        for c in self.cerradas:
            self.kb.agregar_hecho("cerrada", c)

        if penalizacion is None:
            penalizacion = self.kb.valor("penalizacion_transbordo", defecto=5)
        self.penalizacion = float(penalizacion)

        self.kb.inferir()

        # El grafo se construye EXCLUSIVAMENTE con lo que infieren las reglas.
        self.grafo: Dict[str, List[Tuple[str, str, float]]] = {e: [] for (e,) in self.kb.hechos.get("disponible", ())}
        for a, b, linea, t in sorted(self.kb.hechos.get("movimiento", ())):
            self.grafo[a].append((b, linea, float(t)))
        coord = {e: (lat, lon) for e, lat, lon in self.kb.hechos.get("ubicacion", ())}
        self.buscador = Buscador(self.grafo, coord, self.penalizacion)

    # -- utilidades --------------------------------------------------------
    def nombre(self, estacion: str) -> str:
        return self.nombres.get(estacion, estacion)

    def nombre_linea(self, linea: str) -> str:
        return self.lineas.get(linea, linea)

    def resolver(self, texto: str) -> str:
        """Acepta el id (san_mateo) o el nombre ("San Mateo", "san mateo")."""
        clave = normalizar(texto)
        if clave in self.nombres:
            return clave
        for ident, nombre in self.nombres.items():
            if normalizar(nombre) == clave:
                return ident
        parecidas = [self.nombres[i] for i in self.nombres
                     if clave and (clave in i or clave in normalizar(self.nombres[i]))]
        if len(parecidas) == 1:
            return next(i for i, n in self.nombres.items() if n == parecidas[0])
        raise EstacionNoEncontrada(texto, sorted(parecidas)[:6])

    def lineas_de(self, estacion: str) -> List[str]:
        return sorted(l for (l, x) in self.kb.hechos.get("sirve", ()) if x == estacion)

    def estaciones_transbordo(self) -> List[str]:
        return sorted(x for (x,) in self.kb.hechos.get("transbordo", ()))

    def es_alcanzable(self, origen: str, destino: str) -> bool:
        return (origen, destino) in self.kb.hechos.get("alcanzable", set())

    # -- búsqueda ----------------------------------------------------------
    ALGORITMOS = {
        "astar": "a_estrella",
        "ucs": "costo_uniforme",
        "bfs": "amplitud",
        "greedy": "voraz",
    }

    def buscar(self, origen: str, destino: str, algoritmo: str = "astar") -> Resultado:
        o, d = self.resolver(origen), self.resolver(destino)
        if o in self.cerradas or d in self.cerradas:
            return Resultado(algoritmo, False)
        if o == d:
            return Resultado(algoritmo, True)
        return getattr(self.buscador, self.ALGORITMOS[algoritmo])(o, d)

    def comparar(self, origen: str, destino: str) -> List[Resultado]:
        return [self.buscar(origen, destino, a) for a in self.ALGORITMOS]

    # -- explicación en lenguaje natural -----------------------------------
    def explicar(self, r: Resultado) -> List[str]:
        if not r.encontrada:
            return ["No existe una ruta disponible entre esas estaciones."]
        if not r.pasos:
            return ["El origen y el destino son la misma estación."]
        tramos: List[Tuple[str, List[str], float]] = []
        for p in r.pasos:
            if not tramos or tramos[-1][0] != p.linea:
                tramos.append((p.linea, [p.desde, p.hasta], p.minutos))
            else:
                l, est, m = tramos[-1]
                tramos[-1] = (l, est + [p.hasta], m + p.minutos)
        lineas = []
        for i, (linea, est, minutos) in enumerate(tramos, 1):
            verbo = "Tome" if i == 1 else "Haga transbordo en " + self.nombre(est[0]) + " y tome"
            lineas.append(
                f"{i}. {verbo} la {self.nombre_linea(linea)}: "
                f"{self.nombre(est[0])} -> {self.nombre(est[-1])} "
                f"({len(est) - 1} paradas, {minutos:g} min)"
            )
            lineas.append("   Pasa por: " + ", ".join(self.nombre(e) for e in est[1:-1])
                          if len(est) > 2 else "   (directo, sin paradas intermedias)")
        return lineas
