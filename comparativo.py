# -*- coding: utf-8 -*-
# gerar_graficos_por_antecedente.py
# Requisitos: pip install pandas matplotlib openpyxl

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==================== CONFIGURE AQUI ====================
XLSX_PATH = Path("CenarioApenasLifetime.xlsx")   # <-- seu XLSX
OUT_DIR   = Path("GraficosGerados")              # <-- pasta saída
TOPN      = 10                                                     # Top N por |Diff|
SHEET_NAME = "Planilha1"  # ou 0; mantenha "Planilha1" se for o nome da aba
# =======================================================

ANTECEDENTES_VALIDOS = [
    "changedFiles_D",
    "commitsPull_D",
    "requester_experience_project",
    "total_lines_D",
    "coreTeamFollowsRequester",
    "first_Pull",
    "followers_boolean",
    "life_time",
    "typeDeveloper",
]

def split_antecedente_valor(s: str):
    s = str(s)
    if "=" in s:
        a, v = s.split("=", 1)
        return a.strip(), v.strip()
    return s.strip(), ""

def carregar_df(xlsx_path: Path, sheet_name=None):
    raw = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    # se vier dict, pega a primeira não vazia
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, pd.DataFrame) and len(v) > 0:
                raw = v
                break

    # colunas da sua planilha
    col_ante = "Antecendente"   # (assim mesmo, com 'c' extra)
    col_cons = "Consequente"
    col_lift = "Lift"
    col_dari = "Daricelio"

    # separa antecedente/valor
    ants, vals = [], []
    for s in raw[col_ante]:
        a, v = split_antecedente_valor(s)
        ants.append(a)
        vals.append(v)

    df = pd.DataFrame({
        "Antecedente": ants,
        "ValorAnt": vals,
        "Consequente": raw[col_cons].astype(str),
        "Lift": pd.to_numeric(raw[col_lift], errors="coerce"),
        "Daricelio": pd.to_numeric(raw[col_dari], errors="coerce"),
    }).dropna(subset=["Lift","Daricelio"], how="any").reset_index(drop=True)

    # rótulo único
    df["LabelFull"] = (
        df["Antecedente"].str.strip() + " = " + df["ValorAnt"].str.strip()
    ).str.strip() + " \u2192 " + df["Consequente"].str.strip()

    df["Diff"] = df["Lift"] - df["Daricelio"]
    df["AbsDiff"] = df["Diff"].abs()
    return df

def plot_barras_duplas(sub, titulo, out_png):
    x = np.arange(len(sub))
    width = 0.4
    plt.figure(figsize=(12,5))
    plt.bar(x - width/2, sub["Lift"], width=width, label="Lift")
    plt.bar(x + width/2, sub["Daricelio"], width=width, label="Daricélio")
    plt.xticks(ticks=x, labels=sub["LabelFull"], rotation=45, ha="right")
    plt.title(titulo)
    plt.xlabel("Regra / Cenário")
    plt.ylabel("Valor")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = carregar_df(XLSX_PATH, SHEET_NAME)
    # salva CSV consolidado
    df.to_csv(OUT_DIR / "comparativo_consolidado.csv", index=False)

    gerados = []
    # gera um gráfico por antecedente real presente na planilha
    presentes = sorted(df["Antecedente"].dropna().unique().tolist(), key=str.lower)

    for ant in presentes:
        # opcional: restringir aos antecedentes válidos conhecidos
        if ANTECEDENTES_VALIDOS and ant not in ANTECEDENTES_VALIDOS:
            continue

        sub = df[df["Antecedente"] == ant].sort_values("AbsDiff", ascending=False).head(TOPN)
        if sub.empty:
            continue
        out_png = OUT_DIR / f"grafico_{ant}.png"
        plot_barras_duplas(sub, f"Top {len(sub)} – Antecedente: {ant}", out_png)
        gerados.append(out_png)

    print("Gráficos gerados:")
    for p in gerados:
        print(" -", p)
    print("CSV consolidado:", OUT_DIR / "comparativo_consolidado.csv")

if __name__ == "__main__":
    main()
