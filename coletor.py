"""
COLETOR DO PAINEL PÚBLICO (portfólio) | Monitor de preços
==========================================================
Igual à versão interna: abra este arquivo no VS Code e aperte ▶.
Depois suba a pasta dados/ no GitHub (commit e push), e o painel se atualiza.

O que acontece quando você aperta ▶:
  1. Na PRIMEIRA vez, ele procura a sua versão interna nas pastas ao lado (ex.: versao06)
     e copia de lá a lista de pneus e a última coleta, já sem nada interno.
  2. Visita as três lojas e coleta preço, estoque, parcelas e campanhas (10 a 15 minutos).
  3. Passa tudo pelo filtro de segurança (preparar_dados.py) e grava em dados/.

O mesmo arquivo é usado pelo GitHub (coleta automática diária) e pelo botão do painel.
"""

import os
import shutil
import sys
import tempfile

import pandas as pd

PASTA = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(PASTA, "dados")
sys.path.insert(0, os.path.join(PASTA, "coleta"))
sys.path.insert(0, PASTA)

# Colunas na ordem em que o motor grava o histórico (o histórico público tem menos colunas;
# completamos com vazio para a coleta nova entrar na coluna certa)
COLUNAS_MOTOR = ["item", "grupo", "medida", "modelo", "sku_roma", "data_coleta", "concorrente",
                 "equivalencia", "roma_fonte_preco", "roma_disponivel", "conc_disponivel", "conc_estoque_qtd",
                 "situacao_estoque", "roma_preco_cheio", "roma_preco_pix", "roma_preco_parcelado",
                 "roma_n_parcelas", "roma_valor_parcela", "nome_anuncio_concorrente", "conc_preco_cheio",
                 "conc_preco_pix", "conc_preco_parcelado", "conc_n_parcelas", "conc_valor_parcela",
                 "conc_desconto_pix_pct", "conc_desconto_parcelado_pct", "dif_pix_pct", "dif_parcelado_pct",
                 "dif_parcela_pct", "classificacao_pix"]


def ler(nome):
    caminho = os.path.join(DADOS, nome)
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig") if os.path.exists(caminho) else None


def primeira_vez():
    """Cria a pasta dados/ a partir da versão interna que estiver ao lado (só na primeira coleta)."""
    from preparar_dados import achar_versao_interna, main as preparar
    interna = achar_versao_interna()
    if not interna:
        raise SystemExit("Primeira coleta: não achei a versão interna (pasta com base_concorrencia.xlsx) "
                         "ao lado da pasta do portfólio. Coloque as duas pastas lado a lado e rode de novo.")
    print(f"Primeira coleta: copiando a lista de pneus de {interna} (sem dados internos)...")
    preparar(interna)


def coletar():
    lista = os.path.join(DADOS, "lista_coleta.csv")
    if not os.path.exists(lista):
        primeira_vez()

    pasta_original = os.getcwd()
    temporaria = tempfile.mkdtemp(prefix="coleta_publica_")
    try:
        # 1. Pasta de trabalho do robô: lista de pneus e históricos que o painel já tem
        shutil.copy(lista, os.path.join(temporaria, "produtos_monitorados.csv"))
        hist = ler("historico_precos.csv")
        if hist is not None:
            hist.reindex(columns=COLUNAS_MOTOR).to_csv(
                os.path.join(temporaria, "historico_precos.csv"), sep=";", index=False, encoding="utf-8-sig")
        for publico, interno in [("historico_campanhas.csv", "historico_campanhas.csv"),
                                 ("promocoes.csv", "historico_promocoes.csv")]:
            if os.path.exists(os.path.join(DADOS, publico)):
                shutil.copy(os.path.join(DADOS, publico), os.path.join(temporaria, interno))

        # 2. Coleta nas três lojas
        os.chdir(temporaria)
        import motor_coleta
        motor_coleta.preparar_lista = lambda: None       # a lista pública já está pronta
        motor_coleta.coletar()
        os.chdir(pasta_original)

        # 3. Filtro de segurança e gravação em dados/
        from preparar_dados import main as preparar
        preparar(temporaria)
        print("\nAgora suba a pasta dados/ no GitHub (commit e push) e o painel se atualiza.")
    finally:
        os.chdir(pasta_original)
        shutil.rmtree(temporaria, ignore_errors=True)


if __name__ == "__main__":
    coletar()
