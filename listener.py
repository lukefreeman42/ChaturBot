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

total_session = int(config.get('SETTINGS', 'total_session'))
update_every = int(config.get('SETTINGS', 'update_every'))
print(f'SESSION TIME: {total_session} SECONDS')
print(f'UPDATE EVERY: {update_every} SECONDS')
###### FUNCTIONS ######

#Startup:
# loads driver, goes to target_url, logs in using usernanme and password.
# target_url - Model you will be scraping
# username - login username
# password - login password

def startup(target_url, username, password):
    try:
        ### Go to target url
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options = options)
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

#Scrape Start:
# Once driver is on the model's page and logged into the correct account (based on sender.js)
# scrape_start will begin loading data to csv.

# driver - driver to use (must be logged in to correct account)
# time - time in seconds you want the program to run
# step - period of time before reread chat-box
# csv_file_path - path to csv file you'd like to add to.

def scrape_start(driver, total_session, update_every, csv_file_path):
    try : #attempts to find chat-box
        driver.find_element_by_class_name('chat-box')
        print('LOCATED CHAT-BOX')
    except:
        print('UNABLE TO LOCATE CHAT-BOX')
        driver.quit()
        sys.exit()
    
    session = datetime.datetime.now() #makes a session key
    start = 0
    time.sleep(10)
    while start < total_session: #begins scraping every step seconds until time
        try : #attempts to load csv file
            collection = list(pd.read_csv(csv_file_path).drop('Unnamed: 0', axis=1).to_dict(orient='index').values())
            if start == 0:
                print(f'LOADED {csv_file_path}')
            print(f"LATEST ENTRY: {collection[-1]['date']}")
        except:
            print(f'CSV NOT FOUND: CREATING NEW CSV {csv_file_path}!')
            collection = []
        
        scrapeMe = driver.find_element_by_class_name('chat-box').text
        scrape_chatbox(collection, scrapeMe, session)
        pd.DataFrame(collection).to_csv(csv_file_path)
        print(f'UPDATED CSV {start}/{total_session}')
        time.sleep(update_every)
        start += update_every
#Scrape_ChatBox:
#  data -- A .csv file to enter data into
#  scrapeMe -- Chat-Box text where data is held
#  session -- datetime of program start

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
            print("ERROR IN SCRAPE CHATBOX FUNC, MOST LIKELY '}' INSIDE MSG")

def ChaturBot(target_url, username, password, total_session, update_every, csv_file_path):
    driver = startup(target_url, username, password)
    try:
        scrape_start(driver, total_session, update_every, csv_file_path)
        print(f'Succesfully scraped for {total_session} seconds, uploaded to {csv_file_path}')
        return (driver)
    except:
        driver.quit()

driver = ChaturBot(target_url, username, password, total_session, update_every, csv_file_path)
driver.quit()