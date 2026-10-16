#!/usr/bin/env python3
import argparse
import json
import os
import time
from datetime import datetime, timezone, timedelta

import requests

API_BASE = "https://buyticketbrasil.com/api/backend/marketplaces"
CHECKOUT_BASE = "https://buyticketbrasil.com/checkout"
ARQUIBANCADA_TICKET_ID = "59b9544c-a947-46f6-a2db-14623a06d76c"
CATEGORIA_ALVO = "Inteira"
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
TIMEOUT = 10
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
BRT = timezone(timedelta(hours=-3))

SESSOES = {
    "dia30": {
        "session_id": "ced30381-0cc4-4779-9c6b-ba05f44d086e",
    },
    # dia31 removido: já garantido ingresso do dia 30, falta só mais 1 para o mesmo dia
}

DATA_LIMITE = datetime(2026, 11, 1, tzinfo=BRT)  # para de alertar depois do show do dia 31

PRECO_ALVO = float(os.environ.get("PRECO_ALVO") or "2800")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
LOOP_DURATION_SECONDS = int(os.environ.get("LOOP_DURATION_SECONDS") or "240")
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS") or "15")


def carregar_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def registrar_historico(resultado, agora, preco):
    historico = resultado.setdefault("historico", [])
    historico.append({"em": agora.isoformat(), "preco": preco})


def enviar_telegram(msg, dry_run):
    if dry_run:
        print("[DRY-RUN] enviaria ao Telegram:\n" + msg)
        return
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[AVISO] TELEGRAM_TOKEN/TELEGRAM_CHAT_ID não configurados; mensagem não enviada:")
        print(msg)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=TIMEOUT)
    r.raise_for_status()


def consultar_inteira_arquibancada(session_id):
    url = f"{API_BASE}/sessions/{session_id}/tickets/{ARQUIBANCADA_TICKET_ID}/categories"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    for cat in r.json().get("categories", []):
        if cat.get("name") == CATEGORIA_ALVO:
            valor = cat.get("amount", {}).get("value") or 0
            listing_id = cat.get("listingId")
            if not listing_id or not valor:
                return None  # sem anúncio disponível nessa categoria
            return {"preco": valor, "listing_id": listing_id}
    return None


def processar_dia(label, info, state, dry_run):
    agora = datetime.now(BRT)
    resultado = state.setdefault(label, {})

    try:
        oferta = consultar_inteira_arquibancada(info["session_id"])
        resultado["falhas_consecutivas"] = 0
    except Exception as e:
        resultado["falhas_consecutivas"] = resultado.get("falhas_consecutivas", 0) + 1
        print(f"[ERRO] {label}: {e}")
        if resultado["falhas_consecutivas"] >= 3 and not resultado.get("falha_avisada"):
            enviar_telegram(f"⚠️ monitor quebrou ao consultar {label}: {e}", dry_run)
            resultado["falha_avisada"] = True
        return

    if resultado.get("falha_avisada"):
        enviar_telegram(f"✅ monitor voltou a funcionar para {label}", dry_run)
        resultado["falha_avisada"] = False

    resultado["ultima_consulta"] = agora.isoformat()

    if oferta is None:
        resultado["ultimo_preco"] = None
        resultado["ultimo_listing_id"] = None
        registrar_historico(resultado, agora, None)
        print(f"[{agora:%Y-%m-%d %H:%M}] {label} (Arquibancada/Inteira): sem anúncio disponível")
        return

    preco = oferta["preco"]
    listing_id = oferta["listing_id"]
    resultado["ultimo_preco"] = preco
    resultado["ultimo_listing_id"] = listing_id
    registrar_historico(resultado, agora, preco)

    dentro_do_alvo = preco <= PRECO_ALVO
    situacao = "DENTRO DO ALVO" if dentro_do_alvo else "acima do alvo"
    print(f"[{agora:%Y-%m-%d %H:%M}] {label} (Arquibancada/Inteira): R$ {preco:.2f} ({situacao})")

    if not dentro_do_alvo:
        return

    notificados = resultado.setdefault("notificados", {})
    preco_anterior = notificados.get(listing_id)
    if preco_anterior is not None and preco >= preco_anterior:
        return  # já avisado nesse preço (ou preço subiu de novo), não repete

    link_checkout = f"{CHECKOUT_BASE}?listing={listing_id}"
    msg = (
        "\U0001f3ab BTS Arirang - 2026 World Tour\n"
        f"Dia: {label}\n"
        "Setor: Arquibancada | Categoria: Inteira\n"
        f"Preço: R$ {preco:.2f}\n"
        f"Link (já no checkout): {link_checkout}"
    )
    enviar_telegram(msg, dry_run)
    notificados[listing_id] = preco


def main():
    parser = argparse.ArgumentParser(description="Monitor de preço BTS Arirang (Arquibancada/Inteira)")
    parser.add_argument("--dry-run", action="store_true", help="só mostra o que faria, não envia Telegram")
    parser.add_argument("--test-telegram", action="store_true", help="envia uma mensagem de teste e sai")
    parser.add_argument("--once", action="store_true", help="roda só uma verificação e sai (ignora o loop)")
    args = parser.parse_args()

    if args.test_telegram:
        enviar_telegram("✅ Teste do monitor BTS Arirang: Telegram configurado corretamente.", dry_run=False)
        return

    if datetime.now(BRT) >= DATA_LIMITE:
        print("Shows já passaram (após 31/10/2026). Monitor não faz mais nada.")
        return

    state = carregar_state()
    inicio = time.monotonic()

    while True:
        for label, info in SESSOES.items():
            processar_dia(label, info, state, args.dry_run)

        if not args.dry_run:
            salvar_state(state)

        if args.once:
            break
        if time.monotonic() - inicio >= LOOP_DURATION_SECONDS:
            break
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
