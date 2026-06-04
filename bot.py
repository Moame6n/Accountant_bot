import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError, BadRequest
from config import TOKEN, CHANNEL_ID, AFFILIATE_LINK
from tools import (
    calculate_vat,
    calculate_depreciation,
    calculate_gross_profit,
    calculate_break_even
)

# ===== إعداد السجل =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ===== التحقق من الاشتراك =====
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        await asyncio.sleep(1)
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except BadRequest:
        return False
    except TelegramError:
        return False
    except Exception:
        return False

# ===== رسالة الاشتراك الإجباري =====
async def ask_to_subscribe(update: Update):
    keyboard = [
        [InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
        [InlineKeyboardButton("تحققت من اشتراكي ✅", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "⚠️ للاستخدام، اشترك في قناتنا أولاً\n\n"
        "القناة تحتوي على:\n"
        "✅ أدوات محاسبية مجانية\n"
        "✅ برومبتات ذكاء اصطناعي\n"
        "✅ ملخصات IFRS بالعربي\n\n"
        "بعد الاشتراك اضغط ✅ تحققت"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

# ===== القائمة الرئيسية =====
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🧮 ضريبة القيمة المضافة", callback_data="vat")],
        [InlineKeyboardButton("📉 حاسبة الاستهلاك", callback_data="depreciation")],
        [InlineKeyboardButton("📊 مجمل الربح", callback_data="gross_profit")],
        [InlineKeyboardButton("⚖️ نقطة التعادل", callback_data="break_even")],
        [InlineKeyboardButton("💼 برنامج محاسبي احترافي", url=AFFILIATE_LINK)],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== زر الرجوع =====
def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu")]
    ])

# ===== أمر البداية =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "مستخدم"

        if not await is_subscribed(user_id, context):
            await ask_to_subscribe(update)
            return

        await update.message.reply_text(
            f"أهلاً {user_name}! 👋\n\n"
            "مرحباً بك في بوت الأدوات المحاسبية 🧮\n"
            "اختر الأداة التي تريدها:",
            reply_markup=main_menu()
        )
    except TelegramError as e:
        logging.error(f"خطأ في start: {e}")

# ===== معالجة الأزرار =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError:
        pass

    user_id = query.from_user.id

    try:
        if query.data == "check_sub":
            await asyncio.sleep(1)
            if await is_subscribed(user_id, context):
                user_name = query.from_user.first_name or "مستخدم"
                await query.message.reply_text(
                    f"تم التحقق ✅ أهلاً {user_name}!\n"
                    "اختر الأداة التي تريدها:",
                    reply_markup=main_menu()
                )
            else:
                await query.message.reply_text(
                    "⚠️ لم يتم التحقق من اشتراكك بعد\n\n"
                    "تأكد من الاشتراك في القناة ثم اضغط تحققت مجدداً",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
                        [InlineKeyboardButton("تحققت من اشتراكي ✅", callback_data="check_sub")]
                    ])
                )
            return

        if not await is_subscribed(user_id, context):
            await ask_to_subscribe(update)
            return

        if query.data == "menu":
            await query.message.reply_text(
                "اختر الأداة التي تريدها:",
                reply_markup=main_menu()
            )

        elif query.data == "vat":
            context.user_data["mode"] = "vat"
            await query.message.reply_text(
                "🧮 حاسبة ضريبة القيمة المضافة (14%)\n\n"
                "أرسل المبلغ بالجنيه المصري:\n"
                "مثال: 1000"
            )

        elif query.data == "depreciation":
            context.user_data["mode"] = "depreciation"
            await query.message.reply_text(
                "📉 حاسبة الاستهلاك (القسط الثابت)\n\n"
                "أرسل البيانات بهذا الترتيب:\n"
                "تكلفة الأصل , قيمة الخردة , عدد السنوات\n\n"
                "مثال: 100000 , 10000 , 5"
            )

        elif query.data == "gross_profit":
            context.user_data["mode"] = "gross_profit"
            await query.message.reply_text(
                "📊 حاسبة مجمل الربح\n\n"
                "أرسل البيانات بهذا الترتيب:\n"
                "الإيرادات , تكلفة المبيعات\n\n"
                "مثال: 500000 , 300000"
            )

        elif query.data == "break_even":
            context.user_data["mode"] = "break_even"
            await query.message.reply_text(
                "⚖️ حاسبة نقطة التعادل\n\n"
                "أرسل البيانات بهذا الترتيب:\n"
                "التكاليف الثابتة , سعر البيع , التكلفة المتغيرة\n\n"
                "مثال: 50000 , 100 , 60"
            )

    except TelegramError as e:
        logging.error(f"خطأ في button_handler: {e}")

# ===== معالجة الأرقام =====
async def handle_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if not await is_subscribed(user_id, context):
            await ask_to_subscribe(update)
            return

        mode = context.user_data.get("mode")
        text = update.message.text.strip()

        if mode == "vat":
            try:
                amount = float(text.replace(",", ""))
                if amount <= 0:
                    raise ValueError
                result = calculate_vat(amount)
                await update.message.reply_text(
                    f"📊 نتيجة حساب الضريبة:\n\n"
                    f"💰 المبلغ الأصلي: {result['amount']:,.2f} جنيه\n"
                    f"🔢 الضريبة (14%): {result['vat']:,.2f} جنيه\n"
                    f"✅ الإجمالي: {result['total']:,.2f} جنيه\n\n"
                    f"💼 تريد نظام محاسبي كامل؟\n{AFFILIATE_LINK}",
                    reply_markup=back_button()
                )
            except (ValueError, TypeError):
                await update.message.reply_text(
                    "❌ أرسل رقماً صحيحاً أكبر من صفر\nمثال: 1000",
                    reply_markup=back_button()
                )

        elif mode == "depreciation":
            try:
                parts = [float(x.strip().replace(",", "")) for x in text.split(",")]
                if len(parts) != 3:
                    raise ValueError
                if parts[2] <= 0 or parts[0] <= 0:
                    raise ValueError
                result = calculate_depreciation(parts[0], parts[1], int(parts[2]))
                if "error" in result:
                    await update.message.reply_text(f"❌ {result['error']}", reply_markup=back_button())
                    return
                await update.message.reply_text(
                    f"📉 نتيجة حساب الاستهلاك:\n\n"
                    f"🏭 تكلفة الأصل: {result['cost']:,.2f} جنيه\n"
                    f"♻️ قيمة الخردة: {result['salvage']:,.2f} جنيه\n"
                    f"📅 عدد السنوات: {result['years']}\n"
                    f"📆 الاستهلاك السنوي: {result['annual_depreciation']:,.2f} جنيه\n"
                    f"🗓️ الاستهلاك الشهري: {result['monthly_depreciation']:,.2f} جنيه\n\n"
                    f"💼 تريد نظام محاسبي كامل؟\n{AFFILIATE_LINK}",
                    reply_markup=back_button()
                )
            except (ValueError, TypeError):
                await update.message.reply_text(
                    "❌ تأكد من إدخال 3 أرقام مفصولة بفواصل\n"
                    "مثال: 100000 , 10000 , 5",
                    reply_markup=back_button()
                )

        elif mode == "gross_profit":
            try:
                parts = [float(x.strip().replace(",", "")) for x in text.split(",")]
                if len(parts) != 2:
                    raise ValueError
                if parts[0] <= 0:
                    raise ValueError
                result = calculate_gross_profit(parts[0], parts[1])
                await update.message.reply_text(
                    f"📊 نتيجة حساب مجمل الربح:\n\n"
                    f"💵 الإيرادات: {result['revenue']:,.2f} جنيه\n"
                    f"🏭 تكلفة المبيعات: {result['cogs']:,.2f} جنيه\n"
                    f"✅ مجمل الربح: {result['gross_profit']:,.2f} جنيه\n"
                    f"📈 نسبة الهامش: {result['margin_percent']}%\n\n"
                    f"💼 تريد نظام محاسبي كامل؟\n{AFFILIATE_LINK}",
                    reply_markup=back_button()
                )
            except (ValueError, TypeError):
                await update.message.reply_text(
                    "❌ تأكد من إدخال رقمين مفصولين بفاصلة\n"
                    "مثال: 500000 , 300000",
                    reply_markup=back_button()
                )

        elif mode == "break_even":
            try:
                parts = [float(x.strip().replace(",", "")) for x in text.split(",")]
                if len(parts) != 3:
                    raise ValueError
                if any(x <= 0 for x in parts):
                    raise ValueError
                result = calculate_break_even(parts[0], parts[1], parts[2])
                if "error" in result:
                    await update.message.reply_text(f"❌ {result['error']}", reply_markup=back_button())
                    return
                await update.message.reply_text(
                    f"⚖️ نتيجة حساب نقطة التعادل:\n\n"
                    f"🏦 التكاليف الثابتة: {result['fixed_costs']:,.2f} جنيه\n"
                    f"💡 هامش المساهمة: {result['contribution_margin']:,.2f} جنيه\n"
                    f"📦 وحدات التعادل: {result['break_even_units']:,.2f} وحدة\n"
                    f"💰 إيراد التعادل: {result['break_even_revenue']:,.2f} جنيه\n\n"
                    f"💼 تريد نظام محاسبي كامل؟\n{AFFILIATE_LINK}",
                    reply_markup=back_button()
                )
            except (ValueError, TypeError):
                await update.message.reply_text(
                    "❌ تأكد من إدخال 3 أرقام مفصولة بفواصل\n"
                    "مثال: 50000 , 100 , 60",
                    reply_markup=back_button()
                )

        else:
            await update.message.reply_text(
                "اختر أداة من القائمة أولاً 👇",
                reply_markup=main_menu()
            )

    except TelegramError as e:
        logging.error(f"خطأ في handle_numbers: {e}")

# ===== معالجة الأخطاء العامة =====
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"خطأ عام: {context.error}")

# ===== تشغيل البوت =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_numbers))
    app.add_error_handler(error_handler)
    print("البوت يعمل الآن ✅")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
