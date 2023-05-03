import cv2
import re
import pytesseract
import telegram
import numpy as np
from telegram.ext import Handler

pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

class WebError(Exception):
    pass

class Offline(Exception):
    pass

class AdminHandler(Handler):
    def __init__(self, admin_ids):
        super().__init__(self.cb)
        self.admin_ids = admin_ids

    def cb(self, update: telegram.Update, context):
        update.message.reply_text('Unauthorized access!')

    def check_update(self, update: telegram.update.Update):
        if update.message is None or update.message.from_user.id not in self.admin_ids:
            return True

        return False

def break_captcha():
    image = cv2.imread("captcha.png")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.copyMakeBorder(image, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=[250])
    image = cv2.filter2D(image, -1, np.ones((4, 4), np.float32) / 16)

    se = cv2.getStructuringElement(cv2.MORPH_RECT, (8,8))
    bg = cv2.morphologyEx(image, cv2.MORPH_DILATE, se)
    image = cv2.divide(image, bg, scale=255)
    image = cv2.filter2D(image, -1, np.ones((3, 4), np.float32) / 12)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU)[1]

    image = cv2.copyMakeBorder(image, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=[250])

    captcha = pytesseract.image_to_string(image, config='--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNPQRSTUVWYZ')
    denoised_captcha =  re.sub('[\W_]+', '', captcha).strip()

    return denoised_captcha
