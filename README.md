# 🛞 Monitor de Preços da Concorrência

Painel de inteligência competitiva para e-commerce de pneus: compara, pneu a pneu, **preço, parcelamento e estoque**
de três lojas on-line de pneus Goodyear e Kelly (Roma Pneus, Pneu Store e Achei Pneus).

**▶️ Acesse o painel:** _cole aqui o link do Streamlit_

## O problema
Conferir a concorrência pneu a pneu, à mão, toma horas e fica desatualizado no dia seguinte.
A pergunta era simples, mas sem resposta rápida: *estamos mais caros ou mais baratos, em quais pneus,
e o que os concorrentes estão fazendo?*

## A solução
Um pipeline de dados em Python, construído do zero:

```
Sites das lojas → robô de coleta (Python, agendado no GitHub Actions) → tratamento (pandas) → CSV → painel (Streamlit)
```

1. **Coleta:** leitura da API pública das lojas (GraphQL do Magento) e do HTML das páginas.
2. **Tratamento:** padronização, diferenças de preço e detecção automática de promoções.
3. **Histórico:** cada coleta vira um ponto da série de preços.
4. **Automação:** o GitHub Actions roda a coleta todo dia e grava os dados novos no repositório.
5. **Visualização:** Streamlit + Plotly; o painel se atualiza sozinho a cada coleta.

## O que o painel mostra
- Comparativo de preço lado a lado, com o menor preço em destaque
- Tabela completa com filtros e download
- Simulador de parcelamento de 1x a 12x
- Histórico de preços, sinais de promoção e radar de campanhas
- Monitor de Black Friday (preço maquiado) e gerador de ideias de ação

## Ferramentas
Python · pandas · curl_cffi · BeautifulSoup · GraphQL · Plotly · Streamlit · Git/GitHub · GitHub Actions

## Sobre esta versão
Esta é a versão de portfólio. Os preços são **reais e públicos**, coletados automaticamente nos sites das lojas.
A versão usada na empresa também integra vendas faturadas, Google Analytics 4 e Google Ads; esses dados são
internos e **foram omitidos**, assim como a política comercial da loja. As abas de Black Friday e Ideias
usam **dados fictícios**.

## Como rodar
```
pip install -r requirements.txt
python -m streamlit run app.py      # o painel
python coletor.py                   # uma coleta nova (no VS Code: abrir e apertar ▶)
```

## Estrutura
| Arquivo | Para que serve |
|---|---|
| `app.py` | O painel (Streamlit) |
| `coletor.py` | Faz uma coleta e atualiza `dados/`, sem dados internos (abrir e apertar ▶) |
| `atualizar_publico.py` | Atalho do coletor usado pelo GitHub Actions e pelo botão do painel |
| `coleta/` | O motor do robô (preços, parcelas e campanhas) |
| `preparar_dados.py` | Filtro de segurança: só deixa sair colunas públicas |
| `.github/workflows/coleta.yml` | Agenda a coleta diária no GitHub Actions |
| `dados/` | Os dados que o painel lê |

---
Feito por **Lucas Henrique** · Marketing & Dados
