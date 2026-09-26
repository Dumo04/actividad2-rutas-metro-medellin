"""Pruebas del motor de inferencia lógica (independiente de la red de transporte)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.logica import (BaseConocimiento, ErrorBaseConocimiento, ErrorSintaxis,
                          parsear)


def kb_de(texto):
    return BaseConocimiento(parsear(texto)).inferir()


class TestParser(unittest.TestCase):
    def test_hechos_y_reglas(self):
        c = parsear('padre(ana, luis). abuelo(X, Z) :- padre(X, Y), padre(Y, Z).')
        self.assertEqual(len(c), 2)
        self.assertEqual(c[0].cabeza.predicado, "padre")
        self.assertEqual(len(c[1].cuerpo), 2)

    def test_numeros_cadenas_comentarios(self):
        c = parsear('% comentario\nubicacion(x, 4.58, -74.2). nombre(x, "San Mateo").')
        self.assertEqual(c[0].cabeza.args, ("x", 4.58, -74.2))
        self.assertEqual(c[1].cabeza.args, ("x", "San Mateo"))

    def test_error_sintaxis(self):
        with self.assertRaises(ErrorSintaxis):
            parsear("hecho(a, b")


class TestInferencia(unittest.TestCase):
    def test_regla_simple(self):
        kb = kb_de('padre(ana, luis). padre(luis, eva). abuelo(X, Z) :- padre(X, Y), padre(Y, Z).')
        self.assertTrue(kb.es_verdad("abuelo(ana, eva)"))
        self.assertFalse(kb.es_verdad("abuelo(luis, eva)"))

    def test_recursion_cierre_transitivo(self):
        kb = kb_de("""
            arista(a, b). arista(b, c). arista(c, d).
            camino(X, Y) :- arista(X, Y).
            camino(X, Z) :- camino(X, Y), arista(Y, Z).
        """)
        self.assertTrue(kb.es_verdad("camino(a, d)"))
        self.assertEqual(len(kb.consultar("camino(a, X)")), 3)

    def test_negacion_estratificada(self):
        kb = kb_de("""
            est(a). est(b). cerrada(b).
            abierta(X) :- est(X), not cerrada(X).
        """)
        self.assertEqual(kb.consultar("abierta(X)"), [{"X": "a"}])

    def test_comparacion(self):
        kb = kb_de("s(l1, x). s(l2, x). s(l1, y). t(X) :- s(A, X), s(B, X), A != B.")
        self.assertEqual(kb.consultar("t(X)"), [{"X": "x"}])

    def test_regla_insegura(self):
        with self.assertRaises(ErrorBaseConocimiento):
            kb_de("p(a). q(X, Y) :- p(X).")

    def test_negacion_circular(self):
        with self.assertRaises(ErrorBaseConocimiento):
            kb_de("b(a). p(X) :- b(X), not q(X). q(X) :- b(X), not p(X).")


if __name__ == "__main__":
    unittest.main(verbosity=2)
