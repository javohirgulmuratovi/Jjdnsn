import os, json, sqlite3, asyncio, io
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "Soatshunosbot_bot").lstrip("@")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
DB_PATH = os.getenv("DB_PATH", "soatshunos.db")

if not BOT_TOKEN or not ADMIN_ID:
    raise RuntimeError("BOT_TOKEN va ADMIN_ID Railway Variables ga kiritilishi kerak.")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
db.execute("""CREATE TABLE IF NOT EXISTS users(
 user_id INTEGER PRIMARY KEY, first_name TEXT, plan TEXT DEFAULT 'Free',
 plan_until TEXT, referrer INTEGER, balance INTEGER DEFAULT 0,
 referral_paid INTEGER DEFAULT 0, joined TEXT DEFAULT CURRENT_TIMESTAMP)""")
db.execute("""CREATE TABLE IF NOT EXISTS payments(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT,
 amount INTEGER, file_id TEXT, analysis TEXT, status TEXT DEFAULT 'pending',
 created TEXT DEFAULT CURRENT_TIMESTAMP)""")
db.commit()

PLANS = {
 "Free": 0,
 "Standard": 2000,
 "Plus": 5000,
 "Premium": 10000
}
DAYS = 30

def user(uid):
    return db.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def menu():
    b = InlineKeyboardBuilder()
    b.button(text="🕒 Soatni ko‘rish", callback_data="clock")
    b.button(text="💎 Tariflar", callback_data="plans")
    b.button(text="👤 Profilim", callback_data="profile")
    b.button(text="👥 Taklif havolam", callback_data="ref")
    b.button(text="💳 To‘lov chekini yuborish", callback_data="receipt")
    b.button(text="❓ Yordam", callback_data="help")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()

def plan_kb():
    b = InlineKeyboardBuilder()
    for p, amount in PLANS.items():
        b.button(text=f"{p} — {amount:,} so‘m/oy".replace(",", " "), callback_data=f"plan:{p}")
    b.button(text="⬅️ Menyu", callback_data="home")
    b.adjust(1)
    return b.as_markup()

async def groq_receipt(file_id):
    if not GROQ_API_KEY:
        return "Groq API kaliti kiritilmagan. Chekni admin qo‘lda tekshirishi kerak."
    try:
        file = await bot.get_file(file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, destination=buf)
        import base64
        encoded = base64.b64encode(buf.getvalue()).decode()
        url = f"https://api.groq.com/openai/v1/chat/completions"
        payload = {
          "model": GROQ_MODEL,
          "messages": [{
            "role": "user",
            "content": [
              {"type": "text", "text": "Chek rasmini tahlil qil. Summani, sanani, oluvchi nomini va tranzaksiya raqamini ajrat. Ko‘rinmasa noma'lum deb yoz. Faqat qisqa o‘zbekcha javob ber. Rasmning o‘zi pul tushganini isbotlamasligini ham eslat."},
              {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
            ]
          }],
          "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(url, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Chekni AI tahlil qila olmadi ({type(e).__name__}). Admin qo‘lda tekshirsin."

@dp.message(CommandStart())
async def start(m: Message):
    args = (m.text or "").split(maxsplit=1)
    referrer = None
    if len(args) > 1 and args[1].startswith("ref"):
        try: referrer = int(args[1][3:])
        except: pass
    if not user(m.from_user.id):
        db.execute("INSERT INTO users(user_id,first_name,referrer) VALUES(?,?,?)",
                   (m.from_user.id, m.from_user.first_name or "", referrer if referrer != m.from_user.id else None))
        db.commit()
    await m.answer(
        "Assalomu alaykum! 🕒 Soatshunos Bot’ga xush kelibsiz.\n\n"
        "Soat bot ichida ko‘rsatiladi. Oddiy Telegram bot foydalanuvchining shaxsiy profil familiyasini o‘zgartira olmaydi.",
        reply_markup=menu())

@dp.message(Command("admin"))
async def admin(m: Message):
    if m.from_user.id != ADMIN_ID:
        return await m.answer("Bu buyruq faqat admin uchun.")
    pending = db.execute("SELECT COUNT(*) n FROM payments WHERE status='pending'").fetchone()["n"]
    await m.answer(f"Admin paneli\nKutilayotgan chek: {pending}\nYangi cheklar uchun xabarlar sizga yuboriladi.")

@dp.callback_query(F.data == "home")
async def home(c: CallbackQuery):
    await c.message.edit_text("Asosiy menyu:", reply_markup=menu())
    await c.answer()

@dp.callback_query(F.data == "clock")
async def clock(c: CallbackQuery):
    now = datetime.now().strftime("%H:%M")
    await c.message.answer(f"🕒 Hozirgi vaqt: **{now}**\n\nBu bot ichidagi soat; Telegram profiliga yozilmaydi.", parse_mode="Markdown")
    await c.answer()

@dp.callback_query(F.data == "plans")
async def plans(c: CallbackQuery):
    text = ("💎 **Tariflar (30 kun)**\n\n"
            "Free — 0 so‘m\nStandard — 2 000 so‘m\nPlus — 5 000 so‘m\nPremium — 10 000 so‘m\n\n"
            "To‘lovni tanlangan tarifdan keyin chek bilan yuboring.")
    await c.message.edit_text(text, reply_markup=plan_kb(), parse_mode="Markdown")
    await c.answer()

@dp.callback_query(F.data.startswith("plan:"))
async def choose_plan(c: CallbackQuery):
    p = c.data.split(":",1)[1]
    if p not in PLANS: return await c.answer("Tarif topilmadi", show_alert=True)
    if p == "Free":
        db.execute("UPDATE users SET plan='Free',plan_until=NULL WHERE user_id=?", (c.from_user.id,))
        db.commit()
        await c.message.answer("Free tarifi tanlandi.", reply_markup=menu())
    else:
        db.execute("UPDATE users SET plan=? WHERE user_id=?", (p, c.from_user.id))
        db.commit()
        await c.message.answer(
            f"{p} tarifi: {PLANS[p]:,} so‘m / 30 kun.\n"
            "To‘lovni amalga oshirib, «To‘lov chekini yuborish» tugmasi orqali chek rasmini yuboring.".replace(",", " "),
            reply_markup=menu())
    await c.answer()

@dp.callback_query(F.data == "profile")
async def profile(c: CallbackQuery):
    u = user(c.from_user.id)
    until = u["plan_until"] or "Belgilanmagan"
    await c.message.answer(f"👤 ID: {c.from_user.id}\nTarif: {u['plan']}\nAmal qilish muddati: {until}\nBonus: {u['balance']} so‘m")
    await c.answer()

@dp.callback_query(F.data == "ref")
async def ref(c: CallbackQuery):
    link = f"https://t.me/{BOT_USERNAME}?start=ref{c.from_user.id}"
    u = user(c.from_user.id)
    await c.message.answer(f"👥 Taklif havolangiz:\n{link}\n\nBonus: {u['balance']} so‘m.\nBonus faqat taklif qilingan foydalanuvchining birinchi to‘lovi admin tomonidan tasdiqlanganda beriladi.")
    await c.answer()

@dp.callback_query(F.data == "receipt")
async def receipt_prompt(c: CallbackQuery):
    await c.message.answer("Avval tarifni tanlang, keyin to‘lov chekini rasm sifatida shu chatga yuboring.")
    await c.answer()

@dp.callback_query(F.data == "help")
async def help_cb(c: CallbackQuery):
    await c.message.answer("Yordam: tarifni tanlang, to‘lov qiling va chek rasmini yuboring. Shubhali cheklar admin tomonidan tekshiriladi. Bot hech qachon Telegram login kodi yoki 2FA parolini so‘ramaydi.")
    await c.answer()

@dp.message(F.photo)
async def photo(m: Message):
    u = user(m.from_user.id)
    if not u:
        return await m.answer("Avval /start bosing.")
    plan = u["plan"]
    if plan == "Free":
        return await m.answer("Avval 💎 Tariflar bo‘limidan pullik tarif tanlang.")
    p = db.execute("SELECT plan FROM users WHERE user_id=?", (m.from_user.id,)).fetchone()["plan"]
    analysis = await groq_receipt(m.photo[-1].file_id)
    cur = db.execute("INSERT INTO payments(user_id,plan,amount,file_id,analysis) VALUES(?,?,?,?,?)",
                     (m.from_user.id, p, PLANS[p], m.photo[-1].file_id, analysis))
    db.commit()
    pid = cur.lastrowid
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{pid}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{pid}")
    ]])
    await m.answer("Chek qabul qilindi. Groq rasmni tahlil qildi, lekin pul tushganini tasdiqlay olmaydi. Admin tekshiruvini kuting.")
    try:
        await bot.send_photo(ADMIN_ID, m.photo[-1].file_id,
            caption=f"Yangi to‘lov cheki #{pid}\nFoydalanuvchi: {m.from_user.id}\nTarif: {p}\nSumma: {PLANS[p]} so‘m\n\nAI tahlili:\n{analysis}\n\nPul tushganini bank/to‘lov tizimidan alohida tekshiring.",
            reply_markup=kb)
    except Exception:
        await m.answer("Admin xabari yuborilmadi. Admin botni ochib /start bosganini tekshiring.")

@dp.callback_query(F.data.startswith(("approve:", "reject:")))
async def review(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        return await c.answer("Ruxsat yo‘q", show_alert=True)
    action, raw = c.data.split(":")
    pid = int(raw)
    pay = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not pay or pay["status"] != "pending":
        return await c.answer("Bu chek avval ko‘rib chiqilgan.", show_alert=True)
    if action == "approve":
        until = (datetime.utcnow() + timedelta(days=DAYS)).isoformat(timespec="seconds")
        db.execute("UPDATE payments SET status='approved' WHERE id=?", (pid,))
        db.execute("UPDATE users SET plan=?,plan_until=? WHERE user_id=?", (pay["plan"], until, pay["user_id"]))
        # Referral reward is paid once, after first approved payment.
        u = user(pay["user_id"])
        if u and u["referrer"] and not u["referral_paid"]:
            db.execute("UPDATE users SET balance=balance+700 WHERE user_id=?", (u["referrer"],))
            db.execute("UPDATE users SET referral_paid=1 WHERE user_id=?", (pay["user_id"],))
            try: await bot.send_message(u["referrer"], "🎉 Taklif bonusingizga 700 so‘m qo‘shildi!")
            except: pass
        await bot.send_message(pay["user_id"], f"✅ To‘lov tasdiqlandi! {pay['plan']} tarifi 30 kunga faollashtirildi.")
        await c.message.edit_caption((c.message.caption or "") + "\n\nTASDIQLANDI")
    else:
        db.execute("UPDATE payments SET status='rejected' WHERE id=?", (pid,))
        await bot.send_message(pay["user_id"], "❌ To‘lov cheki rad etildi. Admin bilan bog‘laning: @Javoh_123")
        await c.message.edit_caption((c.message.caption or "") + "\n\nRAD ETILDI")
    db.commit()
    await c.answer("Bajarildi")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
