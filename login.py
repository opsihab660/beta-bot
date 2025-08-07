import time
import os
import json
import re
import random
import logging
from contextlib import contextmanager

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions

from CloudflareBypasser import CloudflareBypasser

# === Configuration ===
BASE_URL = "https://mediateluk.com/sms/index.php"
LOGIN_URL = BASE_URL + "?login=1"
SUMMARY_URL = BASE_URL + "?opt=shw_sum"
CHECK_INTERVAL = 10  # Seconds between checks
IGNORE_INITIAL_DATA = True  # Set to False to process existing data on startup


# === Credentials ===
USERNAME = os.getenv("USERNAME", "2915")
PASSWORD = os.getenv("PASSWORD", "sah_0731")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7443478238:AAEPF5zYatWTIpfN2OLOUN7mNdFgcGDT0a4")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "-1002882865906")

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='w', encoding='utf-8')
    ]
)

# === Telegram Bot Setup ===
try:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    bot_info = bot.get_me()
    logging.info(f"[BOT] Telegram bot connected: @{bot_info.username}")
except Exception as e:
    logging.error(f"[ERROR] Failed to connect to Telegram: {e}")
    bot = None

# Islamic quotes for message formatting
ISLAMIC_QUOTES = [
    ("وَذَكِّرْ فَإِنَّ الذِّكْرَى تَنْفَعُ الْمُؤْمِنِينَ", "And remind, for indeed, the reminder benefits the believers."),
    ("يَا أَيُّهَا الَّذِينَ آمَنُوا اصْبِرُوا وَصَابِرُوا وَرَابِطُوا", "O you who have believed, persevere and endure and remain stationed."),
    ("إِنَّ مَعَ الْعُسْرِ يُسْرًا", "Indeed, with hardship comes ease."),
    ("وَتَعَاوَنُوا عَلَى الْبِرِّ وَالتَّقْوَى", "And cooperate in righteousness and piety."),
    ("اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ", "Allah - there is no deity except Him, the Ever-Living, the Sustainer of existence.")
]

def extract_otp(message):
    """Extracts a 6-digit OTP from a message."""
    match = re.search(r"\b(\d{3}[- ]?\d{3}|\d{6})\b", message)
    return match.group(1).replace("-", "").replace(" ", "") if match else None

# A comprehensive country map for prefix guessing
def guess_country(number):
    """Guesses the country based on the phone number prefix."""
    clean_number = number.lstrip('+')
    country_map = {
        "1": "🇺🇸 United States / 🇨🇦 Canada", "7": "🇷🇺 Russia / 🇰🇿 Kazakhstan", "20": "🇪🇬 Egypt", 
        "27": "🇿🇦 South Africa", "30": "🇬🇷 Greece", "31": "🇳🇱 Netherlands", "32": "🇧🇪 Belgium", 
        "33": "🇫🇷 France", "34": "🇪🇸 Spain", "36": "🇭🇺 Hungary", "39": "🇮🇹 Italy", "40": "🇷🇴 Romania", 
        "41": "🇨🇭 Switzerland", "43": "🇦🇹 Austria", "44": "🇬🇧 United Kingdom", "45": "🇩🇰 Denmark", 
        "46": "🇸🇪 Sweden", "47": "🇳🇴 Norway", "48": "🇵🇱 Poland", "49": "🇩🇪 Germany", "51": "🇵🇪 Peru", 
        "52": "🇲🇽 Mexico", "54": "🇦🇷 Argentina", "55": "🇧🇷 Brazil", "58": "🇻🇪 Venezuela", 
        "60": "🇲🇾 Malaysia", "61": "🇦🇺 Australia", "62": "🇮🇩 Indonesia", "63": "🇵🇭 Philippines", 
        "64": "🇳🇿 New Zealand", "65": "🇸🇬 Singapore", "66": "🇹🇭 Thailand", "81": "🇯🇵 Japan", 
        "82": "🇰🇷 South Korea", "84": "🇻🇳 Vietnam", "86": "🇨🇳 China", "90": "🇹🇷 Turkey", 
        "91": "🇮🇳 India", "92": "🇵🇰 Pakistan", "93": "🇦🇫 Afghanistan", "94": "🇱🇰 Sri Lanka", 
        "95": "🇲🇲 Myanmar", "98": "🇮🇷 Iran", "212": "🇲🇦 Morocco", "213": "🇩🇿 Algeria", 
        "234": "🇳🇬 Nigeria", "251": "🇪🇹 Ethiopia", "254": "🇰🇪 Kenya", "255": "🇹🇿 Tanzania", 
        "351": "🇵🇹 Portugal", "359": "🇧🇬 Bulgaria", "380": "🇺🇦 Ukraine", "880": "🇧🇩 Bangladesh",
        "966": "🇸🇦 Saudi Arabia", "971": "🇦🇪 United Arab Emirates", "972": "🇮🇱 Israel", "974": "🇶🇦 Qatar",
    }
    for prefix in sorted(country_map.keys(), key=len, reverse=True):
        if clean_number.startswith(prefix):
            return country_map[prefix]
    return "🌍 Unknown"

def send_telegram_message(entry):
    """Formats and sends a message to the Telegram group."""
    if not bot:
        logging.error("Telegram bot not initialized. Cannot send message.")
        return

    datetime, _, _, receiver, message = entry.values()
    code = extract_otp(message)
    country = guess_country(receiver)
    arabic, translation = random.choice(ISLAMIC_QUOTES)

    # --- Final, Polished Formatting ---
    
    # Header
    header = f"📢 <b>{country} WhatsApp OTP Received</b>"

    # Details section
    details = (
        f"🗓 <b>Date & Time:</b> <code>{datetime}</code>\n"
        f"📱 <b>Service:</b> <code>WhatsApp</code>\n"
        f"📞 <b>Number:</b> <code>{receiver}</code>\n"
        f"🌍 <b>Country:</b> {country}"
    )

    # OTP section for easy copying
    code_section = ""
    if code:
        code_section = (
            f"🔑 <b>OTP Code</b>: "
            f"<code>{code}</code>"
        )

    # Full message with HTML line breaks, removing the problematic <pre> tag
    formatted_message = message.strip().replace('\\n', '\n')
    full_message_section = f"📩 <b>Original Message:</b>\n<pre>{formatted_message}</pre>"

    # Quote section
    quote_section = (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"📖 <b>Reminder:</b>\n"
        f"<i>{arabic}</i>\n"
        f"<i>({translation})</i>"
    )
    
    # Footer
    footer = f"\n\n<i>Bot by @nextblacklist</i>"

    # Assemble the final message
    text = (
        f"{header}\n\n"
        f"{details}\n\n"
        f"{code_section}\n\n"
        f"{full_message_section}\n\n"
        f"{quote_section}"
        f"{footer}"
    )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👨‍💻 Bot Developer", url="https://t.me/nextblacklist"))

    try:
        bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=text, parse_mode="HTML", reply_markup=markup)
        logging.info(f"[SENT] Sent Telegram notification for {receiver}")
    except Exception as e:
        logging.error(f"[ERROR] Failed to send Telegram message: {str(e)}")

def fetch_sms_summary(driver: ChromiumPage):
    """Fetches and parses the SMS summary page using the browser."""
    logging.info(f"[*] Fetching WhatsApp message summary at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
    
    payload = {"det": "1", "sender": "WhatsApp"}
    # DrissionPage doesn't have a direct way to send POST with form data on an existing page,
    # so we use JavaScript to submit the form.
    js_script = f"""
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '{SUMMARY_URL}';
    var params = {json.dumps(payload)};
    for(var key in params) {{
        var hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = key;
        hiddenField.value = params[key];
        form.appendChild(hiddenField);
    }}
    document.body.appendChild(form);
    form.submit();
    """
    driver.run_js(js_script)
    driver.wait.load_start() # Wait for the new page to begin loading

    try:
        soup = BeautifulSoup(driver.html, "html.parser")
        tables = soup.find_all("table", class_="table-head-bg-warning")

        messages = []
        if len(tables) >= 2:
            message_table = tables[1]
            for row in message_table.select("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) == 5:
                    entry = {
                        "datetime": cols[0].text.strip(),
                        "range": cols[1].text.strip(),
                        "sender": cols[2].text.strip(),
                        "receiver": cols[3].text.strip(),
                        "message": cols[4].text.strip()
                    }
                    messages.append(entry)
            logging.info(f"[SUCCESS] Found {len(messages)} messages")
        else:
            logging.warning("[WARN] Message table not found or structure changed.")

        return messages
    except Exception as e:
        logging.error(f"[ERROR] Error fetching or parsing messages: {str(e)}")
        return []

def save_results(data, filename="results.json"):
    """Saves data to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"[+] Results saved to {filename}")
    except Exception as e:
        logging.error(f"[!] Error saving results: {str(e)}")

def browser_login(driver: ChromiumPage):
    """Handles login."""
    # If cookie login fails, proceed with manual login
    logging.info('Navigating to the login page.')
    driver.get(LOGIN_URL)

    logging.info('Starting Cloudflare bypass.')
    cf_bypasser = CloudflareBypasser(driver)
    cf_bypasser.bypass()

    if "just a moment" in driver.title.lower():
        logging.error("Cloudflare bypass failed. Could not proceed.")
        return False

    logging.info("Cloudflare bypass successful. Proceeding to login.")
    try:
        user_field = driver.ele('xpath://input[@name="user"]')
        user_field.input(USERNAME)
        logging.info("Entered username.")

        pass_field = driver.ele('xpath://input[@name="password"]')
        pass_field.input(PASSWORD)
        logging.info("Entered password.")

        login_button = driver.ele('xpath://button[@type="submit"]')
        login_button.click()
        logging.info("Login button clicked.")
        
        driver.wait.ele_displayed('xpath://*[contains(text(), "Logout")]', timeout=15)
        logging.info("[SUCCESS] Manual login successful!")
        
        return True

    except Exception as e:
        logging.error(f"Manual login failed: {e}")
        return False

def main_loop(driver: ChromiumPage):
    """Main execution loop that runs continuously."""
    seen_messages = set()
    
    if not IGNORE_INITIAL_DATA:
        initial_data = fetch_sms_summary(driver)
        for entry in initial_data:
            identifier = f"{entry['datetime']}-{entry['receiver']}-{entry['message'][:20]}"
            seen_messages.add(identifier)
        logging.info(f"[*] Initial data loaded. Tracking {len(seen_messages)} messages.")
    
    while True:
        try:
            current_data = fetch_sms_summary(driver)
            new_messages = []
            
            for entry in current_data:
                identifier = f"{entry['datetime']}-{entry['receiver']}-{entry['message'][:20]}"
                if identifier not in seen_messages:
                    seen_messages.add(identifier)
                    new_messages.append(entry)
            
            if new_messages:
                logging.info(f"[NOTIFY] Found {len(new_messages)} new messages")
                for entry in new_messages:
                    send_telegram_message(entry)
            else:
                logging.info("[*] No new messages found")
            
            logging.info(f"\n[WAITING] Waiting {CHECK_INTERVAL} seconds before next check...\n")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logging.info("\n[!] Script interrupted by user")
            break
        except Exception as e:
            logging.error(f"[ERROR] Unexpected error in main loop: {str(e)}")
            logging.info("[RESTART] Attempting to re-login...")
            if not browser_login(driver):
                logging.error("[ERROR] Re-login failed. Exiting.")
                break
            # Continue to next iteration after re-login
            continue

@contextmanager
def browser_manager():
    """Manages the browser lifecycle."""
    is_headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    display = None
    if is_headless and os.name == 'posix':
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()

    browser_path = os.getenv('CHROME_PATH') # Let DrissionPage find it, or specify full path
    # Example for Windows: r"C:/Program Files/Google/Chrome/Application/chrome.exe"
    # Example for Linux: "/usr/bin/google-chrome"

    arguments = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
    ]

    options = ChromiumOptions().auto_port()
    if browser_path:
        options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)
    
    driver = ChromiumPage(addr_or_opts=options)
    try:
        yield driver
    finally:
        logging.info('Closing the browser.')
        driver.quit()
        if display:
            display.stop()

if __name__ == "__main__":
    if not bot:
        exit(1)

    try:
        with browser_manager() as driver:
            if browser_login(driver):
                main_loop(driver)
            else:
                logging.error("[ERROR] Initial login failed. Cannot start main loop.")
    except KeyboardInterrupt:
        logging.info("\n[!] Script terminated by user.")
    except Exception as e:
        logging.error(f"[ERROR] A critical error occurred: {e}")
        
    logging.info("Script finished.")
    exit(0)
