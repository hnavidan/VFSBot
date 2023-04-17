import cv2
import re
import pytesseract
import telegram
from telegram.ext import Handler

pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

class WebError(Exception):
    pass

class Offline(Exception):
    pass

class AdminHandler(Handler):
    def __init__(self, admin_ids):
        super().__init__(self.cb)
        self.admin_ids = admin_ids

    def cb(self, update: telegram.Update, context):
        if not self.check_update(update):
            update.message.reply_text('unauthorized access!')

    def check_update(self, update: telegram.update.Update):
        if update.message is None or update.message.from_user.id not in self.admin_ids:
            return True

        return False

def break_captcha():
    img = cv2.imread('captcha.png')
    image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    se = cv2.getStructuringElement(cv2.MORPH_RECT, (8,8))
    bg = cv2.morphologyEx(image, cv2.MORPH_DILATE, se)
    out_gray = cv2.divide(image, bg, scale=255)
    out_binary = cv2.threshold(out_gray, 0, 255, cv2.THRESH_OTSU )[1]

    captcha = pytesseract.image_to_string(out_binary, config='--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNPQRSTUVWYZ')
    denoised_captcha =  re.sub('[\W_]+', '', captcha).strip()
    
    return denoised_captcha

class Message:
    def __init__(self, update, context, channel_id):
        self.update = update
        self.context = context
        self.channel_id = channel_id

    def send(self, text):
        print(text)
        self.update.message.reply_text(text)

    def broadcast(self, text):
        self.send(text)
        self.context.bot.send_message(chat_id=self.channel_id, text=text)
