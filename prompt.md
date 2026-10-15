Quero um monitor simples de preço de ingressos na BuyTicket (site de revenda). Só ALERTA — a compra eu faço manualmente. Nada de login automático, checkout ou bypass de proteção.

## Contexto

- Show: BTS - 2026 World Tour Arirang
- Datas: 30/10/2026 e 31/10/2026 (qualquer uma serve)
- Filtros: Setor = Arquibancada, Categoria = Inteira
- Alerta: quando houver anúncio com preço <= R$ 2800, me notificar no Telegram

## Insumos

Na pasta `har/` deixei `dia30.har` e `dia31.har`, exportados do DevTools (Network > Fetch/XHR) nas páginas de cada dia.

## Passo 1 — Investigação (faça isso primeiro e me mostre)

- Analise os HARs (com script, não lendo tudo no olho) e identifique o endpoint que retorna a lista de anúncios/ingressos.
- Mostre: URL, método, parâmetros, headers essenciais, e como aparecem data/evento, setor, categoria (inteira/meia), preço e ID do anúncio.
- Verifique se o preço do JSON já inclui a taxa da plataforma ou não, e me diga.
- Teste se o endpoint funciona SEM cookies de login. Prefira a versão sem autenticação. Se precisar de algo, me explique antes de seguir.
- Confirme comigo antes de passar para o Passo 2.

## Passo 2 — Implementação (Python, simples)

- `monitor.py` usando `requests`:
  - consulta o endpoint para as duas datas
  - filtra Arquibancada + Inteira
  - pega anúncios com preço <= PRECO_ALVO
  - envia mensagem no Telegram com: data, setor, preço, quantidade (se houver) e link direto do evento
- Config via variáveis de ambiente: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `PRECO_ALVO` (default 2800).
- Anti-alerta repetido: salvar em `state.json` os anúncios já notificados (ID + preço). Só alertar de novo se aparecer anúncio novo ou se o preço de um já visto cair.
- Se a API falhar 3 vezes seguidas, mandar UM aviso no Telegram ("monitor quebrou") e não ficar spamando. Avisar de novo quando voltar a funcionar.
- User-Agent normal de navegador, timeout nas requisições e, no máximo, 1 requisição por data a cada execução.
- Parar sozinho depois de 31/10/2026 (não alertar mais).
- Flag `--dry-run` que imprime o que encontraria, sem mandar Telegram, e flag `--test-telegram` que manda uma mensagem de teste.

## Passo 3 — Agendamento com GitHub Actions

- Workflow `.github/workflows/monitor.yml` com cron a cada 15 minutos + `workflow_dispatch` para rodar manual.
- Secrets: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`. `PRECO_ALVO` como variable do repositório.
- Persistir o `state.json` entre execuções commitando de volta no repo (com `[skip ci]`), ou via cache — escolha a opção mais simples e confiável.

## Regras

- `har/` e `.env` no `.gitignore` ANTES do primeiro commit (os HARs têm meus cookies).
- Código curto e legível, sem frameworks desnecessários.
- README curto: como rodar local, como configurar secrets, como mudar o preço alvo.
- Rode localmente com `--dry-run` e `--test-telegram` antes de criar o repo e o workflow.
