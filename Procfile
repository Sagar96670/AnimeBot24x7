# सुनिश्चित करें कि सबसे ऊपर `import os` है (जो आपके पास है)
# सुनिश्चित करें कि सबसे ऊपर `import telebot` है)

from flask import Flask, request

# Flask ऐप बनाएं
app = Flask(__name__)

# Telegram से आने वाले Webhook रिक्वेस्ट को हैंडल करने के लिए
@app.route('/', methods=['POST'])
def webhook():
    # Telegram द्वारा भेजा गया JSON डेटा प्राप्त करें
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        # बॉट को अपडेट प्रोसेस करने के लिए दें
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        # अगर कोई और अनुरोध आता है
        return 'Bad Request', 403

# Google Cloud Run Environment Variable से Port लें
if __name__ == '__main__':
    # Google Cloud Run हमेशा $PORT पर सुनता है
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
