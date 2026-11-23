# Soatshunos Bot — Railway + shaxsiy profil soati

## ZIP tarkibi
- `bot.py` — Telegram bot: menyu, tariflar, referral, Groq chek tahlili, admin ko'rib chiqishi.
- `profile_clock.py` — profil familiyasidagi soatni foydalanuvchining O'Z qurilmasida yangilaydi.
- `requirements.txt`, `Procfile`, `runtime.txt`, `.env.example` — Railway va Python sozlamalari.

## Juda muhim: akkaunt xavfsizligi
`profile_clock.py` Railway serverida ishlamaydi. Uni har bir akkaunt egasi o'z qurilmasida ishga tushiradi.
- Telefon raqami, Telegram login kodi va 2FA paroli Telethon'ning mahalliy terminal oynasiga kiritiladi.
- Kod/parol botga yoki adminga yuborilmaydi.
- `my_telegram_session.session` fayli faqat shu qurilmada saqlanadi. Uni hech kimga yubormang yoki GitHub'ga yuklamang.
- Sessiya fayli avtorizatsiyani davom ettirishga imkon beradi; uni parol kabi maxfiy saqlang.
- Dastur to'xtaganda avvalgi familiyani tiklashga urinadi. Internet uzilishi yoki dastur majburan yopilishi bunga xalaqit berishi mumkin.

## Profil soatini ishga tushirish
1. Python 3.11 o'rnating.
2. Terminalda shu papkaga o'ting.
3. `pip install -r requirements.txt` buyrug'ini bajaring.
4. Telegram API ma'lumotlarini rasmiy `my.telegram.org` saytidan oling. `API_ID` va `API_HASH`ni hech kimga bermang.
5. `python profile_clock.py` buyrug'ini bajaring.
6. Telefon raqamingizni, Telegram yuborgan kodni va zarur bo'lsa 2FA parolni terminalga kiriting.
7. Profil familiyasi `| HH:MM` ko'rinishida yangilanadi; ism saqlanadi.

Bu dastur foydalanuvchi qurilmasi yoqilgan va internetga ulangan paytda ishlaydi. Har bir foydalanuvchi o'z akkauntida mustaqil ishga tushirishi kerak.

## Railway botini joylash
1. `bot.py`, `requirements.txt`, `Procfile`, `runtime.txt` va `.env.example` fayllarini GitHub'ga yuklang.
2. `my_telegram_session.session`, `.env`, tokenlar yoki API kalitlarini GitHub'ga yuklamang.
3. Railway -> New Project -> Deploy from GitHub Repo.
4. Variables bo'limiga `.env.example` ichidagi qiymatlarni kiriting.
5. `ADMIN_ID` — adminning raqamli Telegram ID raqami.
6. Deploy qiling. Admin botga `/start` yuborsin.

## Railway Variables
- `BOT_TOKEN`
- `ADMIN_ID`
- `BOT_USERNAME`
- `GROQ_API_KEY`
- `GROQ_VISION_MODEL`
- `DB_PATH`

`API_ID` va `API_HASH`ni Railway Variables'ga kiritmang: profil soati uchun ular faqat foydalanuvchining o'z qurilmasida ishlatiladi.

## Cheklarni tekshirish
Groq chek rasmini o'qib, ma'lumotlarni ajratadi. Rasm pul haqiqatda tushganini isbotlamaydi. Admin pul tushganini to'lov tizimidan mustaqil tekshirishi kerak.
