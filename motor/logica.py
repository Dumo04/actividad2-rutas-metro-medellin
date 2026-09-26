"""
Motor de inferencia lógica (estilo Datalog) para la base de conocimiento.

Componentes:
  * Term / Atomo / Regla: representación del conocimiento.
  * parsear(): convierte el texto del archivo .kb en hechos y reglas.
  * BaseConocimiento: aplica encadenamiento hacia adelante (forward chaining)
    semi-ingenuo, con negación estratificada (`not`) y comparaciones
    (`!=`, `==`, `<`, `>`, `<=`, `>=`), hasta alcanzar el punto fijo.
  * consultar(): responde preguntas como  transbordo(X)  o  alcanzable(bosa, Y).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Representación
# ---------------------------------------------------------------------------
class Variable:
    __slots__ = ("nombre",)

    def __init__(self, nombre: str):
        self.nombre = nombre

    def __repr__(self) -> str:  # pragma: no cover - solo depuración
        return self.nombre

    def __eq__(self, otro) -> bool:
        return isinstance(otro, Variable) and otro.nombre == self.nombre

    def __hash__(self) -> int:
        return hash(("var", self.nombre))


def es_variable(t) -> bool:
    return isinstance(t, Variable)


@dataclass(frozen=True)
class Atomo:
    predicado: str
    args: Tuple
    negado: bool = False

    def __str__(self) -> str:
        texto = f"{self.predicado}({', '.join(_fmt(a) for a in self.args)})"
        return f"not {texto}" if self.negado else texto


@dataclass(frozen=True)
class Comparacion:
    op: str
    izq: object
    der: object

    def __str__(self) -> str:
        return f"{_fmt(self.izq)} {self.op} {_fmt(self.der)}"


@dataclass
class Regla:
    cabeza: Atomo
    cuerpo: List[object] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.cuerpo:
            return f"{self.cabeza}."
        return f"{self.cabeza} :- {', '.join(str(c) for c in self.cuerpo)}."


def _fmt(valor) -> str:
    if isinstance(valor, Variable):
        return valor.nombre
    if isinstance(valor, str) and not re.fullmatch(r"[a-z][a-zA-Z0-9_]*", valor):
        return f'"{valor}"'
    return str(valor)


# ---------------------------------------------------------------------------
# Analizador léxico / sintáctico
# ---------------------------------------------------------------------------
class ErrorSintaxis(Exception):
    pass


_TOKEN = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<comentario>%[^\n]*)
  | (?P<numero>-?\d+(?:\.\d+)?)
  | (?P<cadena>"[^"]*")
  | (?P<implica>:-)
  | (?P<op>!=|==|<=|>=|<|>)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<punt>[(),.])
    """,
    re.VERBOSE,
)


def _tokenizar(texto: str) -> List[Tuple[str, str, int]]:
    tokens, pos, linea = [], 0, 1
    while pos < len(texto):
        m = _TOKEN.match(texto, pos)
        if not m:
            raise ErrorSintaxis(f"Línea {linea}: carácter inesperado {texto[pos]!r}")
        tipo, valor = m.lastgroup, m.group()
        if tipo not in ("ws", "comentario"):
            tokens.append((tipo, valor, linea))
        linea += valor.count("\n")
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def ver(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None, -1)

    def tomar(self, esperado: Optional[str] = None):
        tok = self.ver()
        if tok[0] is None:
            raise ErrorSintaxis("Fin de archivo inesperado")
        if esperado is not None and tok[1] != esperado:
            raise ErrorSintaxis(f"Línea {tok[2]}: se esperaba {esperado!r} y llegó {tok[1]!r}")
        self.i += 1
        return tok

    def programa(self) -> List[Regla]:
        clausulas = []
        while self.ver()[0] is not None:
            clausulas.append(self.clausula())
        return clausulas

    def clausula(self) -> Regla:
        cabeza = self.atomo()
        cuerpo = []
        if self.ver()[1] == ":-":
            self.tomar(":-")
            cuerpo.append(self.literal())
            while self.ver()[1] == ",":
                self.tomar(",")
                cuerpo.append(self.literal())
        self.tomar(".")
        return Regla(cabeza, cuerpo)

    def literal(self):
        tipo, valor, _ = self.ver()
        if tipo == "ident" and valor == "not":
            self.tomar()
            a = self.atomo()
            return Atomo(a.predicado, a.args, negado=True)
        # ¿comparación?  termino OP termino
        siguiente = self.t[self.i + 1] if self.i + 1 < len(self.t) else (None, None, -1)
        if siguiente[0] == "op":
            izq = self.termino()
            op = self.tomar()[1]
            der = self.termino()
            return Comparacion(op, izq, der)
        return self.atomo()

    def atomo(self) -> Atomo:
        tipo, nombre, linea = self.tomar()
        if tipo != "ident" or nombre[0].isupper() or nombre[0] == "_":
            raise ErrorSintaxis(f"Línea {linea}: nombre de predicado inválido {nombre!r}")
        args = []
        if self.ver()[1] == "(":
            self.tomar("(")
            args.append(self.termino())
            while self.ver()[1] == ",":
                self.tomar(",")
                args.append(self.termino())
            self.tomar(")")
        return Atomo(nombre, tuple(args))

    _anonimas = 0

    def termino(self):
        tipo, valor, linea = self.tomar()
        if tipo == "numero":
            return float(valor) if "." in valor else int(valor)
        if tipo == "cadena":
            return valor[1:-1]
        if tipo == "ident":
            if valor == "_":
                _Parser._anonimas += 1
                return Variable(f"_G{_Parser._anonimas}")
            if valor[0].isupper() or valor[0] == "_":
                return Variable(valor)
            return valor
        raise ErrorSintaxis(f"Línea {linea}: término inválido {valor!r}")


def parsear(texto: str) -> List[Regla]:
    """Convierte texto con sintaxis tipo Prolog en una lista de cláusulas."""
    return _Parser(_tokenizar(texto)).programa()


def parsear_consulta(texto: str) -> List[object]:
    """Convierte 'transbordo(X), sirve(calle_80, X)' en una lista de literales."""
    texto = texto.strip()
    if texto.endswith("."):
        texto = texto[:-1]
    p = _Parser(_tokenizar(texto))
    literales = [p.literal()]
    while p.ver()[1] == ",":
        p.tomar(",")
        literales.append(p.literal())
    if p.ver()[0] is not None:
        raise ErrorSintaxis(f"Sobra texto en la consulta: {p.ver()[1]!r}")
    return literales


# ---------------------------------------------------------------------------
# Unificación y evaluación
# ---------------------------------------------------------------------------
Sustitucion = Dict[Variable, object]


def _valor(t, s: Sustitucion):
    return s.get(t, t) if es_variable(t) else t


def _unificar(patron: Tuple, hecho: Tuple, s: Sustitucion) -> Optional[Sustitucion]:
    if len(patron) != len(hecho):
        return None
    nueva = s
    for p, h in zip(patron, hecho):
        if es_variable(p):
            if p in nueva:
                if nueva[p] != h:
                    return None
            else:
                if nueva is s:
                    nueva = dict(s)
                nueva[p] = h
        elif p != h:
            return None
    return nueva


_OPS = {
    "!=": lambda a, b: a != b,
    "==": lambda a, b: a == b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


class ErrorBaseConocimiento(Exception):
    pass


class BaseConocimiento:
    """Hechos + reglas, con inferencia por encadenamiento hacia adelante."""

    def __init__(self, clausulas: Iterable[Regla] = ()):
        self.reglas: List[Regla] = []
        self.hechos: Dict[str, Set[Tuple]] = {}
        self._indice: Dict[Tuple[str, int, object], Set[Tuple]] = {}
        self.hechos_base = 0
        self.hechos_inferidos = 0
        self.iteraciones = 0
        for c in clausulas:
            self.agregar(c)

    # -- construcción ------------------------------------------------------
    @classmethod
    def desde_archivo(cls, ruta: str) -> "BaseConocimiento":
        with open(ruta, encoding="utf-8") as f:
            return cls(parsear(f.read()))

    def agregar(self, clausula: Regla) -> None:
        if clausula.cuerpo:
            self._validar_regla(clausula)
            self.reglas.append(clausula)
        else:
            if any(es_variable(a) for a in clausula.cabeza.args):
                raise ErrorBaseConocimiento(f"Un hecho no puede tener variables: {clausula}")
            if self._insertar(clausula.cabeza.predicado, clausula.cabeza.args):
                self.hechos_base += 1

    def agregar_hecho(self, predicado: str, *args) -> None:
        self.agregar(Regla(Atomo(predicado, tuple(args))))

    def _validar_regla(self, r: Regla) -> None:
        """Seguridad: toda variable de la cabeza, de un `not` o de una
        comparación debe aparecer en algún literal positivo del cuerpo."""
        positivas = {
            a for lit in r.cuerpo if isinstance(lit, Atomo) and not lit.negado
            for a in lit.args if es_variable(a)
        }
        def revisar(terms, donde):
            for t in terms:
                if es_variable(t) and not t.nombre.startswith("_G") and t not in positivas:
                    raise ErrorBaseConocimiento(f"Regla insegura, variable {t} en {donde}: {r}")
        revisar(r.cabeza.args, "la cabeza")
        for lit in r.cuerpo:
            if isinstance(lit, Comparacion):
                revisar((lit.izq, lit.der), "una comparación")
            elif lit.negado:
                revisar(lit.args, "una negación")

    def _insertar(self, pred: str, args: Tuple) -> bool:
        conjunto = self.hechos.setdefault(pred, set())
        if args in conjunto:
            return False
        conjunto.add(args)
        for i, v in enumerate(args):
            self._indice.setdefault((pred, i, v), set()).add(args)
        return True

    # -- estratificación (para la negación) --------------------------------
    def _estratos(self) -> List[List[Regla]]:
        preds = {r.cabeza.predicado for r in self.reglas}
        estrato = {p: 0 for p in preds}
        cambio = True
        limite = len(preds) + 1
        while cambio:
            cambio = False
            for r in self.reglas:
                h = r.cabeza.predicado
                for lit in r.cuerpo:
                    if not isinstance(lit, Atomo) or lit.predicado not in estrato:
                        continue
                    minimo = estrato[lit.predicado] + (1 if lit.negado else 0)
                    if estrato[h] < minimo:
                        estrato[h] = minimo
                        cambio = True
                        if estrato[h] > limite:
                            raise ErrorBaseConocimiento(
                                f"Negación circular (no estratificable) en '{h}'")
        niveles: Dict[int, List[Regla]] = {}
        for r in self.reglas:
            niveles.setdefault(estrato[r.cabeza.predicado], []).append(r)
        return [niveles[k] for k in sorted(niveles)]

    # -- encadenamiento hacia adelante -------------------------------------
    def inferir(self) -> "BaseConocimiento":
        """Deriva todos los hechos implícitos (punto fijo, semi-ingenuo)."""
        total_antes = sum(len(v) for v in self.hechos.values())
        for reglas in self._estratos():
            cabezas = {r.cabeza.predicado for r in reglas}
            # Primera pasada: evaluación completa.
            delta: Dict[str, Set[Tuple]] = {}
            for r in reglas:
                for s in self._resolver(r.cuerpo, {}, None, None):
                    args = tuple(_valor(a, s) for a in r.cabeza.args)
                    if args not in self.hechos.get(r.cabeza.predicado, ()):
                        delta.setdefault(r.cabeza.predicado, set()).add(args)
            self._volcar(delta)
            self.iteraciones += 1
            # Pasadas siguientes: solo combinaciones que usan algún hecho nuevo.
            while delta:
                nuevo: Dict[str, Set[Tuple]] = {}
                for r in reglas:
                    for i, lit in enumerate(r.cuerpo):
                        if (isinstance(lit, Atomo) and not lit.negado
                                and lit.predicado in cabezas and lit.predicado in delta):
                            for s in self._resolver(r.cuerpo, {}, i, delta[lit.predicado]):
                                args = tuple(_valor(a, s) for a in r.cabeza.args)
                                if args not in self.hechos.get(r.cabeza.predicado, ()):
                                    nuevo.setdefault(r.cabeza.predicado, set()).add(args)
                self._volcar(nuevo)
                delta = nuevo
                self.iteraciones += 1
        self.hechos_inferidos = sum(len(v) for v in self.hechos.values()) - total_antes
        return self

    def _volcar(self, delta: Dict[str, Set[Tuple]]) -> None:
        for pred, filas in delta.items():
            for args in filas:
                self._insertar(pred, args)

    def _candidatos(self, lit: Atomo, s: Sustitucion) -> Iterable[Tuple]:
        mejor = None
        for i, a in enumerate(lit.args):
            v = _valor(a, s)
            if not es_variable(v):
                c = self._indice.get((lit.predicado, i, v), set())
                if mejor is None or len(c) < len(mejor):
                    mejor = c
                    if not mejor:
                        break
        return mejor if mejor is not None else self.hechos.get(lit.predicado, set())

    def _resolver(self, cuerpo, s: Sustitucion, i_delta, filas_delta) -> Iterator[Sustitucion]:
        # Orden de evaluación: primero literales positivos, luego filtros.
        orden = sorted(range(len(cuerpo)),
                       key=lambda k: 0 if (isinstance(cuerpo[k], Atomo) and not cuerpo[k].negado) else 1)
        if i_delta is not None:
            orden.remove(i_delta)
            orden.insert(0, i_delta)
        yield from self._paso(cuerpo, orden, 0, s, i_delta, filas_delta)

    def _paso(self, cuerpo, orden, k, s, i_delta, filas_delta):
        if k == len(orden):
            yield s
            return
        idx = orden[k]
        lit = cuerpo[idx]
        if isinstance(lit, Comparacion):
            a, b = _valor(lit.izq, s), _valor(lit.der, s)
            try:
                ok = _OPS[lit.op](a, b)
            except TypeError:
                ok = False
            if ok:
                yield from self._paso(cuerpo, orden, k + 1, s, i_delta, filas_delta)
            return
        if lit.negado:
            patron = tuple(_valor(a, s) for a in lit.args)
            existe = any(_unificar(patron, h, {}) is not None
                         for h in self._candidatos(lit, s))
            if not existe:
                yield from self._paso(cuerpo, orden, k + 1, s, i_delta, filas_delta)
            return
        filas = filas_delta if idx == i_delta else self._candidatos(lit, s)
        for hecho in list(filas):
            s2 = _unificar(lit.args, hecho, s)
            if s2 is not None:
                yield from self._paso(cuerpo, orden, k + 1, s2, i_delta, filas_delta)

    # -- consultas ---------------------------------------------------------
    def consultar(self, consulta) -> List[Dict[str, object]]:
        """Consulta sobre los hechos (base + inferidos).

        >>> kb.consultar("transbordo(X)")
        [{'X': 'ricaurte'}, ...]
        """
        literales = parsear_consulta(consulta) if isinstance(consulta, str) else consulta
        variables = []
        for lit in literales:
            args = lit.args if isinstance(lit, Atomo) else (lit.izq, lit.der)
            for a in args:
                if es_variable(a) and not a.nombre.startswith("_G") and a not in variables:
                    variables.append(a)
        vistos, resultados = set(), []
        for s in self._resolver(literales, {}, None, None):
            fila = tuple(_valor(v, s) for v in variables)
            if fila not in vistos:
                vistos.add(fila)
                resultados.append({v.nombre: val for v, val in zip(variables, fila)})
        resultados.sort(key=lambda d: tuple(str(x) for x in d.values()))
        return resultados

    def es_verdad(self, consulta: str) -> bool:
        return bool(self.consultar(consulta))

    def valor(self, predicado: str, *args, defecto=None):
        """Devuelve el último argumento de predicado(args..., V) o `defecto`."""
        for fila in self.hechos.get(predicado, ()):
            if fila[:len(args)] == args:
                return fila[len(args)]
        return defecto

    def total_hechos(self) -> int:
        return sum(len(v) for v in self.hechos.values())
