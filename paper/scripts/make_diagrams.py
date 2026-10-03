"""Draw the two schematic figures of the paper (run lineage and censoring mechanisms).

Run from the repository root:

    python paper/scripts/make_diagrams.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# IEEE PDF checks reject Type 3 fonts; embed TrueType and use a Times-like face.
matplotlib.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "STIXGeneral",
    "mathtext.fontset": "stix",
})

OUT = Path(__file__).resolve().parents[1] / "figures"
WIDTH = 3.45  # inches; one IEEEtran column
EDGE = "#34495e"


class Canvas:
    """Axes measured in inches, so box sizes and font sizes are the printed ones."""

    def __init__(self, height: float):
        self.fig = plt.figure(figsize=(WIDTH, height))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set(xlim=(0, WIDTH), ylim=(0, height))
        self.ax.axis("off")

    def box(self, x, y, w, h, heading, detail, face="#e8f0f5"):
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.045",
                                         linewidth=0.7, edgecolor=EDGE, facecolor=face))
        self.ax.text(x + w / 2, y + h - 0.105, heading, ha="center", va="center", fontsize=7.4, weight="bold")
        self.ax.text(x + w / 2, y + (h - 0.19) / 2 + 0.01, detail, ha="center", va="center",
                     fontsize=6.9, linespacing=1.15)
        return (x, y, w, h)

    def note(self, x, y, text, **style):
        self.ax.text(x, y, text, ha="center", va="center", **style)

    def arrow(self, start, end):
        self.ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=7,
                                          linewidth=0.7, color=EDGE, shrinkA=0, shrinkB=0))

    def save(self, name: str) -> None:
        OUT.mkdir(exist_ok=True)
        self.fig.savefig(OUT / name, format="pdf", metadata={"CreationDate": None})
        plt.close(self.fig)
        print(OUT / name)


def lineage():
    c = Canvas(1.78)
    top_y, top_h = 1.10, 0.60
    c.box(0.03, top_y, 1.62, top_h, "Run S: standalone sample", "5,000 series, Phases 0–4\nfull tuning")
    c.box(1.80, top_y, 1.62, top_h, "Run P: standalone population", "50,000 series, Phases 0–4\nfast tuning")
    c.note(WIDTH / 2, 0.93, "Independent executions; neither supplies inputs to run E",
           fontsize=6.9, style="italic", color="#9a3d2d")
    y, h, w, gap = 0.04, 0.72, 1.04, 0.125
    xs = [0.03, 0.03 + w + gap, 0.03 + 2 * (w + gap)]
    c.box(xs[0], y, w, h, "Run E: Phases 0–4", "own 5,000-series\nstage", "#e9f4ec")
    c.box(xs[1], y, w, h, "Prerequisite audit", "masks, features\nand 33 hashes", "#e9f4ec")
    c.box(xs[2], y, w, h, "Run E: Phases 5–9", "lock written,\nthen final week", "#e9f4ec")
    for left, right in ((xs[0], xs[1]), (xs[1], xs[2])):
        c.arrow((left + w, y + h / 2), (right, y + h / 2))
    c.save("run_lineage.pdf")


def mechanisms():
    c = Canvas(2.30)
    top = c.box(0.62, 1.78, 2.21, 0.48, "Eligible donor day", "past-only recorded-sales mean")
    y, h, w, gap = 0.80, 0.70, 1.10, 0.065
    xs = [0.015, 0.015 + w + gap, 0.015 + 2 * (w + gap)]
    faces = ("#e9f4ec", "#f8f0e4", "#f6eaea")
    details = ("ordinary depletion;\nfitted stock level,\none possible refill",
               "promotion-sensitive;\nA's rule with stock\n× 0.6 on promotion days",
               "sustained scarcity;\nhalf of A's stock,\nno refill")
    for x, mech, detail, face in zip(xs, "ABC", details, faces):
        c.box(x, y, w, h, f"Mechanism {mech}", detail, face)
    bottom = c.box(0.30, 0.04, 2.85, 0.52, "Reconstructed visible history",
                   "features recomputed from the past only;\nscored against the unmasked donor proxy")
    tx, ty, tw, _ = top
    bx, by, bw, bh = bottom
    for x in xs:
        c.arrow((tx + tw / 2, ty), (x + w / 2, y + h))
        c.arrow((x + w / 2, y), (bx + bw / 2 + (x + w / 2 - WIDTH / 2) * 0.55, by + bh))
    c.save("mechanism_paths.pdf")


if __name__ == "__main__":
    lineage()
    mechanisms()
