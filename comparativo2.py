# -*- coding: utf-8 -*-
# Requisitos: pip install pandas matplotlib openpyxl

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ========= CONFIG =========
XLSX_PATH = Path("CenarioApenasLifetime.xlsx")
SHEET_NAME = "Planilha1"              # ou 0, se preferir por índice
ANTECEDENT_KEY = "total_lines_D"      # troque para "changedFiles_D" se quiser
VALUE_ORDER = ["1 line", "some lines", "many lines"]
CONSEQ_ORDER = ["very short", "short", "medium", "lengthy"]
OUTPUT_PNG = Path("./grafico_daricelio_style_total_lines.png")
# =========================

# --- Normalizações de rótulos (ajuste se precisar) ---
def norm_value(v: str):
    s = str(v).strip().lower()
    if "1" in s or s in {"one line", "single line", "1 line"}:
        return "1 line"
    if "some" in s or "few" in s:
        return "some lines"
    if "many" in s or "several" in s:
        return "many lines"
    return v

def norm_conseq(c: str):
    s = str(c).strip().lower()
    if "very" in s and "short" in s: return "very short"
    if "short" in s and "very" not in s: return "short"
    if "medium" in s: return "medium"
    if "length" in s or "long" in s: return "lengthy"
    return c

def split_antecedente_valor(s: str):
    s = str(s)
    if "=" in s:
        a, v = s.split("=", 1)
        return a.strip(), v.strip()
    return s.strip(), ""

# --- Carrega e prepara base ---
raw = pd.read_excel(XLSX_PATH, sheet_name=SHEET_NAME)
col_ante = "Antecendente"   # (assim mesmo, com 'c' extra)
col_cons = "Consequente"

ants, vals = [], []
for s in raw[col_ante]:
    a, v = split_antecedente_valor(s)
    ants.append(a)
    vals.append(v)

df = pd.DataFrame({
    "Antecedente": ants,
    "ValorAnt": vals,
    "Consequente": raw[col_cons].astype(str),
    "Lift": pd.to_numeric(raw["Lift"], errors="coerce"),
    "Daricelio": pd.to_numeric(raw["Daricelio"], errors="coerce"),
}).dropna(subset=["Lift","Daricelio"], how="any")

# Filtra o antecedente desejado
sub = df[df["Antecedente"].str.fullmatch(ANTECEDENT_KEY, case=False, na=False)].copy()
if sub.empty:
    raise SystemExit(f"Nenhum dado para antecedente '{ANTECEDENT_KEY}'.")

sub["ValCat"]  = sub["ValorAnt"].apply(norm_value)
sub["ConsCat"] = sub["Consequente"].apply(norm_conseq)

# Agrega (média) por (Valor, Consequente) para obter 3 x 4 células
agg = sub.groupby(["ValCat","ConsCat"], as_index=False).agg(
    Lift=("Lift","mean"),
    Daricelio=("Daricelio","mean")
)

# Garante a ordem dos eixos
agg["ValCat"]  = pd.Categorical(agg["ValCat"],  categories=VALUE_ORDER, ordered=True)
agg["ConsCat"] = pd.Categorical(agg["ConsCat"], categories=CONSEQ_ORDER, ordered=True)
agg = agg.sort_values(["ValCat","ConsCat"])

# --- Plot no estilo Daricélio (mini-grupos por consequente) ---
x_pos = np.arange(len(VALUE_ORDER))           # 3 clusters: 1 line / some / many
n_conseq = len(CONSEQ_ORDER)                  # 4 consequentes
pair_w = 0.10                                 # largura de cada barra (seu, Daricélio)
gap_w  = 0.02                                 # espaço entre as duas barras do par
band_w = 2*pair_w + gap_w                     # largura de um par (meu vs Daricélio)
# espaçamento entre pares dentro do cluster
inner_gap = 0.05
cluster_width = n_conseq*band_w + (n_conseq-1)*inner_gap

plt.figure(figsize=(11.5, 5))

for j, cons in enumerate(CONSEQ_ORDER):
    # dados para esse consequente nas 3 categorias de linhas
    serie = agg[agg["ConsCat"] == cons].set_index("ValCat")
    y_meu = serie.reindex(VALUE_ORDER)["Lift"].values
    y_dar = serie.reindex(VALUE_ORDER)["Daricelio"].values

    # deslocamento horizontal do par dentro do cluster
    # centraliza os 4 pares dentro do cluster
    offset = (j - (n_conseq-1)/2) * (band_w + inner_gap)

    xs_meu = x_pos + offset - pair_w/2
    xs_dar = x_pos + offset + pair_w/2

    # barras
    plt.bar(xs_meu, y_meu, width=pair_w, label="Meu Lift" if j==0 else None)
    plt.bar(xs_dar, y_dar, width=pair_w, label="Daricélio" if j==0 else None)

    # (opcional) rótulo do consequente acima do “par” central do cluster
    # descomente se quiser uma legenda textual por par em cima:
    # for i, xcenter in enumerate(x_pos + offset):
    #     plt.text(xcenter, 0, cons, ha="center", va="bottom", rotation=90, fontsize=8)

# Eixos e legenda
plt.xticks(x_pos, VALUE_ORDER)
plt.xlabel("Lines of Code Modified")
plt.ylabel("Lift")
plt.title(f"{ANTECEDENT_KEY} — Comparativo (Meu vs Daricélio) por Consequente")
plt.legend(ncol=2, loc="best")
plt.tight_layout()
plt.savefig(OUTPUT_PNG, bbox_inches="tight")
plt.show()

print("Figura salva em:", OUTPUT_PNG)
