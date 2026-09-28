import time
import requests
import threading
import random
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# আপনার বটের টোকেন এবং স্টিকার ফাইল আইডি এখানে দিন
TOKEN = "8605922971:AAF8b0wQ0fVd4EF4G5nnB6INBvPKsTukBv8"
STICKER_FILE_ID = "YOUR_STICKER_FILE_ID" 
bot = TeleBot(TOKEN)

# API Endpoints
APIS = {
    '30S': 'https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json',
    '1M': 'https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json'
}

# Game Data & Auto-Running State
game_state = {
    '30S': {'period': 'SYNCING...', 'pred': '--', 'history': [], 'wins': 0, 'losses': 0, 'active': False, 'step': 0},
    '1M': {'period': 'SYNCING...', 'pred': '--', 'history': [], 'wins': 0, 'losses': 0, 'active': False, 'step': 0}
}

def get_custom_prediction(mode):
    """আপনার নির্ধারিত লজিক অনুযায়ী প্রেডিকশন নির্ধারণ করবে"""
    state = game_state[mode]
    
    if mode == '30S':
        # ৩০ সেকেন্ড লজিক: ২টি Big, ১টি Random, ৩টি Small
        sequence = ["BIG", "BIG", random.choice(["BIG", "SMALL"]), "SMALL", "SMALL", "SMALL"]
    else:
        # ১ মিনিট লজিক: ৩টি Small, ১টি Random, ৩টি Big
        sequence = ["SMALL", "SMALL", "SMALL", random.choice(["BIG", "SMALL"]), "BIG", "BIG", "BIG"]
    
    pred = sequence[state['step'] % len(sequence)]
    state['step'] += 1
    return pred

def background_fetcher(mode):
    while True:
        try:
            r = requests.get(f"{APIS[mode]}?t={int(time.time()*1000)}", timeout=5)
            d = r.json()
            list_data = d['data']['list']
            
            next_period = str(int(list_data[0]['issueNumber']) + 1)
            pred = get_custom_prediction(mode)
            
            state = game_state[mode]
            state['period'] = next_period[-4:]
            state['pred'] = pred
            
            if not any(h['period'] == next_period[-4:] for h in state['history']):
                state['history'].insert(0, {'period': next_period[-4:], 'pred': pred, 'res': 'WAITING', 'status': '⏳'})
                if len(state['history']) > 30:
                    state['history'].pop()
            
            actual_res = int(list_data[0]['number'])
            for h in state['history']:
                if h['period'] == list_data[0]['issueNumber'][-4:] and h['res'] == 'WAITING':
                    h['res'] = actual_res
                    
                    # Win এবং Loss ট্র্যাকিং
                    is_big_res = actual_res >= 5
                    is_big_pred = h['pred'] == 'BIG'
                    if is_big_pred == is_big_res:
                        h['status'] = '✅ WIN'
                        state['wins'] += 1
                    else:
                        h['status'] = '❌ LOSS'
                        state['losses'] += 1
        except Exception:
            pass
        time.sleep(2 if mode == '30S' else 5)

# ব্যাকগ্রাউন্ড থ্রেড রান করা
threading.Thread(target=background_fetcher, args=('30S',), daemon=True).start()
threading.Thread(target=background_fetcher, args=('1M',), daemon=True).start()

@bot.message_handler(commands=['start'])
def start_bot(message):
    # চ্যাটের নিচে রিপ্লাই কিবোর্ড বাটন তৈরি
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🚀 Start WinGo 30S"),
        KeyboardButton("🚀 Start WinGo 1M"),
        KeyboardButton("⏹️ Stop WinGo 30S"),
        KeyboardButton("⏹️ Stop WinGo 1M"),
        KeyboardButton("📊 30S History & Stats"),
        KeyboardButton("📊 1M History & Stats")
    )
    text = (
        "🤖 **ANTOR VIP PREDICTION BOT** 🤖\n\n"
        "Welcome Boss! Select a mode from the keyboard below. "
        "Auto predictions will run continuously based on exact timing!"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    
    try:
        bot.send_sticker(message.chat.id, STICKER_FILE_ID)
    except Exception:
        pass

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    chat_id = message.chat.id
    
    if text == "🚀 Start WinGo 30S" or text == "🚀 Start WinGo 1M":
        mode = "30S" if "30S" in text else "1M"
        
        if game_state[mode]['active']:
            bot.send_message(chat_id, f"⚠️ **ANTOR VIP ({mode})** is already running!", parse_mode="Markdown")
            return
            
        game_state[mode]['active'] = True
        bot.send_message(chat_id, f"✅ **ANTOR VIP ({mode})** auto prediction started successfully! It will run automatically.", parse_mode="Markdown")
        
        def send_auto_predictions():
            last_p = ""
            while game_state[mode]['active']:
                info = game_state[mode]
                if info['period'] != last_p:
                    last_p = info['period']
                    cycle = 30 if mode == "30S" else 60
                    remain = cycle - (int(time.time()) % cycle)
                    
                    # এখানে **ANTOR VIP** লেখাটি মোটা করা হয়েছে এবং কোন মার্কেটে সিগন্যাল দেওয়া হচ্ছে তা উল্লেখ করা হয়েছে
                    msg = (
                        f"⚡ **`ANTOR VIP` AUTO PREDICTION ({mode})** ⚡\n\n"
                        f"📌 Market: `WinGo {mode}`\n"
                        f"📌 Period: `{info['period']}`\n"
                        f"⏳ Countdown: `00:{remain:02d}` Sec\n"
                        f"🔮 Prediction: *{info['pred']}*\n\n"
                        f"Status: Live Running 🚀"
                    )
                    
                    try:
                        bot.send_sticker(chat_id, STICKER_FILE_ID)
                        bot.send_message(chat_id, msg, parse_mode="Markdown")
                    except Exception:
                        bot.send_message(chat_id, msg, parse_mode="Markdown")
                        
                time.sleep(2)
                
        threading.Thread(target=send_auto_predictions, daemon=True).start()

    elif text == "⏹️ Stop WinGo 30S" or text == "⏹️ Stop WinGo 1M":
        mode = "30S" if "30S" in text else "1M"
        game_state[mode]['active'] = False
        bot.send_message(chat_id, f"⏹️ **ANTOR VIP ({mode})** auto prediction has been stopped.", parse_mode="Markdown")
        
    elif text == "📊 30S History & Stats" or text == "📊 1M History & Stats":
        mode = "30S" if "30S" in text else "1M"
        state = game_state[mode]
        total = state['wins'] + state['losses']
        win_rate = (state['wins'] / total * 100) if total > 0 else 0
        
        hist_text = (
            f"📊 **`ANTOR VIP` WIN & LOSS STATS ({mode})** 📊\n"
            f"🎯 Total Wins: {state['wins']} | Losses: {state['losses']}\n"
            f"⭐ Accuracy Rate: `{win_rate:.1f}%`\n\n"
        )
        for h in state['history'][:12]:
            hist_text += f"Period: {h['period']} | Pred: {h['pred']} | Result: {h['res']} | {h['status']}\n"
        bot.send_message(chat_id, hist_text, parse_mode="Markdown")

if __name__ == "__main__":
    print("Antor Bot with Full Auto Loop is running...")
    bot.infinity_polling()
