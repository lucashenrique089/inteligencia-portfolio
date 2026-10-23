"""
MONITOR DE PREÇOS DA CONCORRÊNCIA | versão pública (portfólio)
==============================================================
Painel em Streamlit que compara, pneu a pneu, os preços e o estoque de três e-commerces de pneus
Goodyear e Kelly: Roma Pneus, Pneu Store e Achei Pneus.

Esta é a versão de portfólio. Ela lê a pasta dados/, atualizada pelo coletor.py (todo dia
pelo GitHub Actions, ou no botão da barra lateral), que deixa de fora tudo o que é interno da empresa:
vendas, GA4, Google Ads, a regra de desconto da Roma e a ordem de vendas dos pneus.
As abas de Black Friday e Ideias usam dados FICTÍCIOS, só para demonstrar as funcionalidades.

Como rodar (no terminal, dentro da pasta do projeto):
    python -m streamlit run app.py
"""

import base64
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

PASTA_APP = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_APP, "dados")

LOJAS = ["Roma", "PneuStore", "Achei Pneus"]
NOMES = {"Roma": "Roma Pneus", "PneuStore": "Pneu Store", "Achei Pneus": "Achei Pneus"}
COR_ROMA = "#C40000"
COR_GOODYEAR = "#004EA8"
CORES = {"Roma": COR_ROMA, "PneuStore": "#5B2D90", "Achei Pneus": "#F39200"}
CORES_FICTICIAS = {"Loja Alfa": "#C40000", "Loja Beta": "#5B2D90", "Loja Gama": "#F39200"}
LIMITE = 0.05      # faixa de +-5% para "empate técnico"


# ============================================================
# 1. VISUAL
# ============================================================

def achar_imagem(palavra):
    """Procura a imagem pela palavra no nome (ex.: 'roma') na pasta imagens/."""
    pasta = os.path.join(PASTA_APP, "imagens")
    if os.path.isdir(pasta):
        for nome in sorted(os.listdir(pasta)):
            if palavra in nome.lower() and nome.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
                return os.path.join(pasta, nome)
    return ""


def imagem_base64(caminho):
    """Lê uma imagem e devolve no formato que o HTML entende (para pôr as logos no cabeçalho)."""
    if not caminho or not os.path.exists(caminho):
        return None
    with open(caminho, "rb") as arquivo:
        dados = base64.b64encode(arquivo.read()).decode()
    tipo = {"jpg": "jpeg", "jpeg": "jpeg", "svg": "svg+xml"}.get(caminho.rsplit(".", 1)[-1].lower(), "png")
    return f"data:image/{tipo};base64,{dados}"


LOGO_ROMA = achar_imagem("roma")
SELO_GOODYEAR = achar_imagem("goodyear")

st.set_page_config(page_title="Monitor de Preços da Concorrência | Portfólio", layout="wide",
                   page_icon=LOGO_ROMA or "🛞")

st.markdown(f"""
<style>
h2 {{ color: #1A1A1A !important; font-weight: 800 !important; font-size: 1.35rem !important; }}
h3 {{ color: #1A1A1A !important; font-weight: 800 !important; font-size: 1.12rem !important;
      border-left: 4px solid {COR_ROMA}; padding-left: .55rem !important; margin-top: .6rem; }}
.stMarkdown p, .stMarkdown li {{ color: #1A1A1A; font-size: .95rem; }}
[data-testid="stCaptionContainer"] p {{ color: #5F6368; font-size: .84rem; }}
button[data-baseweb="tab"] p {{ font-size: .93rem; font-weight: 700; color: #1A1A1A; }}
button[data-baseweb="tab"][aria-selected="true"] p {{ color: {COR_ROMA}; }}
[data-testid="stMetric"] {{ background: #FFFFFF; border: 1px solid #E6E8EB; border-top: 3px solid {COR_ROMA};
                           border-radius: 10px; padding: .55rem .8rem .5rem; }}
[data-testid="stMetricLabel"] p {{ color: #3C4043; font-weight: 700; font-size: .8rem;
                                  white-space: normal !important; line-height: 1.15; }}
[data-testid="stMetricValue"] {{ color: #111; font-weight: 800; font-size: 1.45rem !important; line-height: 1.25; }}
[data-testid="stMetricValue"] > div {{ white-space: normal !important; overflow: visible !important; }}
.cartao-multi {{ background: #FFFFFF; border: 1px solid #E6E8EB; border-top: 3px solid {COR_ROMA};
                border-radius: 10px; padding: .55rem .8rem .6rem; height: 100%; }}
.cartao-rotulo {{ color: #3C4043; font-weight: 700; font-size: .8rem; margin-bottom: .25rem; }}
.cartao-valor {{ color: #111; font-weight: 700; font-size: 1.02rem; line-height: 1.45; }}
.cabecalho {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;
             padding: .4rem 0 .9rem; margin-bottom: .6rem; border-bottom: 3px solid {COR_ROMA}; }}
.cab-esq {{ display: flex; align-items: center; gap: 1.1rem; flex-wrap: wrap; }}
.cab-esq img {{ height: 52px; }}
.cab-titulo {{ font-size: 1.55rem; font-weight: 800; color: #1A1A1A; line-height: 1.15; }}
.cab-sub {{ font-size: .88rem; color: #5F6368; margin-top: .15rem; }}
.cab-dir img {{ height: 40px; }}
.selo-ficticio {{ display: inline-block; background: #FFF4D6; color: #7A4B00; border: 1px solid #F2C14E;
                 border-radius: 6px; padding: .2rem .55rem; font-weight: 700; font-size: .82rem; }}
</style>
""", unsafe_allow_html=True)


def cartao_html(coluna, rotulo, linhas):
    """Cartão com várias linhas, no mesmo visual dos números (o texto quebra em vez de sair da caixa)."""
    corpo = "<br>".join(str(l).replace("$", "&#36;") for l in linhas if l) or "—"
    coluna.markdown(f'<div class="cartao-multi"><div class="cartao-rotulo">{rotulo}</div>'
                    f'<div class="cartao-valor">{corpo}</div></div>', unsafe_allow_html=True)


def aviso_ficticio(texto):
    st.markdown(f'<span class="selo-ficticio">🧪 Dados fictícios</span> {texto}', unsafe_allow_html=True)


def formatar_real(valor):
    if pd.isna(valor):
        return "—"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_pct(valor, sinal=True):
    if pd.isna(valor):
        return "—"
    return (f"{valor:+.1%}" if sinal else f"{valor:.1%}").replace(".", ",")


def estilo_grafico(fig, altura):
    fig.update_layout(height=altura, font=dict(size=13, color="#1A1A1A"), plot_bgcolor="white", bargap=0.25,
                      legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, title_text=""),
                      margin=dict(l=10, r=110, t=50, b=40))
    fig.update_yaxes(tickfont=dict(size=13, color="#1A1A1A"), title_text="")
    fig.update_xaxes(tickfont=dict(size=12, color="#1A1A1A"), gridcolor="#E5E5E5")
    fig.update_traces(textfont=dict(size=12, color="#1A1A1A"), cliponaxis=False)
    return fig


# ============================================================
# 2. DADOS (foto real de uma coleta, já sem informações internas)
# ============================================================

def ler(nome):
    caminho = os.path.join(PASTA_DADOS, nome)
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig") if os.path.exists(caminho) else pd.DataFrame()


@st.cache_data
def carregar_tudo(marca_tempo):
    """marca_tempo = data de modificação de dados/precos.csv: muda a cada coleta e faz o cache ler de novo."""
    pneus, precos, hist = ler("pneus.csv"), ler("precos.csv"), ler("historico_precos.csv")
    parcelas, campanhas, hist_camp, promocoes = (ler("parcelas.csv"), ler("campanhas.csv"),
                                                 ler("historico_campanhas.csv"), ler("promocoes.csv"))
    for tabela in (precos, hist, parcelas):
        if not tabela.empty:
            tabela["pneu"] = tabela["medida"] + " " + tabela["modelo"]
    if not hist.empty:
        hist["data_coleta"] = pd.to_datetime(hist["data_coleta"])
    if not pneus.empty:
        pneus["pneu"] = pneus["medida"] + " " + pneus["modelo"]
        pneus["tipo"] = pneus["tipo"].fillna("")
    for col in ["novidade", "imagem", "pneus_monitorados"]:
        if not campanhas.empty and col in campanhas:
            campanhas[col] = campanhas[col].fillna("")
    return pneus, precos, hist, parcelas, campanhas, hist_camp, promocoes


_arquivo_precos = os.path.join(PASTA_DADOS, "precos.csv")
pneus, precos, hist, parcelas, campanhas, hist_camp, promocoes = carregar_tudo(
    os.path.getmtime(_arquivo_precos) if os.path.exists(_arquivo_precos) else 0)

_logo, _selo = imagem_base64(LOGO_ROMA), imagem_base64(SELO_GOODYEAR)
st.markdown(f"""
<div class="cabecalho">
  <div class="cab-esq">
    {f'<img src="{_logo}" alt="Roma Pneus">' if _logo else '<b style="color:#C40000;font-size:2rem">🛞</b>'}
    <div>
      <div class="cab-titulo">Monitor de Preços da Concorrência</div>
      <div class="cab-sub">Roma Pneus x Pneu Store x Achei Pneus · pneus Goodyear e Kelly · Python + Streamlit</div>
    </div>
  </div>
  <div class="cab-dir">{f'<img src="{_selo}" alt="Goodyear">' if _selo else ''}</div>
</div>
""", unsafe_allow_html=True)

if precos.empty:
    st.info("Ainda não há dados na pasta `dados/`. Rode `python preparar_dados.py \"pasta_da_coleta\"`.")
    st.stop()

DATA_FOTO = pd.to_datetime(precos["data_coleta"].iloc[0])
st.info(f"📡 **Versão de portfólio.** Preços reais e públicos, coletados automaticamente nos sites das lojas. "
        f"Última coleta: **{DATA_FOTO.strftime('%d/%m/%Y às %H:%M')}**. Dados internos da empresa, como vendas, "
        "tráfego do site e política comercial, foram omitidos. As abas de Black Friday e Ideias usam dados fictícios.")


# ============================================================
# 3. BARRA LATERAL
# ============================================================

if LOGO_ROMA:
    st.sidebar.image(LOGO_ROMA, width="stretch")
st.sidebar.markdown(f"**Última coleta:** {DATA_FOTO.strftime('%d/%m/%Y %H:%M')}")
st.sidebar.markdown(f"**Pneus monitorados:** {pneus['item'].nunique()}")


def senha_da_coleta():
    """Senha guardada nos Secrets do Streamlit Cloud (nunca no código). Sem senha, o botão não aparece."""
    try:
        return st.secrets.get("senha_coleta")
    except Exception:
        return None


# Botão de coleta em tempo real: só para o dono do painel (quem visita só vê os dados).
# Assim ninguém dispara coletas em sequência nos sites das lojas.
if senha_da_coleta():
    with st.sidebar.expander("🔄 Atualizar agora (administrador)"):
        senha = st.text_input("Senha", type="password", key="senha_coleta")
        if st.button("Coletar preços agora", width="stretch"):
            if senha != senha_da_coleta():
                st.error("Senha incorreta.")
            else:
                from atualizar_publico import atualizar
                with st.spinner("Coletando nas três lojas (leva de 10 a 15 minutos)..."):
                    atualizar()
                st.cache_data.clear()
                st.rerun()
st.sidebar.header("Filtros")
concorrentes = st.sidebar.multiselect("Concorrente", ["PneuStore", "Achei Pneus"],
                                      default=["PneuStore", "Achei Pneus"], format_func=lambda l: NOMES[l])
tipos = sorted(t for t in pneus["tipo"].unique() if t)
tipos_f = st.sidebar.multiselect("Tipo de pneu", tipos, default=tipos)
incluir_alternativos = st.sidebar.checkbox(
    "Incluir produto alternativo", value=False,
    help="Quando o concorrente não vende o mesmo pneu, o coletor compara com o modelo equivalente "
         "(ex.: Cargo Marathon 3 no lugar do Cargo Marathon 2). Fica fora das médias por padrão.")
st.sidebar.divider()
st.sidebar.caption("Projeto de portfólio de Lucas Henrique · Python, pandas, Plotly e Streamlit.")

if not concorrentes:
    st.warning("Selecione ao menos um concorrente.")
    st.stop()

itens_f = set(pneus.loc[pneus["tipo"].isin(tipos_f) | (pneus["tipo"] == ""), "item"])
base = precos[precos["concorrente"].isin(concorrentes) & precos["item"].isin(itens_f)].copy()
if not incluir_alternativos:
    alt = base["equivalencia"] == "alternativo"
    for col in ["conc_preco_cheio", "conc_preco_pix", "conc_preco_parcelado", "conc_valor_parcela"]:
        base.loc[alt, col] = float("nan")
    base.loc[alt, "conc_disponivel"] = "alternativo"

# Diferença da Roma no PREÇO CHEIO (o preço de vitrine, sem descontos), contra cada concorrente
base["dif_cheio_pct"] = base["roma_preco_cheio"] / base["conc_preco_cheio"] - 1


def estoque_texto(disponivel, qtd=None):
    if disponivel == "sim":
        return f"Em estoque ({int(qtd)} un.)" if qtd is not None and pd.notna(qtd) and qtd > 0 else "Em estoque"
    return {"nao": "Sem estoque", "nao_vende": "Não vende", "alternativo": "Produto diferente",
            "fora_do_site": "Fora do site"}.get(disponivel, "Não coletado")


def situacao(dif):
    if pd.isna(dif):
        return "Sem comparação"
    return "Roma mais barata" if dif < -0.005 else "Empate" if dif <= 0.005 else "Roma mais cara"


def visao_por_item(dados):
    """Uma linha por pneu, com Roma e cada concorrente lado a lado."""
    linhas = []
    for item, d in dados.groupby("item"):
        l0 = d.iloc[0]
        linha = {"item": item, "Pneu": l0["pneu"], "Tipo": pneus.set_index("item")["tipo"].get(item, ""),
                 "Roma preço cheio": l0["roma_preco_cheio"],
                 "Roma estoque": estoque_texto(l0["roma_disponivel"])}
        for loja in concorrentes:
            c = d[d["concorrente"] == loja]
            if c.empty:
                continue
            c = c.iloc[0]
            nome = NOMES[loja]
            linha[f"{nome} preço cheio"] = c["conc_preco_cheio"]
            linha[f"{nome} PIX"] = c["conc_preco_pix"]
            linha[f"{nome} parcela"] = (f"{int(c['conc_n_parcelas'])}x de {formatar_real(c['conc_valor_parcela'])}"
                                       if pd.notna(c["conc_n_parcelas"]) and pd.notna(c["conc_valor_parcela"]) else "—")
            linha[f"{nome} estoque"] = estoque_texto(c["conc_disponivel"], c.get("conc_estoque_qtd"))
        cheios = d["conc_preco_cheio"].dropna()
        linha["Menor concorrente (cheio)"] = cheios.min() if not cheios.empty else float("nan")
        roma = l0["roma_preco_cheio"]
        linha["Roma x menor"] = (roma / linha["Menor concorrente (cheio)"] - 1
                                 if pd.notna(roma) and pd.notna(linha["Menor concorrente (cheio)"]) else float("nan"))
        linha["Situação"] = situacao(linha["Roma x menor"])
        linhas.append(linha)
    return pd.DataFrame(linhas)


visao = visao_por_item(base)

(aba_inicio, aba_comparar, aba_todos, aba_parcelas, aba_hist, aba_promo, aba_camp, aba_bf, aba_ideias,
 aba_sobre) = st.tabs(["🏠 Início", "⚖️ Comparativo", "📋 Todos os pneus", "💳 Parcelamento", "📈 Histórico",
                       "📣 Promoções", "📢 Campanhas", "🖤 Black Friday", "💡 Ideias", "🛠️ Sobre o projeto"])


# ============================================================
# 4. INÍCIO
# ============================================================

with aba_inicio:
    st.markdown("**Um painel de inteligência competitiva para e-commerce.** Um robô em Python visita três lojas "
                "on-line, lê preço, estoque e parcelamento de cada pneu e organiza tudo aqui, para responder "
                "rápido: *estamos mais caros ou mais baratos? Quem está sem estoque? Quem lançou promoção?*")

    comp = visao[visao["Roma x menor"].notna()]
    k = st.columns(4)
    k[0].metric("Pneus monitorados", len(visao))
    k[1].metric("Roma mais barata no preço cheio", f"{(comp['Situação'] == 'Roma mais barata').sum()} de {len(comp)}",
                help="Preço de vitrine da Roma (sem descontos) contra o menor preço cheio dos concorrentes.")
    k[2].metric("Concorrente sem estoque", base.loc[base["conc_disponivel"] == "nao", "item"].nunique(),
                help="Pneus que estão em falta em pelo menos um concorrente: oportunidade de venda.")
    desc = base.groupby("concorrente")["conc_desconto_pix_pct"].mean()
    cartao_html(k[3], "Desconto médio no PIX (concorrentes)",
                [f"<b>{NOMES[l]}:</b> {formatar_pct(v, sinal=False)}" for l, v in desc.items() if pd.notna(v)])

    st.subheader("🔍 Consultar um pneu")
    rotulos = dict(zip(visao["item"], visao["Pneu"]))
    item_sel = st.selectbox("Escolha o pneu (digite a medida para buscar)", list(rotulos),
                            format_func=lambda i: rotulos[i], key="inicio_pneu")
    v = visao[visao["item"] == item_sel].iloc[0]
    links = pneus.set_index("item").loc[item_sel]

    def link(url):
        return f'<a href="{url}" target="_blank">Ver no site ↗</a>' if isinstance(url, str) and url.startswith("http") else ""

    colunas = st.columns(1 + len(concorrentes))
    cartao_html(colunas[0], "Roma Pneus", [f"<b>Preço cheio:</b> {formatar_real(v['Roma preço cheio'])}",
                                           f"<b>Estoque:</b> {v['Roma estoque']}", link(links.get("url_roma"))])
    urls = {"PneuStore": links.get("url_pneustore"), "Achei Pneus": links.get("url_acheipneus")}
    for coluna, loja in zip(colunas[1:], concorrentes):
        nome = NOMES[loja]
        if f"{nome} preço cheio" in v:
            cartao_html(coluna, nome, [f"<b>Preço cheio:</b> {formatar_real(v[f'{nome} preço cheio'])}",
                                       f"<b>PIX:</b> {formatar_real(v[f'{nome} PIX'])}",
                                       f"<b>Cartão:</b> {v[f'{nome} parcela']}",
                                       f"<b>Estoque:</b> {v[f'{nome} estoque']}", link(urls[loja])])
    if v["Situação"] == "Roma mais barata":
        st.success(f"No preço cheio, a Roma está **{formatar_pct(v['Roma x menor'])}** em relação ao menor concorrente.")
    elif v["Situação"] == "Empate":
        st.info("No preço cheio, a Roma está **empatada** com o menor concorrente.")
    elif v["Situação"] == "Roma mais cara":
        st.error(f"No preço cheio, a Roma está **{formatar_pct(v['Roma x menor'])}** acima do menor concorrente.")
    else:
        st.info("Sem comparação neste pneu: falta o preço da Roma (fora do site) ou dos concorrentes.")

    st.subheader("🧭 O que tem em cada aba")
    st.markdown("""
- **⚖️ Comparativo:** gráfico e tabela de preços lado a lado, com o menor preço em destaque.
- **📋 Todos os pneus:** a tabela completa, com filtros e download em planilha.
- **💳 Parcelamento:** quanto o cliente paga de 1x a 12x nos concorrentes.
- **📈 Histórico**, **📣 Promoções** e **📢 Campanhas:** o que mudou nos concorrentes entre as coletas.
- **🖤 Black Friday** e **💡 Ideias:** demonstração das análises com dados fictícios.
- **🛠️ Sobre o projeto:** o problema, a solução, a arquitetura e as ferramentas.
""")


# ============================================================
# 5. COMPARATIVO
# ============================================================

with aba_comparar:
    st.markdown("**Preço cheio (vitrine, sem descontos) nas três lojas.** Para os concorrentes, o PIX aparece "
                "como referência na tabela.")
    vis = st.radio("Visualização", ["Preço (R$)", "Diferença da Roma (%)"], horizontal=True, key="vis_comp")
    ordem = visao.sort_values("item")["Pneu"].tolist()
    n_graf = st.slider("Quantos pneus mostrar no gráfico", 5, max(5, len(ordem)), min(15, len(ordem)), key="n_graf")
    mostrar = ordem[:n_graf]

    if vis == "Preço (R$)":
        roma = base.groupby(["item", "pneu"], as_index=False).agg(preco=("roma_preco_cheio", "first"))
        roma["loja"] = "Roma"
        conc = base[["item", "pneu", "concorrente", "conc_preco_cheio"]].rename(
            columns={"concorrente": "loja", "conc_preco_cheio": "preco"})
        longa = pd.concat([roma, conc], ignore_index=True)
        longa = longa[longa["pneu"].isin(mostrar)]
        longa["rotulo"] = longa["preco"].map(formatar_real)
        fig = px.bar(longa, x="preco", y="pneu", color="loja", barmode="group", orientation="h", text="rotulo",
                     color_discrete_map=CORES, category_orders={"pneu": mostrar, "loja": LOJAS},
                     labels={"preco": "Preço cheio (R$)", "loja": "Loja"})
        fig.update_traces(texttemplate="<b>%{text}</b>", textposition="outside")
        fig.update_xaxes(tickprefix="R$ ", separatethousands=True)
        st.plotly_chart(estilo_grafico(fig, max(420, 85 * len(mostrar))), width="stretch", key="g_preco")
    else:
        g = base[base["dif_cheio_pct"].notna() & base["pneu"].isin(mostrar)].copy()
        g["rotulo"] = g["dif_cheio_pct"].map(formatar_pct)
        fig = px.bar(g, x="dif_cheio_pct", y="pneu", color="concorrente", barmode="group", orientation="h",
                     text="rotulo", color_discrete_map=CORES, category_orders={"pneu": mostrar},
                     labels={"dif_cheio_pct": "Diferença da Roma no preço cheio", "concorrente": "Concorrente"})
        fig.update_traces(texttemplate="<b>%{text}</b>", textposition="outside")
        fig.add_vline(x=0, line_width=2, line_color="#111")
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(estilo_grafico(fig, max(420, 65 * len(mostrar))), width="stretch", key="g_dif")
        st.caption("À esquerda da linha preta: Roma mais barata. À direita: Roma mais cara.")

    ranking = base[base["dif_cheio_pct"].notna()].groupby("pneu")["dif_cheio_pct"].mean().sort_values()
    if not ranking.empty:
        a, b = st.columns(2)
        a.success(f"**Maior vantagem da Roma:** {ranking.index[0]} (**{formatar_pct(ranking.iloc[0])}**)")
        b.error(f"**Maior desvantagem da Roma:** {ranking.index[-1]} (**{formatar_pct(ranking.iloc[-1])}**)")

    st.subheader("Tabela de preço cheio")
    tabela = pd.DataFrame({"Pneu": visao["Pneu"], "Roma": visao["Roma preço cheio"]})
    for loja in concorrentes:
        if f"{NOMES[loja]} preço cheio" in visao:
            tabela[NOMES[loja]] = visao[f"{NOMES[loja]} preço cheio"]
    numeros = tabela.drop(columns="Pneu").astype(float)
    texto = tabela.copy()
    for c in numeros.columns:
        texto[c] = numeros[c].map(formatar_real)
    texto["Roma x menor"] = visao["Roma x menor"].map(formatar_pct)

    def destacar(_):
        css = pd.DataFrame("color: #111;", index=texto.index, columns=texto.columns)
        css["Pneu"] = "font-weight: 700; color: #000;"
        menor = numeros.min(axis=1)
        for c in numeros.columns:
            css.loc[numeros[c].notna() & (numeros[c] == menor), c] = \
                "background-color: #DFF3E4; color: #0B5D23; font-weight: 800;"
        css.loc[texto["Roma x menor"].str.startswith("-"), "Roma x menor"] = "color: #0B5D23; font-weight: 800;"
        css.loc[texto["Roma x menor"].str.startswith("+"), "Roma x menor"] = "color: #B00020; font-weight: 800;"
        return css

    st.dataframe(texto.style.apply(destacar, axis=None), hide_index=True, width="stretch",
                 height=min(38 * (len(texto) + 1) + 4, 620))
    st.caption("Em verde, o menor preço cheio de cada pneu. 'Roma x menor' compara com o menor concorrente "
               "(negativo = Roma mais barata).")


# ============================================================
# 6. TODOS OS PNEUS
# ============================================================

with aba_todos:
    st.markdown("**Todos os pneus monitorados, com preço, parcela e estoque de cada loja.**")
    f1, f2 = st.columns([1, 1.3])
    situacoes = ["Roma mais barata", "Empate", "Roma mais cara", "Sem comparação"]
    sit_f = f1.multiselect("Situação no preço cheio", situacoes, default=situacoes, key="todos_sit")
    busca = f2.text_input("Buscar (medida ou modelo)", key="todos_busca")
    t = visao[visao["Situação"].isin(sit_f)]
    if busca:
        t = t[t["Pneu"].str.contains(busca.strip(), case=False, regex=False)]
    tab = t.drop(columns=["item"]).copy()
    for c in [c for c in tab.columns if "preço cheio" in c or c.endswith("PIX") or "(cheio)" in c]:
        tab[c] = tab[c].map(formatar_real)
    tab["Roma x menor"] = tab["Roma x menor"].map(formatar_pct)

    def cores_todos(_):
        css = pd.DataFrame("", index=tab.index, columns=tab.columns)
        css["Pneu"] = "font-weight: 700; color: #000;"
        css.loc[tab["Situação"] == "Roma mais barata", ["Situação", "Roma x menor"]] = "color: #0B5D23; font-weight: 800;"
        css.loc[tab["Situação"] == "Roma mais cara", ["Situação", "Roma x menor"]] = "color: #B00020; font-weight: 800;"
        for c in [c for c in tab.columns if c.endswith("estoque")]:
            css.loc[tab[c].isin(["Sem estoque", "Não vende"]), c] = "color: #B00020;"
        return css

    st.dataframe(tab.style.apply(cores_todos, axis=None), hide_index=True, width="stretch",
                 height=min(38 * (len(tab) + 1) + 4, 760))
    st.caption(f"{len(t)} de {len(visao)} pneus. 'Fora do site' = pneu que a Roma vende, mas ainda não está "
               "na loja on-line. Estoque com número = unidades informadas pelo site.")
    st.download_button("⬇️ Baixar esta tabela (CSV para Excel)",
                       t.drop(columns=["item"]).to_csv(sep=";", index=False, decimal=",").encode("utf-8-sig"),
                       file_name="pneus_monitorados.csv", mime="text/csv")


# ============================================================
# 7. PARCELAMENTO (concorrentes)
# ============================================================

with aba_parcelas:
    st.markdown("**Quanto o cliente paga nos concorrentes, de 1x a 12x no cartão.**")
    st.caption("Os concorrentes usam desconto progressivo: quanto menos parcelas, maior o desconto. "
               "A tabela vem do site ou, quando o site não responde, da fórmula do desconto progressivo.")
    tab_p = parcelas[parcelas["loja"].isin(concorrentes) & parcelas["item"].isin(itens_f)] if not parcelas.empty else parcelas
    if tab_p.empty:
        st.info("Sem tabela de parcelas nesta foto.")
    else:
        s1, s2 = st.columns([2, 1])
        n = s1.select_slider("Número de parcelas", options=list(range(1, 13)), value=10, key="n_parc")
        qtd = s2.radio("Quantidade de pneus", [1, 2, 4], horizontal=True, key="qtd_pneus")
        tab_p = tab_p.assign(total=tab_p["total"] * qtd, valor_parcela=tab_p["valor_parcela"] * qtd)
        escolha = tab_p[tab_p["parcelas"] == n]
        ordem_p = tab_p.sort_values("item")["pneu"].unique().tolist()
        lojas_p = [l for l in LOJAS if l in escolha["loja"].unique()]
        media = escolha.groupby("loja")["valor_parcela"].mean()
        m = st.columns(len(lojas_p) or 1)
        for coluna, loja in zip(m, lojas_p):
            coluna.metric(f"Parcela média · {NOMES[loja]} ({n}x)", formatar_real(media.get(loja)))

        totais = escolha.pivot_table(index="pneu", columns="loja", values="total", aggfunc="first").reindex(
            index=ordem_p, columns=lojas_p)
        parcs = escolha.pivot_table(index="pneu", columns="loja", values="valor_parcela", aggfunc="first").reindex(
            index=ordem_p, columns=lojas_p)
        juros = escolha.pivot_table(index="pneu", columns="loja", values="juros", aggfunc="first").reindex(
            index=ordem_p, columns=lojas_p)
        tabela_p = pd.DataFrame({"Pneu": ordem_p})
        for loja in lojas_p:
            tabela_p[NOMES[loja]] = [
                "—" if pd.isna(totais.at[p, loja]) else
                f"{formatar_real(totais.at[p, loja])} ({n}x de {formatar_real(parcs.at[p, loja])})"
                + (" · com juros" if juros.at[p, loja] in (True, "True") else "") for p in ordem_p]
        st.subheader(f"Comparativo em {n}x · {qtd} pneu{'s' if qtd > 1 else ''}")
        st.dataframe(tabela_p, hide_index=True, width="stretch", height=min(38 * (len(tabela_p) + 1) + 4, 620))

        st.subheader("📈 Total a pagar de 1x a 12x")
        pneu_p = st.selectbox("Pneu", ordem_p, key="pneu_curva")
        curva = tab_p[tab_p["pneu"] == pneu_p]
        fig = px.line(curva, x="parcelas", y="total", color="loja", markers=True, color_discrete_map=CORES,
                      labels={"parcelas": "Número de parcelas", "total": "Total a pagar (R$)", "loja": "Loja"})
        fig.update_traces(line=dict(width=3), marker=dict(size=9))
        fig.add_vline(x=n, line_dash="dot", line_color="#555")
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(tickprefix="R$ ", separatethousands=True)
        st.plotly_chart(estilo_grafico(fig, 420), width="stretch", key="g_curva")


# ============================================================
# 8. HISTÓRICO
# ============================================================

with aba_hist:
    h = hist[hist["concorrente"].isin(concorrentes) & hist["item"].isin(itens_f)] if not hist.empty else hist
    if h.empty or h["data_coleta"].nunique() < 2:
        st.info("O histórico aparece quando a foto tem duas coletas ou mais.")
    else:
        st.markdown(f"**Evolução do preço cheio em {h['data_coleta'].nunique()} coletas.**")
        h1, h2 = st.columns(2)
        pneu_h = h1.selectbox("Pneu", h.sort_values("item")["pneu"].unique().tolist(), key="pneu_hist")
        meio = h2.radio("Preço dos concorrentes", ["Preço cheio", "PIX"], horizontal=True, key="meio_hist")
        hh = h[h["pneu"] == pneu_h]
        col = "conc_preco_cheio" if meio == "Preço cheio" else "conc_preco_pix"
        serie = pd.concat([
            hh.groupby("data_coleta", as_index=False)["roma_preco_cheio"].first()
              .rename(columns={"roma_preco_cheio": "preco"}).assign(loja="Roma (preço cheio)"),
            hh[["data_coleta", "concorrente", col]].rename(columns={"concorrente": "loja", col: "preco"})])
        fig = px.line(serie, x="data_coleta", y="preco", color="loja", markers=True,
                      color_discrete_map={**CORES, "Roma (preço cheio)": COR_ROMA},
                      labels={"data_coleta": "Coleta", "preco": "R$", "loja": ""})
        fig.update_traces(line=dict(width=3), marker=dict(size=9))
        fig.update_yaxes(tickprefix="R$ ")
        st.plotly_chart(estilo_grafico(fig, 440), width="stretch", key="g_hist")
        st.caption("Pontos faltando = sem estoque ou sem preço naquela coleta.")


# ============================================================
# 9. PROMOÇÕES
# ============================================================

with aba_promo:
    st.markdown("**Sinais de promoção detectados automaticamente nos concorrentes.**")
    st.caption("A cada coleta, o robô compara o desconto de cada pneu com o desconto normal da loja e os preços "
               "de hoje com os da coleta anterior: baixou, subiu, mudou o parcelamento, esgotou ou voltou.")
    # Desconto acima do normal na foto atual (mediana do desconto de cada loja + 3 pontos)
    com = base[base["conc_desconto_pix_pct"].notna()]
    normal = com.groupby("concorrente")["conc_desconto_pix_pct"].median()
    extra = com[com["conc_desconto_pix_pct"] > com["concorrente"].map(normal) + 0.03]
    p = promocoes[promocoes["concorrente"].isin(concorrentes)] if not promocoes.empty else promocoes
    c1, c2, c3 = st.columns(3)
    c1.metric("Descontos acima do normal (foto atual)", len(extra))
    c2.metric("Sinais registrados no histórico", len(p))
    c3.metric("Esgotaram em algum momento", int(p["sinal"].str.contains("sem estoque").sum()) if not p.empty else 0)
    if not extra.empty:
        st.subheader("🏷️ Desconto acima do normal")
        st.dataframe(pd.DataFrame({
            "Concorrente": extra["concorrente"].map(NOMES), "Pneu": extra["pneu"],
            "Desconto no PIX": extra["conc_desconto_pix_pct"].map(lambda x: formatar_pct(x, False)),
            "Normal da loja": extra["concorrente"].map(normal).map(lambda x: formatar_pct(x, False))}),
            hide_index=True, width="stretch")
    st.subheader("🗂️ Histórico de sinais")
    if p.empty:
        st.markdown("Nenhum sinal registrado nesta foto.")
    else:
        p = p.sort_values("data_coleta", ascending=False)
        st.dataframe(p[["data_coleta", "concorrente", "pneu", "sinal", "detalhe"]].rename(columns={
            "data_coleta": "Coleta", "concorrente": "Concorrente", "pneu": "Pneu", "sinal": "Sinal",
            "detalhe": "Detalhe"}), hide_index=True, width="stretch")


# ============================================================
# 10. CAMPANHAS
# ============================================================

with aba_camp:
    st.markdown("**Banners e campanhas que os concorrentes estavam divulgando na data da coleta.**")
    camp = campanhas[campanhas["concorrente"].isin(concorrentes)] if not campanhas.empty else campanhas
    if camp.empty:
        st.info("Sem campanhas nesta foto.")
    else:
        ativas = camp[camp["status"] == "ativa"]
        r = st.columns(3)
        r[0].metric("Campanhas ativas", len(ativas))
        r[1].metric("Tipos diferentes", ativas["tipo"].nunique())
        r[2].metric("Black Friday detectada", "Sim" if (ativas["tipo"] == "Black Friday").any() else "Não")
        st.subheader("🔥 As campanhas mais fortes")
        fortes = ativas[ativas["tipo"] != "Institucional / marca"].sort_values("forca", ascending=False).head(6)
        cols = st.columns(3)
        for i, (_, c) in enumerate(fortes.iterrows()):
            with cols[i % 3], st.container(border=True):
                if isinstance(c["imagem"], str) and c["imagem"].startswith("http"):
                    st.image(c["imagem"], width="stretch")
                st.markdown(f"**{c['titulo']}**")
                st.caption(f"{NOMES.get(c['concorrente'], c['concorrente'])} · {c['tipo']}")
                if isinstance(c["link"], str) and c["link"].startswith("http"):
                    st.markdown(f"[Abrir página da campanha]({c['link']})")
        por_tipo = ativas.groupby(["tipo", "concorrente"]).size().reset_index(name="campanhas")
        if not por_tipo.empty:
            st.subheader("📊 O que cada concorrente está usando")
            fig = px.bar(por_tipo, x="campanhas", y="tipo", color="concorrente", orientation="h", barmode="group",
                         text="campanhas", color_discrete_map=CORES,
                         labels={"campanhas": "Nº de campanhas", "tipo": " ", "concorrente": "Concorrente"})
            fig.update_traces(texttemplate="<b>%{text}</b>", textposition="outside")
            st.plotly_chart(estilo_grafico(fig, max(320, 55 * por_tipo["tipo"].nunique())), width="stretch",
                            key="g_camp")


# ============================================================
# 11. BLACK FRIDAY (cenário fictício)
# ============================================================

def proxima_black_friday(hoje=None):
    """Black Friday = sexta-feira seguinte à quarta quinta-feira de novembro."""
    hoje = hoje or date.today()

    def bf(ano):
        d = date(ano, 11, 1)
        while d.weekday() != 3:
            d += timedelta(days=1)
        return d + timedelta(days=22)
    return bf(hoje.year) if bf(hoje.year) >= hoje - timedelta(days=3) else bf(hoje.year + 1)


@st.cache_data
def cenario_black_friday(semente=7):
    """Gera 60 dias de preços FICTÍCIOS para três lojas inventadas, com os comportamentos que o
    painel sabe detectar: loja que sobe o preço antes de anunciar desconto ('preço maquiado'),
    loja que baixa aos poucos e loja que só reage na semana da Black Friday."""
    rng = np.random.default_rng(semente)
    bf = proxima_black_friday()
    dias = pd.date_range(bf - timedelta(days=59), bf)
    linhas = []
    perfis = {"Loja Alfa": lambda d: 100 - 0.08 * d - (6 if d >= 55 else 0),            # baixa aos poucos
              "Loja Beta": lambda d: 100 + (7 if 30 <= d < 55 else 0) - (14 if d >= 55 else 0),  # maquiado
              "Loja Gama": lambda d: 100 - (9 if d >= 57 else 0)}                       # reage no fim
    for loja, perfil in perfis.items():
        for i, dia in enumerate(dias):
            linhas.append({"data": dia, "loja": loja, "indice": round(perfil(i) + rng.normal(0, 0.6), 1)})
    precos_f = pd.DataFrame(linhas)
    lancamentos = pd.DataFrame([
        {"loja": "Loja Beta", "campanha": "Esquenta Black (até 30% OFF)", "inicio": bf - timedelta(days=21)},
        {"loja": "Loja Alfa", "campanha": "Black Week de Pneus", "inicio": bf - timedelta(days=7)},
        {"loja": "Loja Gama", "campanha": "Black Friday · frete grátis", "inicio": bf - timedelta(days=2)}])
    maquiados = pd.DataFrame([
        {"Loja": "Loja Beta", "Pneu": "Pneu exemplo 185/65R15", "Menor preço em 30 dias": 389.90,
         "Preço antes do anúncio": 429.90, "Anunciado na Black Friday": 379.90},
        {"Loja": "Loja Beta", "Pneu": "Pneu exemplo 205/55R16", "Menor preço em 30 dias": 459.90,
         "Preço antes do anúncio": 499.90, "Anunciado na Black Friday": 449.90}])
    return bf, precos_f, lancamentos, maquiados


with aba_bf:
    aviso_ficticio("Cenário inventado com três lojas fictícias, para mostrar o que o painel acompanha "
                   "na Black Friday. Não representa nenhuma empresa real.")
    bf, precos_f, lanc, maq = cenario_black_friday()
    dias_bf = (bf - date.today()).days
    k = st.columns(4)
    k[0].metric("Dias para a Black Friday", max(dias_bf, 0), help=f"Black Friday em {bf.strftime('%d/%m/%Y')}")
    k[1].metric("Campanhas lançadas", len(lanc))
    k[2].metric("Possíveis preços maquiados", len(maq))
    ultimo = precos_f[precos_f["data"] == precos_f["data"].max()].set_index("loja")["indice"]
    k[3].metric("Maior queda no período", f"{ultimo.idxmin()} ({ultimo.min() - 100:+.0f}%)".replace(".", ","))

    st.subheader("📉 Índice de preços até a Black Friday")
    fig = px.line(precos_f, x="data", y="indice", color="loja", color_discrete_map=CORES_FICTICIAS,
                  labels={"data": "", "indice": "Índice de preço (1º dia = 100)", "loja": ""})
    fig.add_hline(y=100, line_dash="dot", line_color="#555")
    fig.update_traces(line=dict(width=3))
    st.plotly_chart(estilo_grafico(fig, 420), width="stretch", key="g_bf")
    st.caption("A Loja Beta sobe o preço um mês antes e depois anuncia o desconto: o padrão de preço maquiado. "
               "Acima de 100 = mais caro do que no início do período.")

    st.subheader("⚠️ Alerta de preço maquiado")
    st.dataframe(maq.style.format({c: formatar_real for c in maq.columns if c not in ("Loja", "Pneu")}),
                 hide_index=True, width="stretch")
    st.caption("Regra do alerta: preço atual 3% ou mais acima do menor preço dos últimos 30 dias.")

    st.subheader("🗓️ Quando cada loja começou a falar de Black Friday")
    for _, l in lanc.iterrows():
        st.markdown(f"- **{l['loja']}** · {l['campanha']} · a partir de {l['inicio'].strftime('%d/%m')} "
                    f"({(bf - l['inicio']).days} dias antes)")

    st.subheader("🗓️ Exemplo de plano até a Black Friday")
    for dias_antes, fase, acao in [
            (45, "Planejamento", "Escolher os pneus da campanha e negociar estoque com o fornecedor."),
            (30, "Lista de espera", "Abrir cadastro de interesse por e-mail e aquecer a base."),
            (15, "Esquenta", "Primeiras ofertas para a base e banner com contagem regressiva."),
            (7, "Semana Black", "Ofertas diárias e monitoramento dos concorrentes duas vezes por dia."),
            (0, "Black Friday", "Ofertas principais e ajuste rápido de preço com base no painel.")]:
        st.markdown(f"**{fase}** · a partir de {(bf - timedelta(days=dias_antes)).strftime('%d/%m')}: {acao}")


# ============================================================
# 12. IDEIAS (exemplos fictícios)
# ============================================================

IDEIAS_EXEMPLO = [
    ("Alta", "Preço", "Revisar o preço dos pneus em que a loja está mais cara",
     "Em 8 pneus (exemplo), o preço está mais de 5% acima do menor concorrente.",
     "Avaliar ajuste pontual só nessas medidas, respeitando a margem mínima."),
    ("Alta", "Estoque", "Aproveitar a falta de estoque do concorrente",
     "Em 5 pneus (exemplo), um concorrente ficou sem estoque e a loja tem o produto.",
     "Reforçar anúncios dessas medidas enquanto durar a falta."),
    ("Média", "Parcelamento", "Comunicar o total parcelado, não só a parcela",
     "Concorrentes parcelam em 12x: a parcela parece menor, mesmo quando o total é maior.",
     "Mostrar na página do produto o total pago em cada opção de parcelamento."),
    ("Média", "Kit 2/4 pneus", "Destacar o preço do jogo de 4 pneus",
     "O cliente de pneu costuma comprar 2 ou 4 de uma vez.",
     "Exibir a economia total do kit nas medidas em que a loja é competitiva."),
    ("Baixa", "Campanhas", "Responder a campanhas de frete grátis",
     "Um concorrente mantém uma categoria de frete grátis ativa (exemplo).",
     "Testar frete grátis em um recorte pequeno, com prazo e meta de vendas."),
]

BIBLIOTECA = [
    {"titulo": "Frete grátis em campanha específica",
     "como": "Frete grátis só para um recorte: categoria, kit, região ou período.",
     "piloto": "Frete grátis só para o kit de 4 pneus das medidas principais, por 15 dias.",
     "medir": "Vendas de kits durante o teste x mesmo período anterior."},
    {"titulo": "Retirada grátis na loja em destaque",
     "como": "Transformar a retirada na loja física em argumento de venda.",
     "piloto": "Selo de retirada grátis na página dos pneus monitorados por 30 dias.",
     "medir": "Conversão das páginas com selo x antes."},
    {"titulo": "Condição especial para o jogo de 4",
     "como": "Benefício extra quando o cliente leva 4 pneus.",
     "piloto": "Parcelamento maior só para pedidos de 4 pneus, por 30 dias.",
     "medir": "Participação de pedidos com 4 pneus e ticket médio."},
    {"titulo": "Montagem ou alinhamento grátis",
     "como": "Serviço incluso na compra, em loja própria ou oficina parceira.",
     "piloto": "Alinhamento grátis na compra de 4 pneus com retirada na loja, por 30 dias.",
     "medir": "Vendas de kits com retirada e avaliação do cliente."},
    {"titulo": "Recuperação de carrinho abandonado",
     "como": "E-mail automático para quem colocou o pneu no carrinho e não comprou.",
     "piloto": "Lembrete 24 horas depois, com prazo curto para decidir.",
     "medir": "Taxa de recuperação de carrinhos antes x depois."},
]

with aba_ideias:
    aviso_ficticio("Exemplos de como o painel transforma os dados em sugestões de ação. Os números são ilustrativos.")
    st.markdown("**Na versão interna, estas sugestões são geradas automaticamente a cada coleta, a partir de regras "
                "sobre preço, estoque, parcelamento e campanhas dos concorrentes.**")
    i = st.columns(3)
    for coluna, prio in zip(i, ["Alta", "Média", "Baixa"]):
        coluna.metric(f"Prioridade {prio.lower()}", sum(1 for x in IDEIAS_EXEMPLO if x[0] == prio))
    icones = {"Alta": "🔴", "Média": "🟠", "Baixa": "🟢"}
    for prio, alavanca, titulo, motivo, acao in IDEIAS_EXEMPLO:
        with st.container(border=True):
            st.markdown(f"#### {icones[prio]} {titulo}")
            st.markdown(f"**Prioridade:** {prio} · **Alavanca:** {alavanca}")
            st.markdown(f"**Por quê:** {motivo}")
            st.markdown(f"**O que fazer:** {acao}")
    st.subheader("📚 Biblioteca de ideias no formato de piloto")
    st.caption("Proposta pequena, com prazo, custo limitado e forma de medir é mais fácil de aprovar.")
    for b in BIBLIOTECA:
        with st.expander(f"💡 {b['titulo']}"):
            st.markdown(f"**Como funciona:** {b['como']}\n\n**Piloto:** {b['piloto']}\n\n**Como medir:** {b['medir']}")


# ============================================================
# 13. SOBRE O PROJETO
# ============================================================

with aba_sobre:
    st.subheader("🎯 O problema")
    st.markdown("""
Em e-commerce, o preço muda o tempo todo, e conferir a concorrência pneu a pneu, à mão, toma horas e
fica desatualizado no dia seguinte. A pergunta do dia a dia era simples, mas sem resposta rápida:
**estamos mais caros ou mais baratos, em quais pneus, e o que os concorrentes estão fazendo?**
""")
    st.subheader("💡 A solução")
    st.markdown("""
Um pipeline de dados em Python, do zero:

1. **Coleta:** um robô visita as três lojas e lê preço, PIX, parcelamento e estoque de cada pneu,
   usando a API pública das lojas (GraphQL do Magento) e a leitura do HTML das páginas.
2. **Tratamento:** pandas padroniza os dados, calcula diferenças e detecta sinais de promoção,
   comparando cada coleta com a anterior.
3. **Histórico:** cada coleta é gravada em arquivo, formando a série de preços ao longo do tempo.
4. **Automação:** o GitHub Actions roda a coleta todo dia e grava os dados novos no repositório.
5. **Visualização:** este painel em Streamlit e Plotly, que se atualiza sozinho a cada coleta.
""")
    st.code("Sites das lojas → robô de coleta (Python, agendado no GitHub Actions) → tratamento (pandas) → CSV → painel (Streamlit)",
            language=None)
    st.subheader("🧰 Ferramentas")
    st.markdown("Python · pandas · curl_cffi · BeautifulSoup · GraphQL · Plotly · Streamlit · Git, GitHub e GitHub Actions")
    st.subheader("📈 Resultados na versão interna")
    st.markdown("""
- Comparação de dezenas de pneus nas três lojas em minutos, em vez de horas de pesquisa manual.
- Alertas automáticos de promoção, mudança de preço e falta de estoque nos concorrentes.
- Uma visão única para a área comercial e a diretoria acompanharem preço, mercado e campanhas.
""")
    st.subheader("🔒 Sobre esta versão")
    st.markdown("""
A versão usada na empresa também integra **vendas faturadas, Google Analytics 4 e Google Ads**, com
análises de conversão e investimento em mídia. Esses dados são internos e **não aparecem aqui**.
Também foram omitidas a política comercial da Roma (descontos e parcelamento) e a ordem de vendas dos pneus.
Os preços desta versão são **reais e públicos** e se atualizam sozinhos todo dia; Black Friday e Ideias usam dados fictícios.
""")
