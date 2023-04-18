import subprocess
import sys
import threading
import time
import undetected_chromedriver as uc
from configparser import ConfigParser
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram.ext.updater import Updater
from telegram.ext.commandhandler import CommandHandler
from utils import *

class VFSBot:
    def __init__(self):
        # If you have a mac, this line keep your mac awake, otherwise comment it out.
        caffeinate_process = subprocess.Popen(["caffeinate"])

        self.started = self.logged_in = False

        config = ConfigParser()
        config.read('config.ini')
    
        self.url = config.get('VFS', 'url')
        self.email_str = config.get('VFS', 'email')
        self.pwd_str = config.get('VFS', 'password')
        self.interval = config.getint('DEFAULT', 'interval')
        self.channel_id = config.get('TELEGRAM', 'channel_id')
        token = config.get('TELEGRAM', 'auth_token')
        admin_ids = list(map(int, config.get('TELEGRAM', 'admin_ids').split(" ")))

        updater = Updater(token, use_context=True)

        dp = updater.dispatcher

        dp.add_handler(AdminHandler(admin_ids))
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))
        dp.add_handler(CommandHandler("quit", self.quit))
        dp.add_handler(CommandHandler("check", self.check_appointment))

        updater.start_polling()
        updater.idle()
    
    def fill_login_form(self, update, context):
        WebDriverWait(self.browser, 600).until(EC.presence_of_element_located((By.NAME, 'EmailId')))

        emailInput = self.browser.find_element(by=By.NAME, value='EmailId')
        if emailInput.get_attribute('value') != self.email_str:
            emailInput.clear()
            emailInput.send_keys(self.email_str)

        self.browser.find_element(by=By.NAME, value='Password').send_keys(self.pwd_str)

        print("sending captcha")

        captcha_img = self.browser.find_element(by=By.ID, value='CaptchaImage')
        
        self.captcha_filename = 'captcha.png'
        with open(self.captcha_filename, 'wb') as file:
            file.write(captcha_img.screenshot_as_png)

        captcha = break_captcha()
        
        self.browser.find_element(by=By.NAME, value='CaptchaInputText').send_keys(captcha)
        time.sleep(1)

        self.browser.find_element(by=By.ID, value='btnSubmit').click()

    def login(self, update, context):
        self.message.send('Logging in.')
        self.logged_in = False
        self.browser.get((self.url))

        if "You are now in line." in self.browser.page_source:
           self.message.send("You are now in queue.")
    
        self.fill_login_form(update, context)
        while "Les mots de vérification sont erronés" in self.browser.page_source:
            # self.message.send("Incorrect captcha. \nTrying again.")
            self.fill_login_form(update, context)

        if "Prendre un rendez-vous" in self.browser.page_source:
            self.message.send("logged in ✔")
            self.logged_in = True
            while True:
                try:
                    self.check_appointment(update, context)
                except WebError:
                    self.message.send("An WebError has occured.\nTrying again.")
                    raise WebError
                except Offline:
                    self.message.send("Downloaded offline version.\nTrying again.")
                    continue
                except Exception as e:
                    self.message.broadcast("An error has occured: " + e + "\nTrying again.") # type: ignore
                    raise WebError
                time.sleep(self.interval)
        elif "Votre compte a été verrouillé, veuillez vous connecter après 2 minutes." in self.browser.page_source:
           self.message.send("Account locked.\nPlease wait 2 minutes.")
           time.sleep(120)
           return
        else:
            self.message.send("An unknown error has occured.\nTrying again.")
            raise WebError
   
    def login_helper(self, update, context):
        options = uc.ChromeOptions()
        if len(sys.argv) == 1 or sys.argv[1] != "--no-headless":
            options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        # uncomment to set english language or see chrome preferences
        # options.add_argument('--lang=en')

        self.browser = uc.Chrome(
            options=options
        )

        while True and self.started:
            try:
                self.login(update, context)
            except:
                continue

    def help(self, update, context):
        self.message.send("This is a VFS appointment bot!\nPress /start to begin.\nPress /quit to quit.\nPress /check to check for appointments.")

    def start(self, update, context):
        if hasattr(self, 'thr') and self.thr is not None:
            self.message.send("Bot is already running.")
            return

        if not hasattr(self, 'message') or type(self.message) is not Message:
            self.message = Message(update, context, self.channel_id)
        
        self.thr = threading.Thread(target=self.login_helper, args=(update, context))
        self.thr.start()
        self.started = True

    def quit(self, update, context):
        try:
            self.browser.quit()
            self.started = False
            # self.thr.join()
            self.thr = None
        except:
            self.quit(update, context)
            pass

        self.message.send("Quit successfully.")
    
    def check_errors(self):
        if "Server Error in '/Global-Appointment' Application." in self.browser.page_source:
            self.message.send("Server Error in '/Global-Appointment' Application.")
            return True
        elif "Cloudflare" in self.browser.page_source:
            self.message.send("Cloudflare")
            return True
        elif "Sorry, looks like you were going too fast." in self.browser.page_source:
            self.message.send("Sorry, looks like you were going too fast.")
            return True
        elif "Session expired." in self.browser.page_source:
            self.message.send("Session expired.")
            return True
        elif "Sorry, looks like you were going too fast." in self.browser.page_source:
            self.message.send("Sorry, looks like you were going too fast.")
            return True
        
    def check_offline(self):
        if "offline" in self.browser.page_source:
            return True

    def check_appointment(self, update, context):
        if not self.logged_in:
            self.message.send("Not logged in.")
            return

        self.go_to_appointment(update, context)

        self.message.send("New appointment check.")

        # see ajaxRequest.js to set another country or comment out this line to ignore
        self.ajax_appointment_request(update, context)

        time.sleep(3)

        return self.visual_appointment_request(update, context)

    def go_to_appointment(self, update, context):
        time.sleep(1)
    
        self.browser.find_element(by=By.XPATH, 
                                value='//*[@id="Accordion1"]/div/div[2]/div/ul/li[1]/a').click()
        if self.check_errors():
            raise WebError
        if self.check_offline():
            raise Offline
    
        WebDriverWait(self.browser, 100).until(EC.presence_of_element_located((
            By.XPATH, '//*[@id="LocationId"]')))

    def ajax_appointment_request(self, update, context):
        with open('ajaxRequest.js', 'r') as file:
            js = file.read()

        time.sleep(1)

        response = self.browser.execute_script(js)

        if response != "":
            self.message.send(response)
        else:
            self.message.broadcast("Possible appointment found 🤞🏽")

    def visual_appointment_request(self, update, context):
        select = Select(self.browser.find_element(by=By.XPATH, value='//*[@id="LocationId"]'))
        select.select_by_index(2)

        if self.check_errors():
            raise WebError
        
        time.sleep(2)

        locationError = self.browser.find_element(by=By.XPATH, value='//*[@id="LocationError"]').text

        if locationError != "" and "Rabat" in locationError:
            self.message.send("There are no appointments available ❗️")

            records = open("record.txt", "r+")
            last_date = records.readlines()[-1]
            
            if last_date != '0':
                self.message.broadcast("There are no appointments available right now ❗️")
                records.write('\n' + '0')
                records.close()
            return True
        else:
            time.sleep(2)

            if not self.browser.find_elements(by=By.XPATH, value='//*[@id="VisaCategoryId"]') or not self.browser.find_element(by=By.XPATH, value='//*[@id="VisaCategoryId"]').is_enabled():
                self.message.send("False alarm, no appointment ❗️")
                return True

            self.message.broadcast("Selecting Visa Type 🤞🏽")
            
            Select(self.browser.find_element(by=By.XPATH, value='//*[@id="VisaCategoryId"]')).select_by_value('684')

            time.sleep(2)
            subCategoryError = self.browser.find_element(by=By.XPATH, value='//*[@id="SubCategoryError"]').text

            if subCategoryError != "" and "Aucun créneau disponible" in subCategoryError:
                self.message.send("There are no appointments available for this type of visa 😔")
                return True
            
            WebDriverWait(self.browser, 100).until(EC.presence_of_element_located((
                By.XPATH, '//*[@id="dvEarliestDateLnk"]')))
    
            time.sleep(1)
            new_date = self.browser.find_element(by=By.XPATH, 
                           value='//*[@id="lblDate"]').get_attribute('innerHTML')
            
            records = open("record.txt", "r+")
            last_date = records.readlines()[-1]

            if new_date != last_date and len(new_date) > 0:
                self.message.broadcast(f"Appointment available on {new_date}.")
                records.write('\n' + new_date)
                records.close()
            return True
                
if __name__ == '__main__':
    VFSbot = VFSBot()
