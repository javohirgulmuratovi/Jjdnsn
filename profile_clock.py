"""
Soatshunos local profile clock.
Run this on the account owner's own device, NOT on Railway.
Phone, Telegram login code, and 2FA password are entered directly into
Telethon's local terminal prompt. They are never sent to the bot/admin.
The Telethon session file is stored locally in this folder.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient, functions

def read_int(prompt):
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Faqat raqam kiriting.")

async def main():
    print("SOATSHUNOS — shaxsiy profil soati")
    print("Bu dastur Railway'da emas, o'zingizning qurilmangizda ishlaydi.")
    api_id = read_int("Telegram API_ID: ")
    api_hash = input("Telegram API_HASH: ").strip()
    if not api_hash:
        print("API_HASH bo'sh bo'lmasin.")
        return

    session_path = str(Path(__file__).with_name("my_telegram_session"))
    client = TelegramClient(session_path, api_id, api_hash)

    # Telethon requests phone, login code, and (if enabled) 2FA password
    # interactively in this local process.
    await client.start()

    me = await client.get_me()
    original_first = me.first_name or ""
    original_last = me.last_name or ""

    print(f"\nUlandi: {original_first} {original_last}".strip())
    print("Ko'rinish: ism | HH:MM")
    print("To'xtatish uchun Ctrl+C bosing.")
    print("Dastur yopilganda avvalgi familiya tiklanadi.")

    try:
        while True:
            now = datetime.now().strftime("%H:%M")
            # Preserve first name; set last name to the clock suffix.
            await client(functions.account.UpdateProfileRequest(
                first_name=original_first,
                last_name=f"| {now}"
            ))
            print(f"Yangilandi: {original_first} | {now}")
            # Align approximately to the next minute.
            current = datetime.now()
            await asyncio.sleep(max(1, 60 - current.second))
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nSoat to'xtatilmoqda...")
    finally:
        try:
            await client(functions.account.UpdateProfileRequest(
                first_name=original_first,
                last_name=original_last
            ))
            print("Avvalgi ism va familiya tiklandi.")
        except Exception as e:
            print("Avvalgi familiyani avtomatik tiklab bo'lmadi:", str(e))
            print("Telegram profil sozlamalaridan familiyangizni qo'lda tiklang.")
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print("\nXatolik:", str(exc))
        print("Internet va API_ID/API_HASH qiymatlarini tekshiring.")
