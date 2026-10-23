"""
PREPARA OS DADOS DA VERSÃO PÚBLICA (portfólio) | Monitor de preços
====================================================================
Para que serve: a versão interna do painel tem dados que NÃO podem ir para um link público
(vendas, GA4, Google Ads, a regra de desconto da Roma, preços internos). Este script pega uma
"foto" da sua última coleta e copia para a pasta dados/ SÓ o que é público:

  - preços que qualquer pessoa vê nos sites (preço cheio da Roma e preços dos concorrentes);
  - estoque e parcelamento dos concorrentes;
  - campanhas e promoções dos concorrentes.

O que fica de fora (nunca é copiado):
  - PIX, parcelado e parcela da Roma (são calculados com a regra interna de desconto);
  - diferenças e classificações calculadas com essa regra;
  - quantidade vendida, canal (varejo/distribuição), código interno (SKU) e grupos;
  - preço da Roma de pneus que não estão no site (vêm da planilha interna);
  - a tabela de parcelas da Roma;
  - a ordem original dos pneus (ela segue o ranking de vendas): os pneus são renumerados por tipo e medida.

Como usar: não precisa rodar este arquivo. O coletor.py chama ele sozinho.
(Ele procura a versão interna nas pastas ao lado desta, ex.: versao06.)

Ele roda uma vez só, na primeira coleta, para criar a pasta dados/ e a lista de pneus.
"""

import os
import sys

import pandas as pd

DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

# Colunas que podem ir para o público (todo o resto é descartado)
COLUNAS_PRECOS = ["item", "medida", "modelo", "data_coleta", "concorrente", "equivalencia",
                  "roma_disponivel", "roma_preco_cheio",
                  "conc_disponivel", "conc_estoque_qtd", "conc_preco_cheio", "conc_preco_pix",
                  "conc_preco_parcelado", "conc_n_parcelas", "conc_valor_parcela", "conc_desconto_pix_pct"]
COLUNAS_PNEUS = ["item", "medida", "modelo", "tipo", "no_site_roma", "url_roma", "url_pneustore", "url_acheipneus"]
# Lista que o robô público usa para coletar (links e códigos públicos dos produtos, nada de vendas)
COLUNAS_LISTA = ["item", "medida", "modelo", "tipo", "no_site_roma", "sku_roma", "roma_disponivel", "url_roma",
                 "url_pneustore", "url_acheipneus", "sku_acheipneus", "equivalencia_pneustore",
                 "equivalencia_acheipneus"]
COLUNAS_PARCELAS = ["data_coleta", "item", "medida", "modelo", "loja", "parcelas", "total", "valor_parcela",
                    "juros", "fonte"]
COLUNAS_CAMPANHAS = ["data_coleta", "concorrente", "fonte", "titulo", "tipo", "forca", "maior_pct", "status",
                     "qtd_produtos", "pneus_monitorados", "link", "imagem", "novidade"]
COLUNAS_PROMOCOES = ["data_coleta", "concorrente", "item", "pneu", "sinal", "detalhe"]

# Palavras que nunca podem aparecer no nome de uma coluna publicada (trava de segurança)
PROIBIDAS = ["roma_preco_pix", "roma_preco_parcelado", "roma_valor_parcela", "roma_n_parcelas", "dif_",
             "classificacao", "qtd_vendida", "canal", "sku", "grupo", "vend", "ga4", "receita", "pedido"]


def ler_csv(pasta, nome, **opcoes):
    caminho = os.path.join(pasta, nome)
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig", **opcoes) if os.path.exists(caminho) else None


def so_colunas(tabela, colunas):
    return tabela[[c for c in colunas if c in tabela.columns]].copy()


def limpar_precos(tabela, pneus):
    """Mantém só as colunas públicas e apaga o preço da Roma dos pneus que não estão no site."""
    tabela = so_colunas(tabela, COLUNAS_PRECOS)
    no_site = set(pneus.loc[pneus["no_site_roma"] == "Sim", "item"])
    fora = ~tabela["item"].isin(no_site)
    tabela.loc[fora, "roma_preco_cheio"] = float("nan")
    tabela.loc[fora, "roma_disponivel"] = "fora_do_site"
    return tabela


def conferir(nome, tabela):
    """Trava de segurança: para tudo se alguma coluna interna escapou."""
    vazou = [c for c in tabela.columns for p in PROIBIDAS if p in c.lower()]
    if vazou:
        raise SystemExit(f"PAREI: a tabela {nome} tem colunas internas {vazou}. Nada foi publicado.")


def salvar(nome, tabela):
    conferir(nome, tabela)
    tabela.to_csv(os.path.join(DESTINO, nome), sep=";", index=False, encoding="utf-8-sig")
    print(f"   {nome:<26} {len(tabela):>6} linhas")


def achar_versao_interna():
    """Procura, nas pastas ao lado do portfólio, a versão interna mais recente
    (a que tem base_concorrencia.xlsx e produtos_monitorados.csv)."""
    pasta_mae = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidatas = []
    for nome in os.listdir(pasta_mae):
        pasta = os.path.join(pasta_mae, nome)
        if (os.path.isdir(pasta) and pasta != os.path.dirname(DESTINO)
                and os.path.exists(os.path.join(pasta, "base_concorrencia.xlsx"))
                and os.path.exists(os.path.join(pasta, "produtos_monitorados.csv"))):
            candidatas.append(pasta)
    return max(candidatas, key=lambda p: os.path.getmtime(os.path.join(p, "base_concorrencia.xlsx"))) if candidatas else None


def main(origem):
    if not os.path.exists(os.path.join(origem, "base_concorrencia.xlsx")):
        raise SystemExit(f"Não encontrei base_concorrencia.xlsx em {origem}. Rode o coletor antes.")
    os.makedirs(DESTINO, exist_ok=True)

    # 1. Lista de pneus (sem vendas, canal, SKU e grupo)
    pneus = ler_csv(origem, "produtos_monitorados.csv", dtype={"sku_roma": str, "sku_acheipneus": str})
    pneus["item"] = pneus["item"].astype(int)
    for coluna, padrao in {"tipo": "", "no_site_roma": "Sim", "url_roma": ""}.items():
        if coluna not in pneus:
            pneus[coluna] = padrao
    pneus["no_site_roma"] = pneus["no_site_roma"].fillna("Sim")
    pneus.loc[pneus["no_site_roma"] != "Sim", "url_roma"] = ""      # link de pneu fora do site não existe
    completa = pneus.copy()
    pneus = so_colunas(pneus, COLUNAS_PNEUS)

    # Renumera os pneus por tipo e medida: na lista interna, a ordem dos números segue o ranking
    # de vendas, e isso também é informação interna
    pneus = pneus.sort_values(["tipo", "medida", "modelo"]).reset_index(drop=True)
    novo_numero = dict(zip(pneus["item"], range(1, len(pneus) + 1)))
    pneus["item"] = pneus["item"].map(novo_numero)

    def renumerar(tabela):
        tabela = tabela[tabela["item"].isin(novo_numero)].copy()
        tabela["item"] = tabela["item"].map(novo_numero)
        return tabela

    print(f"Preparando a foto pública a partir de: {origem}")
    salvar("pneus.csv", pneus)

    # Lista do robô público: sem vendas, canal e preço interno (o preço da Roma vem sempre do site)
    lista = so_colunas(renumerar(completa), COLUNAS_LISTA).sort_values("item")
    lista.insert(1, "grupo", "Portfólio")
    lista["roma_preco_cheio"] = ""
    for c in ["sku_roma", "sku_acheipneus"]:
        lista[c] = lista[c].fillna("").str.replace(r"\.0$", "", regex=True)
    lista.to_csv(os.path.join(DESTINO, "lista_coleta.csv"), sep=";", index=False, encoding="utf-8-sig")
    print(f"   {'lista_coleta.csv':<26} {len(lista):>6} linhas")

    # 2. Preços da última coleta e histórico
    base = pd.read_excel(os.path.join(origem, "base_concorrencia.xlsx"), sheet_name="Base_Consolidada")
    salvar("precos.csv", limpar_precos(renumerar(base), pneus))
    hist = ler_csv(origem, "historico_precos.csv")
    if hist is not None:
        salvar("historico_precos.csv", limpar_precos(renumerar(hist), pneus))

    # 3. Parcelas: só dos concorrentes (a tabela da Roma usa a regra interna)
    parcelas = ler_csv(origem, "parcelas_atuais.csv")
    if parcelas is not None:
        parcelas = renumerar(parcelas[parcelas["loja"] != "Roma"])
        salvar("parcelas.csv", so_colunas(parcelas, COLUNAS_PARCELAS))

    # 4. Campanhas e promoções dos concorrentes (informação pública dos sites deles)
    for origem_nome, destino_nome, colunas in [
            ("campanhas_atuais.csv", "campanhas.csv", COLUNAS_CAMPANHAS),
            ("historico_campanhas.csv", "historico_campanhas.csv", COLUNAS_CAMPANHAS),
            ("historico_promocoes.csv", "promocoes.csv", COLUNAS_PROMOCOES)]:
        tabela = ler_csv(origem, origem_nome)
        if tabela is not None:
            tabela = tabela[tabela["concorrente"] != "Roma"]
            if "item" in tabela:
                tabela = renumerar(tabela)
            salvar(destino_nome, so_colunas(tabela, colunas))

    print("Pronto! Confira a pasta dados/ e suba no GitHub do portfólio.")


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else achar_versao_interna()
    if not pasta:
        raise SystemExit("Não achei a versão interna (pasta com base_concorrencia.xlsx) ao lado do portfólio.")
    main(pasta)
