# -*- coding: utf-8 -*-
# Gera, para cada ANTECEDENTE presente no XLSX, um gráfico por VALOR do antecedente,
# comparando "Bases Python" (seu Lift) vs "Referência" (Daricélio).
# Estilo limpo (fundo branco), rótulos, e organização em subpastas.
#
# Requisitos:
#   pip install pandas matplotlib openpyxl

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

# =================== CONFIGURE AQUI ===================
XLSX_PATH = Path("CenarioApenasLifetime.xlsx")
SHEET_NAME = "Planilha1"  # ou 0
OUT_DIR = Path("GraficosGerados_TODOS")
# ======================================================

# Ordem canônica dos consequentes (ajuste se necessário)
CONSEQ_ORDER = ["very short", "short", "medium", "lengthy"]

# Normalização dos consequentes -> very short / short / medium / lengthy
def norm_conseq(c: str):
    s = str(c).strip().lower()
    if "very" in s and "short" in s: return "very short"
    if "short" in s and "very" not in s: return "short"
    if "medium" in s: return "medium"
    if "length" in s or "long" in s: return "lengthy"
    return s

# Normalizações por antecedente e ordem desejada de valores
def norm_lines(v: str):
    s = str(v).strip().lower()
    if "1" in s or s in {"one line","single line","1 line"}: return "1 line"
    if "some" in s or "few" in s:                            return "some lines"
    if "many" in s or "several" in s:                        return "many lines"
    return v

def norm_files(v: str):
    s = str(v).strip().lower()
    if "1" in s or "one" in s:   return "1 file"
    if "some" in s or "few" in s:return "some files"
    if "many" in s or "several" in s: return "many files"
    return v

def norm_commits(v: str):
    s = str(v).strip().lower()
    if "1" in s or "one" in s:     return "1 commit"
    if "some" in s or "few" in s:  return "some commits"
    if "many" in s or "several" in s: return "many commits"
    return v

def norm_bool(v: str):
    s = str(v).strip().lower()
    if s in {"true","yes","sim"}:  return "True"
    if s in {"false","no","não","nao"}: return "False"
    return v

def norm_followers(v: str):
    s = str(v).strip().lower()
    if "no" in s and "follower" in s:  return "no followers"
    if "has" in s or "sim" in s or "true" in s: return "has followers"
    return v

def norm_reqexp(v: str):
    s = str(v).strip().lower()
    if "no" in s: return "no contribution"
    if "some" in s or "few" in s: return "some contributions"
    if "many" in s or "several" in s: return "many contributions"
    return v

def norm_typedev(v: str):
    s = str(v).strip().lower()
    if s.startswith("core"):     return "core"
    if s.startswith("extern"):   return "external"
    return s or "(blank)"


# Mapa de antecedentes conhecidos → (função de normalização, ordem de valores)
ANT_CONFIG = {
    "total_lines_D":                (norm_lines,    ["1 line", "some lines", "many lines"]),
    "changedFiles_D":               (norm_files,    ["1 file", "some files", "many files"]),
    "commitsPull_D":                (norm_commits,  ["1 commit", "some commits", "many commits"]),
    "first_Pull":                   (norm_bool,     ["True", "False"]),
    "coreTeamFollowsRequester":     (norm_bool,     ["True", "False"]),
    "followers_boolean":            (norm_followers,["no followers", "has followers"]),
    "typeDeveloper":                (norm_typedev, ["external", "core"]),
    "requester_experience_project": (norm_reqexp,   ["no contribution", "some contributions", "many contributions"]),
    # Se tiver outros, adicione aqui…
}

def split_antecedente_valor(s: str):
    s = str(s)
    if "=" in s:
        a, v = s.split("=", 1)
        return a.strip(), v.strip()
    # fallback para formatos "ante_valor" (menos comum na sua base)
    if "_" in s:
        a, v = s.split("_", 1)
        return a.strip(), v.replace("_", " ").strip()
    return s.strip(), ""

def carregar_df(xlsx_path: Path, sheet_name=None):
    raw = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    if isinstance(raw, dict):
        for k,v in raw.items():
            if isinstance(v, pd.DataFrame) and len(v)>0:
                raw = v; break
    col_ante = "Antecendente"  # (grafia do arquivo)
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
        "BasesPython": pd.to_numeric(raw["Lift"], errors="coerce"),
        "Referencia":  pd.to_numeric(raw["Daricelio"], errors="coerce"),
    }).dropna(subset=["BasesPython","Referencia"], how="any").reset_index(drop=True)
    return df

def plot_par_barras(x, y1, y2, labels, title, out_png):
    # Estilo limpo
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

    width = 0.35
    plt.figure(figsize=(8.5, 4.5))
    bars1 = plt.bar(x - width/2, y1, width=width, label="Bases Python", color="#4C72B0")
    bars2 = plt.bar(x + width/2, y2, width=width, label="Referência",  color="#8C8C8C")

    # Rótulos numéricos
    for bars in (bars1, bars2):
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x()+bar.get_width()/2, yval+0.02, f"{yval:.2f}",
                     ha="center", va="bottom", fontsize=9, color="#333333")

    plt.xticks(x, labels)
    plt.xlabel("Consequente")
    plt.ylabel("Lift")
    plt.title(title, pad=20)
    plt.legend(frameon=False)
    ymax = max(np.nanmax(y1), np.nanmax(y2))
    plt.ylim(0, ymax*1.2 if np.isfinite(ymax) else 1)
    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.12, right=0.95)
    plt.savefig(out_png, bbox_inches="tight", dpi=300)
    plt.close()

def gerar_todos(df, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    # Normaliza consequentes
    df = df.copy()
    df["ConsCat"] = df["Consequente"].apply(norm_conseq)

    antecedentes = sorted(df["Antecedente"].dropna().unique().tolist(), key=str.lower)
    print("Antecedentes encontrados:", antecedentes)

    for ant in antecedentes:
        sub = df[df["Antecedente"] == ant].copy()
        if sub.empty:
            continue

        # Decide normalização dos VALORES conforme antecedente
        norm_fun, value_order = ANT_CONFIG.get(ant, (lambda x: x, sorted(sub["ValorAnt"].astype(str).unique().tolist())))
        sub["ValCat"] = sub["ValorAnt"].apply(norm_fun)

        # Ordem de consequentes (usa canônica; se não houver, usa únicos)
        conseq_order = CONSEQ_ORDER if sub["ConsCat"].isin(CONSEQ_ORDER).any() else \
                       sorted(sub["ConsCat"].astype(str).unique().tolist())

        # Gera um gráfico por VALOR presente
        values_present = [v for v in value_order if v in sub["ValCat"].unique()]
        if not values_present:
            values_present = sorted(sub["ValCat"].astype(str).unique().tolist())

        ant_dir = out_dir / ant
        ant_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[{ant}] valores: {values_present}")
        for val in values_present:
            g = sub[sub["ValCat"] == val].copy()
            if g.empty:
                continue

            # agrega por consequente (média) — caso haja múltiplas regras por mesma célula
            agg = g.groupby("ConsCat", as_index=False).agg(
                BasesPython=("BasesPython","mean"),
                Referencia=("Referencia","mean")
            )
            # garante ordem no eixo X
            agg["ConsCat"] = pd.Categorical(agg["ConsCat"], categories=conseq_order, ordered=True)
            agg = agg.sort_values("ConsCat")
            xs = np.arange(len(conseq_order))

            fname = f"{ant}__{re.sub(r'[^A-Za-z0-9_]+','_', str(val))}.png"
            out_png = ant_dir / fname
            title = f"{ant.replace('_',' ')} — {val}"
            plot_par_barras(xs, agg["BasesPython"].values, agg["Referencia"].values, conseq_order, title, out_png)
            print(" - Gerado:", out_png)

def main():
    df = carregar_df(XLSX_PATH, SHEET_NAME)
    gerar_todos(df, OUT_DIR)
    print("\nConcluído. Verifique a pasta:", OUT_DIR)

if __name__ == "__main__":
    main()
