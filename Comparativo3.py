# -*- coding: utf-8 -*-
# Gera um gráfico por valor do antecedente (1 line, some lines, many lines)
# Visual limpo, estilo tese (fundo branco, tons suaves, rótulos claros)
# Requisitos: pip install pandas matplotlib openpyxl

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =================== CONFIGURE AQUI ===================
XLSX_PATH = Path("CenarioApenasLifetime.xlsx")
SHEET_NAME = "Planilha1"
OUT_DIR = Path("GraficosGerados_porValor")

ANTECEDENT_KEY = "total_lines_D"
CONSEQ_ORDER = ["very short", "short", "medium", "lengthy"]
# ======================================================

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

def carregar_df(xlsx_path: Path, sheet_name=None):
    raw = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, pd.DataFrame) and len(v) > 0:
                raw = v
                break

    col_ante = "Antecendente"
    col_cons = "Consequente"
    col_lift = "Lift"
    col_dari = "Daricelio"

    ants, vals = [], []
    for s in raw[col_ante]:
        a, v = split_antecedente_valor(s)
        ants.append(a)
        vals.append(v)

    df = pd.DataFrame({
        "Antecedente": ants,
        "ValorAnt": vals,
        "Consequente": raw[col_cons].astype(str),
        "BasesPython": pd.to_numeric(raw[col_lift], errors="coerce"),
        "Referencia": pd.to_numeric(raw[col_dari], errors="coerce"),
    }).dropna(subset=["BasesPython","Referencia"], how="any").reset_index(drop=True)
    return df

def grafico_por_valor(df_ant, valor_normalizado: str, out_png: Path):
    sub = df_ant[df_ant["ValCat"] == valor_normalizado].copy()
    if sub.empty:
        return False

    agg = sub.groupby("ConsCat", as_index=False).agg(
        BasesPython=("BasesPython","mean"),
        Referencia=("Referencia","mean")
    )

    agg["ConsCat"] = pd.Categorical(agg["ConsCat"], categories=CONSEQ_ORDER, ordered=True)
    agg = agg.sort_values("ConsCat")

    # --- Estilo geral ---
    plt.style.use("default")
    plt.rcParams.update({
        "font.family": "Arial",
        "axes.edgecolor": "black",
        "axes.linewidth": 1.0,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.fontsize": 10,
        "figure.facecolor": "white"
    })

    x = np.arange(len(CONSEQ_ORDER))
    width = 0.35

    plt.figure(figsize=(8.5, 4.5))
    bars1 = plt.bar(x - width/2, agg["BasesPython"].values, width=width, label="Bases Python", color="#4C72B0")
    bars2 = plt.bar(x + width/2, agg["Referencia"].values, width=width, label="Referência", color="#8C8C8C")

    # Rótulos com valor
    for bars in [bars1, bars2]:
        for bar in bars:
            yval = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2,
                yval + 0.02,
                f"{yval:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                color="#333333"
            )

    plt.xticks(x, CONSEQ_ORDER)
    plt.xlabel("Consequente")
    plt.ylabel("Lift")
    plt.title(f"{ANTECEDENT_KEY.replace('_',' ')} — {valor_normalizado}", pad=20)
    plt.legend(frameon=False)
    plt.ylim(0, max(agg["BasesPython"].max(), agg["Referencia"].max()) * 1.2)

    # Margens generosas para evitar corte
    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.12, right=0.95)

    plt.savefig(out_png, bbox_inches="tight", dpi=300)
    plt.close()
    return True

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = carregar_df(XLSX_PATH, SHEET_NAME)

    sub = df[df["Antecedente"].str.fullmatch(ANTECEDENT_KEY, case=False, na=False)].copy()
    if sub.empty:
        raise SystemExit(f"Nenhum dado para antecedente '{ANTECEDENT_KEY}'.")

    sub["ValCat"]  = sub["ValorAnt"].apply(norm_value)
    sub["ConsCat"] = sub["Consequente"].apply(norm_conseq)

    values_present = [v for v in ["1 line","some lines","many lines"] if v in sub["ValCat"].unique()]

    print(f"Gerando gráficos para {ANTECEDENT_KEY}: {values_present}")
    for val in values_present:
        out_png = OUT_DIR / f"{ANTECEDENT_KEY}__{val.replace(' ','_')}.png"
        ok = grafico_por_valor(sub, val, out_png)
        if ok:
            print(" - Gerado:", out_png)

if __name__ == "__main__":
    main()
