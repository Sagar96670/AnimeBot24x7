import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import string

# *******************************************************************
# ** 1. आपकी गुप्त जानकारियाँ **
# *******************************************************************

# @BotFather से मिला हुआ Token
BOT_TOKEN = "8211153494:AAG3LqSjffJEBTQPqhB54msBVMm7eHLP-QU" 

# *******************************************************************
# ** 2. डेटाबेस और मेमोरी सेटअप **
# *******************************************************************

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = 'bot_config.json'

# आपकी सभी सेटिंग्स (User ID, Channel IDs, Names) यहां डिफ़ॉल्ट रूप से सेट हैं।
DEFAULT_CONFIG = {
    "ADMIN_ID": 6295589267, # आपकी Telegram User ID
    "CHANNELS": {
        "ch1": {"id": -1003029714016, "name": "Nexus Prime Hindi"}, 
        "ch2": {"id": -1003188049987, "name": "AnimeVerseXIN Hindi"}
    },
    "FILE_DB": {} 
}
CONFIG = DEFAULT_CONFIG
USER_STATE = {}

def load_config():
    """डिस्क से कॉन्फ़िगरेशन लोड करता है।"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            global CONFIG
            loaded_data = json.load(f)
            CONFIG.update(loaded_data)
            
load_config()

def save_config():
    """कॉन्फ़िगरेशन को डिस्क में सेव करता है।"""
    with open(DB_FILE, 'w') as f:
        json.dump(CONFIG, f, indent=4)

# *******************************************************************
# ** 3. आवश्यक फ़ंक्शन्स **
# *******************************************************************

def is_admin(user_id):
    """जाँचता है कि यूज़र बॉट का एडमिन है या नहीं।"""
    return user_id == CONFIG["ADMIN_ID"]

def is_member(user_id, channel_id):
    """जाँचता है कि यूज़र दिए गए चैनल का सदस्य है या नहीं।"""
    if is_admin(user_id):
        return True
    try:
        member = bot.get_chat_member(channel_id, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

def get_subscribe_markup(channel_id):
    """जॉइन बटन और Try Again बटन के लिए Inline कीबोर्ड बनाता है।"""
    markup = InlineKeyboardMarkup()
    channel_link = f"https://t.me/c/{str(channel_id)[4:]}" 
    markup.add(InlineKeyboardButton("✅ चैनल जॉइन करें", url=channel_link))
    markup.add(InlineKeyboardButton("🔄 कोशिश करें", callback_data="check_again"))
    return markup

def generate_link_key():
    """एक यूनिक रैंडम लिंक कुंजी बनाता है।"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# *******************************************************************
# ** 4. डायनामिक सेटिंग्स मेनू (/settings) **
# *******************************************************************

@bot.message_handler(commands=['settings'])
def show_settings(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "🛑 आप एडमिन नहीं हैं।")

    markup = InlineKeyboardMarkup()
    for key, data in CONFIG["CHANNELS"].items():
        markup.add(InlineKeyboardButton(f"🔗 {data['name']} (ID: {data['id']})", callback_data=f'set_ch_id_{key}'))
    
    markup.add(InlineKeyboardButton(f"👤 Admin ID: {CONFIG['ADMIN_ID']}", callback_data='set_admin_id'))
    
    bot.reply_to(message, "⚙️ **सेटिंग्स मेनू**\n"
                          "चैनल ID/नाम बदलने के लिए बटन दबाएँ।", 
                          reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_ch_id_'))
def handle_channel_setting(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ एक्सेस अस्वीकृत।")
        
    channel_key = call.data.split('_')[-1]
    
    USER_STATE[user_id] = {'step': 'waiting_for_channel_forward', 'channel_key': channel_key}
    
    bot.edit_message_text(f"✅ सेट: {CONFIG['CHANNELS'][channel_key]['name']}\n"
                          "अब **अपने चैनल से कोई भी एक मैसेज** यहाँ फ़ॉरवर्ड करें।", 
                          call.message.chat.id, 
                          call.message.message_id)
    
    bot.answer_callback_query(call.id, "मैसेज फ़ॉरवर्ड करें...")

@bot.message_handler(content_types=['forward'], func=lambda message: is_admin(message.from_user.id) and USER_STATE.get(message.from_user.id, {}).get('step') == 'waiting_for_channel_forward')
def update_channel_id(message):
    user_id = message.from_user.id
    state = USER_STATE.pop(user_id, None)
    
    if message.forward_from_chat and state:
        new_channel_id = message.forward_from_chat.id
        channel_key = state['channel_key']
        
        CONFIG["CHANNELS"][channel_key]['id'] = new_channel_id
        CONFIG["CHANNELS"][channel_key]['name'] = message.forward_from_chat.title
        save_config()
        
        bot.reply_to(message, 
                     f"🎉 **सफलतापूर्वक अपडेट किया गया!**\n"
                     f"चैनल: {CONFIG['CHANNELS'][channel_key]['name']} (ID: `{new_channel_id}`)")
    else:
        bot.reply_to(message, "❌ त्रुटि: कृपया एक वैध चैनल मैसेज फ़ॉरवर्ड करें।")

# *******************************************************************
# ** 5. कंडीशनल फ़ाइल स्टोरिंग लॉजिक (/store_new) **
# *******************************************************************

@bot.message_handler(commands=['store_new'])
def start_store_new(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "🛑 यह कमांड केवल एडमिन के लिए है।")

    markup = InlineKeyboardMarkup()
    for key, data in CONFIG["CHANNELS"].items():
        markup.add(InlineKeyboardButton(f"🔗 {data['name']} चाहिए", callback_data=f'set_store_ch_{key}'))
    
    msg = bot.reply_to(message, "फ़ाइल/बैच एक्सेस के लिए अनिवार्य **एक** चैनल चुनें।", reply_markup=markup)
    
    USER_STATE[message.from_user.id] = {'step': 'waiting_for_store_channel_choice', 'msg_id': msg.message_id}

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_store_ch_'))
def set_channel_for_batch(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ एक्सेस अस्वीकृत।")

    channel_key = call.data.split('_')[-1]
    USER_STATE[user_id]['channel_key'] = channel_key
    USER_STATE[user_id]['step'] = 'waiting_for_first_message'
    
    bot.edit_message_text(f"✅ सेट: {CONFIG['CHANNELS'][channel_key]['name']}।\n"
                          "अब **बैच का पहला मैसेज** या **सिंगल फ़ाइल** को फ़ॉरवर्ड करें।", 
                          call.message.chat.id, 
                          call.message.message_id)
    bot.answer_callback_query(call.id, "पहला मैसेज फ़ॉरवर्ड करें...")

@bot.message_handler(content_types=['forward'], func=lambda message: is_admin(message.from_user.id) and USER_STATE.get(message.from_user.id, {}).get('step') == 'waiting_for_first_message')
def handle_batch_forward_new(message):
    user_id = message.from_user.id
    if not is_admin(user_id): return

    state = USER_STATE.pop(user_id, None)

    if message.forward_from_chat and message.forward_from_message_id and state:
        
        channel_key = state['channel_key']
        required_channel_id = CONFIG["CHANNELS"][channel_key]['id']
            
        file_identifier = f"batch_{message.forward_from_chat.id}_{message.forward_from_message_id}"
        link_key = generate_link_key()

        CONFIG["FILE_DB"][link_key] = {'identifier': file_identifier, 'req_ch_id': required_channel_id}
        save_config()
        
        share_link = f"https://t.me/{bot.get_me().username}?start={link_key}"
        bot.reply_to(message, 
                     f"🎉 **फ़ाइल/बैच स्टोर हो गया!**\n"
                     f"अनिवार्य चैनल: {CONFIG['CHANNELS'][channel_key]['name']}\n"
                     f"शेयर करने योग्य लिंक:\n`{share_link}`")
    else:
        bot.reply_to(message, "❌ कृपया **फ़ॉरवर्ड टैग** के साथ मैसेज फ़ॉरवर्ड करें।")


# *******************************************************************
# ** 6. यूज़र एक्सेस लॉजिक **
# *******************************************************************

@bot.message_handler(commands=['start'])
def handle_start(message):
    if len(message.text.split()) > 1:
        link_key = message.text.split()[1]
        
        if link_key in CONFIG["FILE_DB"]:
            file_data = CONFIG["FILE_DB"][link_key]
            identifier = file_data['identifier']
            required_channel_id = file_data['req_ch_id']
            
            # ** कंडीशनल फोर्स सब चेक **
            if is_member(message.from_user.id, required_channel_id):
                
                try:
                    chat_id, message_id = identifier.split('_')[1:]
                    bot.copy_message(message.chat.id, chat_id, message_id)
                    bot.send_message(message.chat.id, "🥳 आपकी फ़ाइल यहाँ है।")

                except Exception:
                    bot.send_message(message.chat.id, "❌ फ़ाइल भेजने में त्रुटि हुई। सुनिश्चित करें कि बॉट सोर्स चैनल में एडमिन है।")
            else:
                # यूज़र को केवल वही चैनल जॉइन करने को कहना जिसकी ज़रूरत है
                markup = get_subscribe_markup(required_channel_id)
                
                required_channel_name = next((data['name'] for data in CONFIG["CHANNELS"].values() if data['id'] == required_channel_id), "आवश्यक चैनल")

                bot.send_message(message.chat.id, 
                                 f"🛑 **फ़ाइल एक्सेस नहीं कर सकते।**\n"
                                 f"कृपया पहले **{required_channel_name}** जॉइन करें।", 
                                 reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ यह लिंक अब मान्य नहीं है।")

    else:
        bot.send_message(message.chat.id, "नमस्ते! फ़ाइलें एक्सेस करने के लिए एक शेयर करने योग्य लिंक का उपयोग करें।")

@bot.callback_query_handler(func=lambda call: call.data == "check_again")
def check_membership_callback(call):
    bot.answer_callback_query(call.id, "सदस्यता की जाँच हो रही है...")
    bot.send_message(call.message.chat.id, "कृपया फ़ाइल लिंक को फिर से दबाएँ या /start पर वापस जाएँ।")


# *******************************************************************
# ** 7. बॉट को चलाना **
# *******************************************************************

print("बॉट शुरू हो रहा है...")
bot.polling(none_stop=True)
