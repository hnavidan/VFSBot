
 # VFS Appointment Bot
This python script automatically checks the available VFS appointments and notifies the earliest opening via Telegram.

## Dependencies
Check 'requirements.txt' for Python packages.
The captcha recognition is done using Tesseract OCR, which can be installed from [here](https://github.com/tesseract-ocr/tesseract).

- Selenium
- Undetected-chromedriver
- OpenCV
- PyTesseract
- Python-telegram-bot

## How to use
1. Clone the repo.
2. Install the dependencies. 
3. Download the latest Chromedriver from [here](https://chromedriver.chromium.org/).
4. Move the chromedriver.exe file into the repo directory. 
5. Create a Telegram bot using [BotFather](https://t.me/BotFather) and save the auth token.
6. Make a Telegram channel to notify the appointment updates. 
7. Use [this bot](https://t.me/username_to_id_bot) to find the channel id and your own account id.
8. Update the config.ini file with your VFS URL, account info, telegram token, and ids.
9. Run the script!  

## Description
This script was initially made for the Belgium visa center. However, it can also be used for other centers around the world. You might have to change the XPATH (available through inspect element) addresses in the check_appointment() function to your desired values.

### Captcha
So far, I've used OpenCV along with Tesseract to recognize the captcha. Its accuracy is very low, as sometimes it may take 10-15 tries to enter the correct captcha. However, this will not cause any problems as the whole process is automated, and the script will keep trying until it successfully logs in.

### Telegram 
The created bot should have two default commands:
1. /start: Starts the bot.
2. /quit: Stops the bot. (It can be started again using /start as long as the Python script is running.)

Next, add the created bot in the channel you want to post updates to and make sure it has admin priviliges. In order to prevent repitition of messages, the script will keep a record of updates in the record.txt file. Furthermore, by specifying your account id as admin_id in the config.ini, you can prevent others from using the bot, which might cause unexpected behaivor. If you want multiple accounts to access the bot, you can enter multiple ids in the config file separated by space. 

## TODO:
1. Check multiple countries at the same time.
2. Feature to update the config via Telegram input.
