from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import pandas as pd
import time
import re
import json
import sys
import datetime
from configparser import ConfigParser

###### ARGUMENTS ######
client = sys.argv[1] if len(sys.argv) > 1 else 'TEST'

print(f'CLIENT IS {client}')
config = ConfigParser()
config.read('keys.config')
username = config.get(client, 'username')
password = config.get(client, 'password')
target_url = config.get(client, 'target_url')
csv_file_path = config.get(client, 'csv_file_path')

update_every = int(config.get('SETTINGS', 'update_every'))
print(f'UPDATE EVERY: {update_every} SECONDS')

###### FUNCTIONS #######

def startup(target_url, username, password):
    try:
        ### Use Headless browser
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options = options)
        ### Go to target url
        driver.get(target_url)
        print(f'FOUND {target_url}')
        ## Wait 10 seconds before timeouts
        wait = WebDriverWait(driver, 10) 
        ## Click I accept over 18
        accept_18 = wait.until(EC.element_to_be_clickable((By.ID, 'close_entrance_terms')))
        accept_18.click()
        print(f'ACCEPTED 18YR OLD CHECK')
        ## Redirect to Login Page
        login_page = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'login-link')))
        login_page.click()
        print('GOING TO LOGIN PAGE')
        ## Input username
        login_input = wait.until(EC.visibility_of_element_located((By.ID, 'id_username')))
        login_input.send_keys(username)
        ## Input password
        password_input = wait.until(EC.visibility_of_element_located((By.ID, 'id_password')))
        password_input.send_keys(password)
        ## Submit form
        login_input.submit()
        print('SUBMITTED LOGIN CREDENTIALS')
        ## Return the enviornment
        return (driver)
    except:
        print('STARTUP FAILED')
        driver.quit()
        sys.exit()
    
def scrape_chatbox(data, scrapeMe, session):
    
    pattern = re.compile(r'Notice: (\{[^\}]*\})') #sender.js determines pattern of data sent
    date = re.compile(r'"date":(\d*)\}')
    matches = pattern.finditer(scrapeMe) #find all matches of useful data in Chat-Box
    for match in matches:
        Json = match.group(1)
        try:
            dt = int(date.search(Json).group(1)) 
            if len(data): #check if dataframe is empty or existing
                if (dt > data[-1]['date']): #if json we found is newer than last entry in df, append
                    Json = json.loads(Json)
                    Json['session'] = session #add session key to json object before appending
                    data.append(Json)
            else:
                Json = json.loads(Json)
                Json['session'] = session
                data.append(Json)
        except:
            print("ERROR IN SCRAPE CHATBOX FUNC, MOST LIKELY '}' INSIDE A MSG")

def ChaturBot2 (target_url, username, password, update_every, csv_file_path):
    driver = startup(target_url, username, password)
    while (True):
        try : #attempts to find chat-box
            driver.find_element_by_class_name('chat-box')
            print('LOCATED CHAT-BOX')
            time.sleep(5)
            session = datetime.datetime.now()
            print(f'CREATING SESSION {session}')
            x = True
            while (True):
                try:
                    collection = list(pd.read_csv(csv_file_path).drop('Unnamed: 0', axis=1).to_dict(orient='index').values())
                    if (x):
                        print(f'LOADED {csv_file_path}')
                        x = False
                except:
                    print(f'CSV NOT FOUND: CREATING NEW CSV {csv_file_path}!')
                    collection = []
                time.sleep(5)
                try:
                    scrapeMe = driver.find_element_by_class_name('chat-box').text
                    scrape_chatbox(collection, scrapeMe, session)
                    try:
                        print(f"CSV UPDATED: {collection[-1]['date']}")
                    except:
                        print('CSV UPDATED: NO LAST ENTRY')
                    pd.DataFrame(collection).to_csv(csv_file_path)
                    time.sleep(update_every)
                except:
                    print(f'SESSION HAS ENDED {datetime.datetime.now()}')
                    break
        except:
            print('UNABLE TO LOCATE CHAT-BOX')
            time.sleep(15)

ChaturBot2(target_url, username, password, update_every, csv_file_path)