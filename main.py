import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from gtts import gTTS

# ফ্লাস্ক অ্যাপ চালু করা (রেন্ডার সার্ভিসের জন্য)
app = Flask(__name__)

# আপনার দেওয়া টোকেন এবং এপিআই কি সরাসরি এখানে বসানো হলো
TOKEN = "8971767093:AAERqhkpcP3bCsOdle8NRJAd-b0x0igPUA"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# টেলিগ্রাম বট অ্যাপ্লিকেশন তৈরি
application = Application.builder().token(TOKEN).build()

@app.route('/')
def home():
    return "Bot is active and running via Webhook!"

# স্টার্ট কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = "স্বাগতম! আমি আপনার ডেডিকেটেড এআই সহকারী। কোডিং বা যেকোনো সমস্যায় আমাকে নির্দ্বিধায় বলতে পারেন। আমি আপনাকে কীভাবে সাহায্য করতে পারি? 🚀"
    await update.message.reply_text(welcome_message, parse_mode="HTML")

# মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    try:
        chat_completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": user_text}]
        )
        response_text = chat_completion.choices[0].message.content
        await update.message.reply_text(response_text)
    except Exception as e:
        await update.message.reply_text(f"দুঃখিত, একটি সমস্যা হয়েছে: {str(e)}")

# হ্যান্ডলারগুলো যোগ করা
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# রেন্ডার থেকে ওয়েবহুক রিসিভ করার রুট
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "ok"

if __name__ == '__main__':
    # বটের জন্য ওয়েবহুক সেট করা (আপনার রেন্ডার ইউআরএল এখানে স্বয়ংক্রিয়ভাবে কাজ করবে)
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") 
    if RENDER_URL:
        application.bot.set_webhook(f"{RENDER_URL}/{TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
