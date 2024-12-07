import asyncio
import undetected_chromedriver as uc
from utils import *
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler
from configparser import ConfigParser

class VFSBot:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('config.ini')
    
        self.url = self.config.get('VFS', 'url')
        self.email_str = self.config.get('VFS', 'email')
        self.pwd_str = self.config.get('VFS', 'password')
        self.interval = self.config.getint('VFS', 'interval')
        self.channel_id = self.config.get('TELEGRAM', 'channel_id')
        token = self.config.get('TELEGRAM', 'auth_token')
        admin_ids = list(map(int, self.config.get('TELEGRAM', 'admin_ids').split(" ")))
        self.started = False
        self.admin_handler = AdminHandler(admin_ids)

        self.app = ApplicationBuilder().token(token).build()

        self.app.add_handler(MessageHandler(
                self.admin_handler.filter_admin(),
                self.admin_handler.unauthorized_access))
        
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("quit", self.quit))
        self.app.add_handler(CommandHandler("setting", self.setting))

        
        self.app.run_polling()
    
    async def login(self, update: Update, context: CallbackContext):
        self.browser.get((self.url))
        
        # await asyncio.sleep(500) # For debugging purposes
        if "You are now in line." in self.browser.page_source:
           update.message.reply_text("You are now in queue.")
        
        WebDriverWait(self.browser, 600).until(EC.presence_of_element_located((By.NAME, 'EmailId')))
        await asyncio.sleep(1)

        self.browser.find_element(by=By.NAME, value='EmailId').send_keys(self.email_str)
        self.browser.find_element(by=By.NAME, value='Password').send_keys(self.pwd_str)
    
        
        #update.message.reply_text("Sending Captcha...")

        captcha_img = self.browser.find_element(by=By.ID, value='CaptchaImage')
        
        self.captcha_filename = 'captcha.png'
        with open(self.captcha_filename, 'wb') as file:
            file.write(captcha_img.screenshot_as_png)

        captcha = break_captcha()
        
        self.browser.find_element(by=By.NAME, value='CaptchaInputText').send_keys(captcha)
        await asyncio.sleep(1)
        self.browser.find_element(by=By.ID, value='btnSubmit').click()
        
        if "Reschedule Appointment" in self.browser.page_source:
            update.message.reply_text("Successfully logged in!")
            while True:
                try:
                    await self.check_appointment(update, context)
                except WebError:
                    update.message.reply_text("An WebError has occured.\nTrying again.")
                    raise WebError
                except Offline:
                    update.message.reply_text("Downloaded offline version. \nTrying again.")
                    continue
                except Exception as e:
                    update.message.reply_text("An error has occured: " + e + "\nTrying again.")
                    raise WebError
                await asyncio.sleep(self.interval)
        elif "Your account has been locked, please login after 2 minutes." in self.browser.page_source:
           update.message.reply_text("Account locked.\nPlease wait 2 minutes.")
           await asyncio.sleep(120)
           return
        elif "The verification words are incorrect." in self.browser.page_source:
           #update.message.reply_text("Incorrect captcha. \nTrying again.")
           return
        elif "You are being rate limited" in self.browser.page_source:
            update.message.reply_text("Rate Limited. \nPlease wait 5 minutes.")
            await asyncio.sleep(300)
            return
        else:
            update.message.reply_text("An unknown error has occured. \nTrying again.")
            #self.browser.find_element(by=By.XPATH, value='//*[@id="logoutForm"]/a').click()
            raise WebError

    
    async def login_helper(self, update, context):
        self.browser = uc.Chrome(options=self.options)

        while True and self.started:
            try:
                await self.login(update, context)
            except Exception as e:
                print(e)
                continue
                
    async def help(self, update: Update, context: CallbackContext):
        await update.message.reply_text("This is a VFS appointment bot!\nPress /start to begin.")

    async def start(self, update: Update, context: CallbackContext):
        self.options = uc.ChromeOptions()
        self.options.add_argument('--disable-gpu')
        #Uncomment the following line to run headless
        #self.options.add_argument('--headless=new')
        
        if hasattr(self, 'thr') and self.thr is not None:
            await update.message.reply_text("Bot is already running.")
            return

        self.started = True
        self.thr = asyncio.create_task(self.login_helper(update, context))
        await update.message.reply_text("Bot started successfully.")

    
    async def quit(self, update: Update, context: CallbackContext):
        if not self.started:
            await update.message.reply_text("Cannot quit. Bot is not running.")
            return

        try:
            self.browser.quit()
            self.thr = None
            self.started = False
            await update.message.reply_text("Quit successfully.")
        except:
            await update.message.reply_text("Quit unsuccessful.")
            pass
        
    async def setting(self, update: Update, context: CallbackContext):
        if not context.args or len(context.args) < 3:
            await update.message.reply_text("Usage: /setting <section> <key> <value>\nExample: /setting VFS url https://example.com")
            return
       
        section, key, value = context.args[0], context.args[1], ' '.join(context.args[2:])
        
        if not self.config.has_section(section):
            await update.message.reply_text(f"Section '{section}' does not exist in the config file.")
            return

        if not self.config.has_option(section, key):
            await update.message.reply_text(f"Key '{key}' does not exist in section '{section}'.")
            return
       
           # Prevent changing the auth token
        if section == 'TELEGRAM' and key == 'auth_token':
            await update.message.reply_text("Cannot change the auth token.")
            return
    
        self.config.set(section, key, value)
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

        if section == 'VFS':
            if key == 'url':
                self.url = value
            elif key == 'email':
                self.email_str = value
            elif key == 'password':
                self.pwd_str = value
        elif section == 'DEFAULT' and key == 'interval':
            self.interval = int(value)
        elif section == 'TELEGRAM' and key == 'channel_id':
            self.channel_id = value
        
        await update.message.reply_text(f"Configuration updated: [{section}] {key} = {value}")

    def check_errors(self):
        if "Server Error in '/Global-Appointment' Application." in self.browser.page_source:
            return True
        elif "Cloudflare" in self.browser.page_source:
            return True
        elif "Sorry, looks like you were going too fast." in self.browser.page_source:
            return True
        elif "Session expired." in self.browser.page_source:
            return True
        elif "Sorry, looks like you were going too fast." in self.browser.page_source:
            return True
        elif "Sorry, Something has gone" in self.browser.page_source:
            return True
        
    def check_offline(self):
        if "offline" in self.browser.page_source:
            return True
            
    async def check_appointment(self, update, context):
        await asyncio.sleep(5)
    
        self.browser.find_element(by=By.XPATH, 
                                value='//*[@id="Accordion1"]/div/div[2]/div/ul/li[1]/a').click()
        if self.check_errors():
            raise WebError
        if self.check_offline():
            raise Offline
    
        WebDriverWait(self.browser, 100).until(EC.presence_of_element_located((
            By.XPATH, '//*[@id="LocationId"]')))
        
        self.browser.find_element(by=By.XPATH, value='//*[@id="LocationId"]').click()
        if self.check_errors():
             raise WebError
        await asyncio.sleep(3)
    
            
        self.browser.find_element(by=By.XPATH, value='//*[@id="LocationId"]/option[2]').click()
        if self.check_errors():
            raise WebError
    
        await asyncio.sleep(3)

            
        if "There are no open seats available for selected center - Belgium Long Term Visa Application Center-Tehran" in self.browser.page_source:
            #update.message.reply_text("There are no appointments available.")
            records = open("record.txt", "r+")
            last_date = records.readlines()[-1]
            
            if last_date != '0':
                await context.bot.send_message(chat_id=self.channel_id,
                                         text="There are no appointments available right now.")
                records.write('\n' + '0')
                records.close
        else:
            select = Select(self.browser.find_element(by=By.XPATH, value='//*[@id="VisaCategoryId"]'))
            select.select_by_value('1314')
            
            WebDriverWait(self.browser, 100).until(EC.presence_of_element_located((
                By.XPATH, '//*[@id="dvEarliestDateLnk"]')))
    
            await asyncio.sleep(2)
            new_date = self.browser.find_element(by=By.XPATH, 
                           value='//*[@id="lblDate"]').get_attribute('innerHTML')
            
            records = open("record.txt", "r+")
            last_date = records.readlines()[-1]

            if new_date != last_date and len(new_date) > 0:
                await context.bot.send_message(chat_id=self.channel_id,
                                         text=f"Appointment available on {new_date}.")
                records.write('\n' + new_date)
                records.close()
        #Uncomment if you want the bot to notify everytime it checks appointments.
        #update.message.reply_text("Checked!", disable_notification=True)
        return True

if __name__ == '__main__':
    VFSbot = VFSBot()