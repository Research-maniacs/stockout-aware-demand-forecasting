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
HEADING_PT = 8.5  # the IEEE template asks for figure labels of about 8 to 12 pt
TEXT_PT = 8.0


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
        self.ax.text(x + w / 2, y + h - 0.11, heading, ha="center", va="center", fontsize=HEADING_PT, weight="bold")
        self.ax.text(x + w / 2, y + (h - 0.21) / 2, detail, ha="center", va="center",
                     fontsize=TEXT_PT, linespacing=1.2)
        return (x, y, w, h)

    def note(self, x, y, text, **style):
        self.ax.text(x, y, text, ha="center", va="center", fontsize=TEXT_PT, **style)

    def arrow(self, start, end):
        self.ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=7,
                                          linewidth=0.7, color=EDGE, shrinkA=0, shrinkB=0))

    def save(self, name: str) -> None:
        OUT.mkdir(exist_ok=True)
        self.fig.savefig(OUT / name, format="pdf", metadata={"CreationDate": None})
        plt.close(self.fig)
        print(OUT / name)


def lineage():
    c = Canvas(1.86)
    top_y, top_h, top_w = 1.16, 0.66, 1.66
    c.box(0.02, top_y, top_w, top_h, "Run S (sample)", "5,000 series, Phases 0–4\nfull search")
    c.box(WIDTH - 0.02 - top_w, top_y, top_w, top_h, "Run P (population)", "50,000 series, Phases 0–4\nreduced search")
    c.note(WIDTH / 2, 0.97, "Independent executions; neither supplies inputs to run E", style="italic", color="#9a3d2d")
    y, h, w = 0.03, 0.72, 1.09
    gap = (WIDTH - 0.04 - 3 * w) / 2
    xs = [0.02, 0.02 + w + gap, 0.02 + 2 * (w + gap)]
    c.box(xs[0], y, w, h, "Run E", "Phases 0–4 on its\nown 5,000 series", "#e9f4ec")
    c.box(xs[1], y, w, h, "Audit", "masks, features,\n33 file hashes", "#e9f4ec")
    c.box(xs[2], y, w, h, "Run E", "Phases 5–9: lock,\nthen final week", "#e9f4ec")
    for left, right in ((xs[0], xs[1]), (xs[1], xs[2])):
        c.arrow((left + w, y + h / 2), (right, y + h / 2))
    c.save("run_lineage.pdf")


def mechanisms():
    c = Canvas(2.50)
    top = c.box(0.57, 1.95, 2.31, 0.52, "Eligible donor day", "past-only recorded-sales mean")
    y, h, w = 0.86, 0.84, 1.12
    gap = (WIDTH - 0.02 - 3 * w) / 2
    xs = [0.01, 0.01 + w + gap, 0.01 + 2 * (w + gap)]
    faces = ("#e9f4ec", "#f8f0e4", "#f6eaea")
    details = ("ordinary depletion;\nfitted stock,\none possible refill",
               "promotion-sensitive;\nstock × 0.6 on\npromotion days",
               "sustained scarcity;\nhalf of A's stock,\nno refill")
    for x, mech, detail, face in zip(xs, "ABC", details, faces):
        c.box(x, y, w, h, f"Mechanism {mech}", detail, face)
    bottom = c.box(0.22, 0.03, 3.01, 0.58, "Reconstructed visible history",
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
