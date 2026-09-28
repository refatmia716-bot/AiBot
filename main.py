import logging
import os
import re
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from groq import Groq
from gtts import gTTS

# সরাসরি পোর্টের সাথে ফ্লাস্ক সার্ভার সেটআপ (রেন্ডার যাতে সাথে সাথে পোর্ট পেয়ে যায়)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live!"

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# আপনার টোকেন এবং এপিআই কি
TELEGRAM_BOT_TOKEN = "8971767093:AAERqhkpcP3bCsOdl-e8NRJAd-b0x0igPUA"
GROQ_API_KEY = "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"

# Groq ক্লায়েন্ট ইনিশিয়ালাইজ করুন
client = Groq(api_key=GROQ_API_KEY)

def remove_emojis(text):
    emoji_pattern = re.compile(
        r"["
        r"\U0001f1e0-\U0001f1ff"
        r"\U0001f300-\U0001f5ff"
        r"\U0001f600-\U0001f64f"
        r"\U0001f680-\U0001f6ff"
        r"\U0001f700-\U0001f77f"
        r"\U0001f780-\U0001f7ff"
        r"\U0001f800-\U0001f8ff"
        r"\U0001f900-\U0001f9ff"
        r"\U0001fa00-\U0001fa6f"
        r"\U0001fa70-\U0001faff"
        r"\U00020000-\U0002a6ff"
        r"\U0002a700-\U0002b73f"
        r"\U0002b740-\U0002b81f"
        r"\U0002b820-\U0002ceaf"
        r"\U0002f800-\U0002fa1f"
        r"\u0023-\u0039"
        r"\u00a9\u00ae\u203c\u2045\u20cb\u2122\u2139\u3030"
        r"\u2150-\u2199\u21a0-\u21f9\u2200-\u22ff"
        r"\u2300-\u23ff\u2400-\u243f\u2440-\u244a\u2460-\u24ff"
        r"\u2500-\u257f\u2580-\u259f\u25a0-\u25ff"
        r"\u2600-\u26ff\u2700-\u27bf"
        r"\u2800-\u28ff"
        r"\u2900-\u297f\u2a00-\u2aff\u2b00-\u2bff"
        r"\u3200-\u32ff\u3300-\u33ff"
        r"]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text_clean = "স্বাগতম! আমি আপনার ডেডিকেটেড এআই অ্যাসিস্ট্যান্ট। কোডিং বা যেকোনো সমস্যায় আমাকে নির্দ্বিধায় বলতে পারেন। আজ আপনাকে কীভাবে সাহায্য করতে পারি?"
    
    welcome_message = (
        "<b>🤖 AI Assistant</b>\n\n"
        "👋 স্বাগতম! আমি আপনার ডেডিকেটেড এআই অ্যাসিস্ট্যান্ট।\n\n"
        "💻 কোডিং, 🛠️ টেকনিক্যাল সমস্যা সমাধান কিংবা 🧠 যেকোনো প্রশ্ন—যেকোনো প্রয়োজনে আমাকে নির্দ্বিধায় বলতে পারেন। বলুন, আজ আপনাকে কীভাবে সাহায্য করতে পারি? 🚀✨"
    )
    
    await update.message.reply_text(welcome_message, parse_mode="HTML")
    
    try:
        tts = gTTS(text=welcome_text_clean, lang='bn', slow=False)
        voice_path = "start_audio.ogg"
        tts.save(voice_path)
        
        with open(voice_path, 'rb') as audio:
            await update.message.reply_voice(voice=audio)
            
        if os.path.exists(voice_path):
            os.remove(voice_path)
    except Exception as e:
        logging.info(f"Voice error on start: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(1.5)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an advanced, smart, and helpful AI assistant. Always use relevant and attractive emojis throughout your responses based on the context of the conversation. If anyone asks who created you, who made you, or about your creator, always proudly and respectfully say: 'আমাকে অন্তর তৈরি করেছে। এই বোটটি বানানোর জন্য উনি অনেক পরিশ্রম ও কষ্ট করেছেন। 💻🔥' Do not add random descriptions of smiling, facial expressions, or laughing. Answer accurately and directly, provide clean code when requested, and handle user queries regardless of casing."
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        
        raw_response = chat_completion.choices[0].message.content
        
        if len(raw_response) > 4000:
            raw_response = raw_response[:4000] + "\n\n*(উত্তরটি দীর্ঘ হওয়ায় কিছুটা সংক্ষিপ্ত করা হলো)*"

        bot_response = f"<b>🤖 AI Assistant</b>\n\n{raw_response}"
        await update.message.reply_text(bot_response, parse_mode="HTML")
        
        if len(user_message.split()) <= 10 and len(raw_response) < 300:
            clean_voice_text = remove_emojis(raw_response)
            tts = gTTS(text=clean_voice_text, lang='bn', slow=False)
            voice_path = "response_audio.ogg"
            tts.save(voice_path)
            
            with open(voice_path, 'rb') as audio:
                await update.message.reply_voice(voice=audio)
                
            if os.path.exists(voice_path):
                os.remove(voice_path)
            
    except Exception as e:
        error_reply = "<b>🤖 AI Assistant</b>\n\nআরে ভাই একটু ফুরসত দাও! 🛜 নেটওয়ার্ক স্লো থাকার কারণে মাথা ঘুরে গেছে, একটু পরে আবার ট্রাই করো তো দেখি! 😅"
        await update.message.reply_text(error_reply, parse_mode="HTML")

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # পোলিং স্টার্ট করার আগে ফ্লাস্ক পোর্ট বাইন্ড করার জন্য রেন্ডারের পোর্ট ভেরিয়েবল চেক করবে
    # তবে যেহেতু পাইথন বট সাধারণত একসাথে ফ্লাস্ক এবং পোলিং দুটো লুপ একসাথে চালাতে গিটহাবে ঝামেলা করে, 
    # তাই রেন্ডারে ফ্রি ওয়েব সার্ভিসের জন্য নিচের কমান্ডটি ব্যবহার করতে হবে: gunicorn main:app
    application.run_polling()

if __name__ == '__main__':
    main()
