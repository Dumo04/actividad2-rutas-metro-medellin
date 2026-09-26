"""Pruebas del sistema de rutas sobre la base de conocimiento del Metro de Medellín."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.sistema import EstacionNoEncontrada, SistemaRutas

SISTEMA = SistemaRutas()

# Pares origen/destino usados para comparar algoritmos.
PARES = [
    ("la_estrella", "arvi"),
    ("niquia", "san_javier"),
    ("el_progreso", "villa_sierra"),
    ("u_de_medellin", "la_aurora"),
    ("parque_berrio", "la_estrella"),
    ("vallejuelos", "universidad"),
    ("parque_aranjuez", "trece_de_noviembre"),
]


class TestBaseConocimiento(unittest.TestCase):
    def test_estaciones_de_transbordo_inferidas(self):
        esperadas = {"san_antonio", "acevedo", "san_javier", "santo_domingo", "miraflores",
                     "oriente", "industriales", "cisneros", "hospital"}
        self.assertEqual(set(SISTEMA.estaciones_transbordo()), esperadas)

    def test_simetria_de_tramos(self):
        kb = SISTEMA.kb
        self.assertTrue(kb.es_verdad("conectado(niquia, bello, linea_a, 2)"))
        self.assertTrue(kb.es_verdad("conectado(bello, niquia, linea_a, 2)"))

    def test_red_conexa(self):
        # Regla R9-R10: desde Niquía se alcanza cualquier estación.
        for est in SISTEMA.nombres:
            if est != "niquia":
                self.assertTrue(SISTEMA.es_alcanzable("niquia", est), est)

    def test_lineas_de_san_antonio(self):
        self.assertEqual(SISTEMA.lineas_de("san_antonio"), ["linea_a", "linea_b", "tranvia_t"])


class TestBusqueda(unittest.TestCase):
    def test_ruta_la_estrella_arvi(self):
        r = SISTEMA.buscar("La Estrella", "Arví")
        self.assertTrue(r.encontrada)
        self.assertEqual(r.estaciones[0], "la_estrella")
        self.assertEqual(r.estaciones[-1], "arvi")
        self.assertEqual(r.costo, 70)
        self.assertEqual(r.transbordos, 2)
        self.assertEqual([p.linea for p in r.pasos][-1], "linea_l")

    def test_misma_linea_sin_transbordo(self):
        r = SISTEMA.buscar("Niquía", "Poblado")
        self.assertEqual(r.transbordos, 0)
        self.assertEqual(r.costo, 2 + 3 + 2 + 2 + 2 + 2 + 2 + 2 + 2 + 1 + 1 + 1 + 2 + 3)

    def test_ruta_continua(self):
        for o, d in PARES:
            r = SISTEMA.buscar(o, d)
            for p1, p2 in zip(r.pasos, r.pasos[1:]):
                self.assertEqual(p1.hasta, p2.desde)

    def test_a_estrella_es_optimo(self):
        # A* con heurística admisible debe igualar a Costo Uniforme (Dijkstra).
        for o, d in PARES:
            a = SISTEMA.buscar(o, d, "astar")
            u = SISTEMA.buscar(o, d, "ucs")
            self.assertAlmostEqual(a.costo, u.costo, msg=f"{o}->{d}")
            self.assertLessEqual(a.nodos_expandidos, u.nodos_expandidos)

    def test_bfs_minimiza_paradas(self):
        for o, d in PARES:
            b = SISTEMA.buscar(o, d, "bfs")
            a = SISTEMA.buscar(o, d, "astar")
            self.assertLessEqual(b.paradas, a.paradas)
            self.assertGreaterEqual(b.costo, a.costo)

    def test_voraz_no_garantiza_optimo(self):
        # Desde Parque Berrío la heurística "engaña" a la búsqueda voraz.
        v = SISTEMA.buscar("parque_berrio", "la_estrella", "greedy")
        a = SISTEMA.buscar("parque_berrio", "la_estrella", "astar")
        self.assertGreater(v.costo, a.costo)

    def test_heuristica_admisible(self):
        # h(n) nunca supera el costo real óptimo hasta el destino.
        for destino in ("la_estrella", "arvi", "la_aurora"):
            for est in SISTEMA.nombres:
                if est == destino:
                    continue
                real = SISTEMA.buscar(est, destino, "ucs").costo
                self.assertLessEqual(SISTEMA.buscador.heuristica(est, destino), real + 1e-9, est)

    def test_mismo_origen_destino(self):
        r = SISTEMA.buscar("poblado", "poblado")
        self.assertTrue(r.encontrada)
        self.assertEqual(r.costo, 0)


class TestEscenarios(unittest.TestCase):
    def test_cierre_con_ruta_alterna(self):
        normal = SISTEMA.buscar("niquia", "san_javier")
        self.assertIn("san_antonio", normal.estaciones)
        s = SistemaRutas(cerradas=["san_antonio"])
        r = s.buscar("niquia", "san_javier")
        # Sin San Antonio, se llega a la Línea B por Metroplús (Hospital -> Cisneros).
        self.assertTrue(r.encontrada)
        self.assertNotIn("san_antonio", r.estaciones)
        self.assertIn("metroplus_1", {p.linea for p in r.pasos})

    def test_estacion_cerrada_aisla_tranvia(self):
        s = SistemaRutas(cerradas=["san_antonio"])
        self.assertFalse(s.buscar("niquia", "oriente").encontrada)
        self.assertFalse(s.es_alcanzable("niquia", "oriente"))

    def test_penalizacion_cambia_ruta(self):
        barato = SistemaRutas(penalizacion=0).buscar("vallejuelos", "universidad")
        caro = SistemaRutas(penalizacion=30).buscar("vallejuelos", "universidad")
        self.assertLessEqual(caro.transbordos, barato.transbordos)

    def test_nombres_flexibles(self):
        self.assertEqual(SISTEMA.resolver("Itagui"), "itagui")
        self.assertEqual(SISTEMA.resolver("santo domingo savio"), "santo_domingo")
        self.assertEqual(SISTEMA.resolver("ARVI"), "arvi")

    def test_estacion_inexistente(self):
        with self.assertRaises(EstacionNoEncontrada):
            SISTEMA.buscar("Marte", "poblado")

    def test_estacion_ambigua(self):
        with self.assertRaises(EstacionNoEncontrada) as ctx:
            SISTEMA.resolver("Parque")
        self.assertGreaterEqual(len(ctx.exception.sugerencias), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
