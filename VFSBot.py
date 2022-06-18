import time
import threading
from utils import *
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram.ext.updater import Updater
from telegram.ext.commandhandler import CommandHandler
from configparser import ConfigParser

class VFSBot:
    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
    
        self.url_be = config.get('VFS_BE', 'url')
        self.url_nl = config.get('VFS_NL', 'url')
        self.email_str = config.get('VFS_BE', 'email')
        self.pwd_str = config.get('VFS_BE', 'password')
        
        self.nl_name = config.get('VFS_NL', 'name')
        self.nl_surname = config.get('VFS_NL', 'surname')
        self.nl_phone = config.get('VFS_NL', 'phone')
        self.nl_email = config.get('VFS_NL', 'email')
        
        self.interval_be = config.getint('DEFAULT', 'interval_be')
        self.interval_nl = config.getint('DEFAULT', 'interval_nl')
        
        self.channel_id = config.get('TELEGRAM', 'channel_id')

        
        token = config.get('TELEGRAM', 'auth_token')
        admin_ids = list(map(int, config.get('TELEGRAM', 'admin_ids').split(" ")))

        updater = Updater(token, use_context=True)

        self.options = webdriver.ChromeOptions()
        self.options.add_argument("start-maximized")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        dp = updater.dispatcher

        dp.add_handler(AdminHandler(admin_ids))
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))
        dp.add_handler(CommandHandler("quit", self.quit))


        updater.start_polling()
        updater.idle()
    
    def login_be(self, update, context):
        self.browser_be.get((self.url_be))
        
        if "You are now in line." in self.browser_be.page_source:
           update.message.reply_text("You are now in queue.")
        
        WebDriverWait(self.browser_be, 600).until(
            EC.presence_of_element_located((By.NAME, 'EmailId')))
        
        self.browser_be.find_element(by=By.NAME, value='EmailId').send_keys(self.email_str)
        self.browser_be.find_element(by=By.NAME, value='Password').send_keys(self.pwd_str)
    
        
        captcha_img = self.browser_be.find_element(by=By.ID, value='CaptchaImage')
        
        self.captcha_filename = 'captcha.png'
        with open(self.captcha_filename, 'wb') as file:
            file.write(captcha_img.screenshot_as_png)

        captcha = break_captcha()
        
        self.browser_be.find_element(by=By.NAME, value='CaptchaInputText').send_keys(captcha)
        time.sleep(1)
        self.browser_be.find_element(by=By.ID, value='btnSubmit').click()
        
        if "Reschedule Appointment" in self.browser_be.page_source:
            update.message.reply_text("Successfully logged in!")
            while True:
                try:
                    self.check_appointment(update, context)
                except WebError:
                    update.message.reply_text("An error has occured.\nTrying again.")
                    raise WebError
                except Offline:
                    update.message.reply_text("Downloaded offline version. Trying again.")
                    continue
                except:
                    update.message.reply_text("An error has occured. \nTrying again.")
                    raise WebError
                time.sleep(self.interval_be)
        elif "Your account has been locked, please login after 2 minutes." in self.browser_be.page_source:
           update.message.reply_text("Account locked.\nPlease wait 2 minutes.")
           time.sleep(120)
           return
        elif "The verification words are incorrect." in self.browser_be.page_source:
           #update.message.reply_text("Incorrect captcha. \nTrying again.")
           return
        else:
            update.message.reply_text("An error has occured. \nTrying again.")
            #self.browser_be.find_element(by=By.XPATH, value='//*[@id="logoutForm"]/a').click()
            raise WebError

    
    def login_nl(self, update, context):
        self.browser_nl.get((self.url_nl))
        
        WebDriverWait(self.browser_nl, 600).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="plhMain_lnkSchApp"]')))
        
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_lnkSchApp"]').click()
        
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_cboVisaCategory"]').click()
        time.sleep(1)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_cboVisaCategory"]/option[9]').click()
        time.sleep(1)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_btnSubmit"]').click()

        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_repAppVisaDetails_cboTitle_0"]').click()
        time.sleep(1)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_repAppVisaDetails_cboTitle_0"]/option[2]').click()
        time.sleep(1)
        
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_repAppVisaDetails_tbxFName_0"]').send_keys(self.nl_name)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_repAppVisaDetails_tbxLName_0"]').send_keys(self.nl_surname)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_repAppVisaDetails_tbxContactNumber_0"]').send_keys(self.nl_phone)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_repAppVisaDetails_tbxEmailAddress_0"]').send_keys(self.nl_email)

                
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_cboConfirmation"]').click()
        time.sleep(1)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_cboConfirmation"]/option[2]').click()
        time.sleep(1)
        self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_btnSubmit"]').click()
        
        
        while True:
            WebDriverWait(self.browser_nl, 600).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="plhMain_lblSchAppDt"]')))
            
            if '<td class="OpenDateAllocated"' in self.browser_nl.page_source:
                day = self.browser_nl.find_element(by=By.XPATH, value='//td[@class="OpenDateAllocated"]').text
                month = self.browser_nl.find_element(by=By.XPATH, value='//*[@id="plhMain_cldAppointment"]/tbody/tr[1]/td/table/tbody/tr/td[2]').text
                
                new_date = day + ' ' + month
                
                records_nl = open("record_nl.txt", "r+")
                last_date = records_nl.readlines()[-1]
                
                if new_date != last_date and len(new_date) > 0:
                    context.bot.send_message(chat_id=self.channel_id,
                                             text=f"\U0001F1F3\U0001F1F1 Appointment available on {new_date}.")
                    records_nl.write('\n' + new_date)
                    records_nl.close()
            else:
                records_nl = open("record_nl.txt", "r+")
                last_date = records_nl.readlines()[-1]
                if last_date != '0':
                    context.bot.send_message(chat_id=self.channel_id,
                                             text="\U0001F1F3\U0001F1F1 There are no appointments available right now.")

                    records_nl.write('\n' + '0')
                    records_nl.close
            time.sleep(self.interval_nl)
            self.browser_nl.refresh()
            
    def login_helper(self, update, context, country):
        self.open_browser(country)      
        while True:
            try:
                if country == 'be':
                    self.login_be(update, context)
                elif country == 'nl':
                    self.login_nl(update, context)
            except:
                if country == 'be':
                    self.browser_be.quit()
                elif country == 'nl':
                    self.browser_nl.quit()
                self.open_browser(country)
                continue

    def open_browser(self, country):
        browser = webdriver.Chrome(options=self.options, 
                 executable_path=r'chromedriver.exe')
        
        stealth(browser,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        
        if country == 'be':
            self.browser_be = browser
        elif country == 'nl':
            self.browser_nl = browser
    
    
    def help(self, update, context):
        update.message.reply_text("This is a VFS appointment bot!\nPress /start to begin.")

    def start(self, update, context):
        try:
            self.browser_be.close()
        except:
                pass
            
        update.message.reply_text('Logging in...')
       
        self.thr_be = threading.Thread(target=self.login_helper, args=(update, context, 'be'))
        self.thr_nl = threading.Thread(target=self.login_helper, args=(update, context, 'nl'))

        self.thr_be.start()
        self.thr_nl.start()
    
    def quit(self, update, context):
        try:
            self.browser_be.quit()
            self.thr_be.terminate()
            self.thr_nl.terminate()
        except:
            pass
        update.message.reply_text("Quit successfully.")
    
    def check_errors(self):
        if "Server Error in '/Global-Appointment' Application." in self.browser_be.page_source:
            return True
        elif "Cloudflare" in self.browser_be.page_source:
            return True
        elif "Sorry, looks like you were going too fast." in self.browser_be.page_source:
            return True
        elif "Session expired." in self.browser_be.page_source:
            return True
        elif "Sorry, looks like you were going too fast." in self.browser_be.page_source:
            return True
        
    def check_offline(self):
        if "offline" in self.browser_be.page_source:
            return True
            
    def check_appointment(self, update, context):
        time.sleep(5)
    
        self.browser_be.find_element(by=By.XPATH, 
                                value='//*[@id="Accordion1"]/div/div[2]/div/ul/li[1]/a').click()
        if self.check_errors():
            raise WebError
        if self.check_offline():
            raise Offline
    
        WebDriverWait(self.browser_be, 100).until(EC.presence_of_element_located((
            By.XPATH, '//*[@id="LocationId"]')))
        
        self.browser_be.find_element(by=By.XPATH, value='//*[@id="LocationId"]').click()
        if self.check_errors():
             raise WebError
        time.sleep(5)
    
            
        self.browser_be.find_element(by=By.XPATH, value='//*[@id="LocationId"]/option[2]').click()
        if self.check_errors():
            raise WebError
    
        time.sleep(5)

            
        if "There are no open seats available for selected center - Belgium Long Term Visa Application Center-Tehran" in self.browser_be.page_source:
            #update.message.reply_text("There are no appointments available.")
            records = open("record_be.txt", "r+")
            last_date = records.readlines()[-1]
            
            if last_date != '0':
                context.bot.send_message(chat_id=self.channel_id,
                                         text="\U0001F1E7\U0001F1EA There are no appointments available right now.")
                records.write('\n' + '0')
                records.close
            return True
        
        else:
            select = Select(self.browser_be.find_element(by=By.XPATH, value='//*[@id="VisaCategoryId"]'))
            select.select_by_value('1314')
            
            WebDriverWait(self.browser_be, 100).until(EC.presence_of_element_located((
                By.XPATH, '//*[@id="dvEarliestDateLnk"]')))
    
            time.sleep(2)
            new_date = self.browser_be.find_element(by=By.XPATH, 
                           value='//*[@id="lblDate"]').get_attribute('innerHTML')
            
            records = open("record_be.txt", "r+")
            last_date = records.readlines()[-1]

            if new_date != last_date and len(new_date) > 0:
                context.bot.send_message(chat_id=self.channel_id,
                                         text=f"\U0001F1E7\U0001F1EA Appointment available on {new_date}.")
                records.write('\n' + new_date)
                records.close()
            #update.message.reply_text("Checked!", disable_notification=True)
            return True

                
if __name__ == '__main__':
    VFSbot = VFSBot()
