# bts-snipper

Monitor de preço de ingressos (BTS - 2026 World Tour Arirang) na BuyTicket. Só alerta — a compra é manual.

Monitora Setor = Arquibancada, Categoria = Inteira, nos dias 30/10 e 31/10/2026, e manda uma mensagem no Telegram quando aparecer um anúncio com preço <= `PRECO_ALVO`.

## Rodar local

```bash
pip install -r requirements.txt

export TELEGRAM_TOKEN="123456:abc..."
export TELEGRAM_CHAT_ID="7874718818"
export PRECO_ALVO=2800   # opcional, default 2800

python monitor.py --dry-run        # mostra o preço atual dos dois dias, sem mandar Telegram
python monitor.py --test-telegram  # manda uma mensagem de teste no Telegram
python monitor.py                  # execução normal (salva state.json e manda alerta se achar preço <= alvo)
```

`state.json` guarda, separado por dia (`dia30`/`dia31`), o último preço consultado e os anúncios já notificados — evita alertar de novo pro mesmo anúncio no mesmo preço.

## Configurar no GitHub Actions

- Secrets do repositório: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.
- Variable do repositório (opcional): `PRECO_ALVO` (default 2800 se não setar).
- O workflow roda a cada 5 minutos (`.github/workflows/monitor.yml`) e também pode ser disparado manualmente em Actions > Run workflow.

## Mudar o preço alvo

Local: variável de ambiente `PRECO_ALVO`. No GitHub Actions: Settings > Secrets and variables > Actions > Variables > `PRECO_ALVO`.
