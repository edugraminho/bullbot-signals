#!/usr/bin/env python3
"""
Script para obter Chat ID do Telegram
"""

import os
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


def get_chat_id():
    """Obter Chat ID via API do Telegram"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN não encontrado no .env")
        return

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    print("🔍 Obtendo Chat IDs...")
    print("📝 Envie uma mensagem para o bot @CryptoHunterBitBot primeiro!")
    print("=" * 50)

    try:
        response = requests.get(url)
        data = response.json()

        if data.get("ok"):
            updates = data.get("result", [])

            if not updates:
                print("❌ Nenhuma mensagem encontrada!")
                print("💡 Envie uma mensagem para o bot primeiro e tente novamente")
                return

            print(f"✅ Encontrados {len(updates)} updates:")
            print()

            for i, update in enumerate(updates):
                if "message" in update:
                    message = update["message"]
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    chat_type = chat.get("type", "unknown")
                    chat_title = chat.get("title", "")
                    chat_username = chat.get("username", "")
                    chat_first_name = chat.get("first_name", "")

                    print(f"📱 Update {i + 1}:")
                    print(f"   Chat ID: {chat_id}")
                    print(f"   Tipo: {chat_type}")

                    if chat_type == "private":
                        print(f"   Nome: {chat_first_name}")
                        if chat_username:
                            print(f"   Username: @{chat_username}")
                    elif chat_type in ["group", "supergroup"]:
                        print(f"   Grupo: {chat_title}")
                        if chat_username:
                            print(f"   Username: @{chat_username}")

                    print()
        else:
            print(f"❌ Erro na API: {data.get('description', 'Erro desconhecido')}")

    except Exception as e:
        print(f"❌ Erro ao fazer requisição: {e}")


if __name__ == "__main__":
    get_chat_id()
