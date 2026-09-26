"""Dibuja la red y resalta una ruta (requiere matplotlib, es opcional)."""
from __future__ import annotations

from typing import Optional

from .busqueda import Resultado

COLORES = {
    "linea_a": "#1f5fa8",
    "linea_b": "#f28c28",
    "linea_k": "#2ca02c",
    "linea_l": "#8c564b",
    "linea_j": "#e6b800",
    "linea_p": "#d62728",
    "linea_h": "#9467bd",
    "linea_m": "#e377c2",
    "tranvia_t": "#17becf",
    "metroplus_1": "#4d7a1f",
}


def dibujar(sistema, resultado: Optional[Resultado], archivo: str, titulo: str = "") -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    coord = sistema.buscador.coord
    fig, ax = plt.subplots(figsize=(9, 10), dpi=130)
    dibujados = set()
    for a, vecinos in sistema.grafo.items():
        for b, linea, _ in vecinos:
            if (b, a, linea) in dibujados:
                continue
            dibujados.add((a, b, linea))
            (y1, x1), (y2, x2) = coord[a], coord[b]
            ax.plot([x1, x2], [y1, y2], color=COLORES.get(linea, "#999"), lw=3, alpha=0.35, zorder=1)
    for linea, color in COLORES.items():
        ax.plot([], [], color=color, lw=3, alpha=0.6, label=sistema.nombre_linea(linea))

    transbordos = set(sistema.estaciones_transbordo())
    for est, (lat, lon) in coord.items():
        cerrada = est in sistema.cerradas
        ax.scatter(lon, lat, s=40 if est in transbordos else 12,
                   c="black" if not cerrada else "red", marker="x" if cerrada else "o", zorder=3)
        if est in transbordos or cerrada:
            ax.annotate(sistema.nombre(est), (lon, lat), fontsize=7, xytext=(4, 3),
                        textcoords="offset points")

    if resultado and resultado.encontrada and resultado.pasos:
        for p in resultado.pasos:
            (y1, x1), (y2, x2) = coord[p.desde], coord[p.hasta]
            ax.plot([x1, x2], [y1, y2], color=COLORES.get(p.linea, "k"), lw=5, zorder=2)
        o, d = resultado.estaciones[0], resultado.estaciones[-1]
        for est, marca, txt in ((o, "^", "ORIGEN"), (d, "*", "DESTINO")):
            lat, lon = coord[est]
            ax.scatter(lon, lat, s=260, marker=marca, c="gold", edgecolors="black", zorder=4)
            ax.annotate(f"{txt}: {sistema.nombre(est)}", (lon, lat), fontsize=9, weight="bold",
                        xytext=(0, -18), textcoords="offset points", ha="center",
                        bbox=dict(boxstyle="round", fc="white", alpha=0.8))

    ax.set_title(titulo or "Red simplificada Metro de Medellín")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=7)
    ax.margins(x=0.12, y=0.05)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(archivo)
    plt.close(fig)
    return archivo
