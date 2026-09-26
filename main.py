#!/usr/bin/env python3
"""
Sistema inteligente de rutas para el Metro de Medellín.

Ejemplos:
  python main.py --origen "La Estrella" --destino "Arví"
  python main.py --origen Niquia --destino "San Javier" --comparar
  python main.py --origen Niquia --destino "San Javier" --cerrar san_antonio
  python main.py --consulta "transbordo(X)"
  python main.py --estaciones
  python main.py            (modo interactivo)
"""
from __future__ import annotations

import argparse
import sys

from motor.sistema import EstacionNoEncontrada, SistemaRutas

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LINEA = "=" * 72


def imprimir_ruta(sistema: SistemaRutas, origen: str, destino: str, algoritmo: str) -> None:
    r = sistema.buscar(origen, destino, algoritmo)
    o, d = sistema.resolver(origen), sistema.resolver(destino)
    print(LINEA)
    print(f" Ruta: {sistema.nombre(o)}  ->  {sistema.nombre(d)}   [{r.algoritmo}]")
    print(LINEA)
    for linea in sistema.explicar(r):
        print(linea)
    if r.encontrada and r.pasos:
        print("-" * 72)
        print(f" Tiempo estimado : {r.costo:g} min "
              f"({r.minutos_viaje:g} en viaje + {r.transbordos} transbordo(s) x {sistema.penalizacion:g} min)")
        print(f" Paradas         : {r.paradas}")
        print(f" Nodos expandidos: {r.nodos_expandidos}   generados: {r.nodos_generados}"
              f"   tiempo de cómputo: {r.tiempo_ms:.2f} ms")
    print()


def imprimir_comparacion(sistema: SistemaRutas, origen: str, destino: str) -> None:
    o, d = sistema.resolver(origen), sistema.resolver(destino)
    print(LINEA)
    print(f" Comparación de estrategias: {sistema.nombre(o)} -> {sistema.nombre(d)}")
    print(LINEA)
    print(f" {'Algoritmo':<18}{'Costo(min)':>11}{'Paradas':>9}{'Transb.':>9}{'Expandidos':>12}{'ms':>9}")
    for r in sistema.comparar(o, d):
        if r.encontrada:
            print(f" {r.algoritmo:<18}{r.costo:>11g}{r.paradas:>9}{r.transbordos:>9}"
                  f"{r.nodos_expandidos:>12}{r.tiempo_ms:>9.2f}")
        else:
            print(f" {r.algoritmo:<18}{'sin ruta':>11}")
    print()


def imprimir_resumen_kb(sistema: SistemaRutas) -> None:
    kb = sistema.kb
    print(LINEA)
    print(" Base de conocimiento")
    print(LINEA)
    print(f" Reglas: {len(kb.reglas)}   Hechos base: {kb.hechos_base}   "
          f"Hechos inferidos: {kb.hechos_inferidos}   Iteraciones: {kb.iteraciones}")
    print(f" Estaciones: {len(sistema.nombres)}   Líneas: {len(sistema.lineas)}   "
          f"Transbordos: {len(sistema.estaciones_transbordo())}")
    if sistema.cerradas:
        print(" Cerradas: " + ", ".join(sistema.nombre(c) for c in sistema.cerradas))
    print()


def imprimir_estaciones(sistema: SistemaRutas) -> None:
    for linea_id, linea_nombre in sorted(sistema.lineas.items(), key=lambda x: x[1]):
        est = sorted({x for (l, x) in sistema.kb.hechos.get("sirve", ()) if l == linea_id},
                     key=sistema.nombre)
        print(f"\n{linea_nombre} ({len(est)} estaciones)")
        print("  " + ", ".join(f"{sistema.nombre(e)} [{e}]" for e in est))
    print("\nEstaciones de transbordo (inferidas por la regla R5): "
          + ", ".join(sistema.nombre(e) for e in sistema.estaciones_transbordo()))


def imprimir_consulta(sistema: SistemaRutas, consulta: str) -> None:
    resultados = sistema.kb.consultar(consulta)
    print(f"?- {consulta}")
    if not resultados:
        print("   false.")
    elif resultados == [{}]:
        print("   true.")
    else:
        for fila in resultados[:200]:
            print("   " + ", ".join(f"{k} = {v}" for k, v in fila.items()))
        if len(resultados) > 200:
            print(f"   ... ({len(resultados)} resultados en total)")
        else:
            print(f"   ({len(resultados)} resultado(s))")
    print()


def modo_interactivo(sistema: SistemaRutas, algoritmo: str) -> None:
    print("Modo interactivo. Escriba 'salir' para terminar, 'estaciones' para listarlas.")
    while True:
        try:
            origen = input("\nOrigen : ").strip()
            if origen.lower() in ("salir", "exit", "q"):
                break
            if origen.lower() == "estaciones":
                imprimir_estaciones(sistema)
                continue
            destino = input("Destino: ").strip()
            imprimir_ruta(sistema, origen, destino, algoritmo)
        except EstacionNoEncontrada as e:
            print(f"  ! {e}")
        except (EOFError, KeyboardInterrupt):
            print()
            break


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Sistema inteligente basado en reglas para encontrar la mejor ruta en el Metro de Medellín.")
    p.add_argument("--origen", "-o", help="Estación de origen (id o nombre)")
    p.add_argument("--destino", "-d", help="Estación de destino (id o nombre)")
    p.add_argument("--algoritmo", "-a", choices=list(SistemaRutas.ALGORITMOS), default="astar",
                   help="astar (defecto), ucs, bfs o greedy")
    p.add_argument("--comparar", action="store_true", help="Compara los 4 algoritmos")
    p.add_argument("--cerrar", nargs="+", default=[], metavar="ESTACION",
                   help="Estaciones fuera de servicio")
    p.add_argument("--transbordo", type=float, default=None, metavar="MIN",
                   help="Minutos de penalización por transbordo (defecto: el de la KB)")
    p.add_argument("--consulta", "-q", action="append", default=[],
                   help='Consulta lógica, p. ej. "transbordo(X)" o "alcanzable(niquia, arvi)"')
    p.add_argument("--estaciones", action="store_true", help="Lista lineas y estaciones")
    p.add_argument("--kb", default=None, help="Ruta a otra base de conocimiento .kb")
    p.add_argument("--mapa", metavar="ARCHIVO.png", default=None,
                   help="Guarda un mapa de la red con la ruta resaltada (requiere matplotlib)")
    args = p.parse_args(argv)

    try:
        kwargs = {"cerradas": args.cerrar, "penalizacion": args.transbordo}
        if args.kb:
            kwargs["ruta_kb"] = args.kb
        sistema = SistemaRutas(**kwargs)
    except EstacionNoEncontrada as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    imprimir_resumen_kb(sistema)

    if args.estaciones:
        imprimir_estaciones(sistema)
    for c in args.consulta:
        imprimir_consulta(sistema, c)

    try:
        if args.origen and args.destino:
            imprimir_ruta(sistema, args.origen, args.destino, args.algoritmo)
            if args.comparar:
                imprimir_comparacion(sistema, args.origen, args.destino)
            if args.mapa:
                try:
                    from motor.mapa import dibujar
                except ImportError:
                    print("Para el mapa instale matplotlib:  pip install matplotlib", file=sys.stderr)
                    return 1
                r = sistema.buscar(args.origen, args.destino, args.algoritmo)
                titulo = (f"{sistema.nombre(sistema.resolver(args.origen))} -> "
                          f"{sistema.nombre(sistema.resolver(args.destino))} ({r.algoritmo}, {r.costo:g} min)")
                print(f"Mapa guardado en: {dibujar(sistema, r, args.mapa, titulo)}")
        elif args.mapa:
            from motor.mapa import dibujar
            print(f"Mapa guardado en: {dibujar(sistema, None, args.mapa)}")
        elif args.origen or args.destino:
            p.error("Debe indicar --origen y --destino")
        elif not (args.estaciones or args.consulta):
            modo_interactivo(sistema, args.algoritmo)
    except EstacionNoEncontrada as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
