##
# ssh into server
# run script, pipe to output file
# crtl A + D
##

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import pandas as pd
import time, re, json, sys, datetime
from configparser import ConfigParser
from aux.read_chat import chatbox_to_txt

###### ARGUMENTS ######
requirements_path = './req/'

client = sys.argv[1] if len(sys.argv) > 1 else 'TEST'

print(f'CLIENT IS {client}')
config = ConfigParser()
config.read(requirements_path+'keys.config')
username = config.get(client, 'username')
password = config.get(client, 'password')
target_url = config.get(client, 'target_url')
csv_file_path = config.get(client, 'csv_file_path')

time_to_check = int(config.get('SETTINGS', 'time_to_check'))
update_every = int(config.get('SETTINGS', 'update_every'))
print(f'UPDATE EVERY: {update_every} SECONDS')

###### FUNCTIONS #######

def startup(target_url, username, password, wait_time):
    try:
        ### Use Headless browser
        gecko_path = requirements_path+'geckodriver'
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options = options, executable_path=gecko_path)
        ## Wait 60 seconds before timeouts
        driver.implicitly_wait(wait_time)
        print(f'MAX WAIT TIME BETWEEN OUTPUT: {wait_time}')
        ### Go to target url
        driver.get(target_url)
        print(f'FOUND {target_url}')
        ## Wait 60 seconds before timeouts
        wait = WebDriverWait(driver, 60) 
        ## Click I accept over 18
        accept_18 = wait.until(EC.element_to_be_clickable((By.ID, 'close_entrance_terms')))
        accept_18.click()
        print(f'ACCEPTED 18YR OLD CHECK')
        print(f'...WAITING FOR LOGIN PAGE...')
        ## Redirect to Login Page
        login_page = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'login-link')))
        login_page.click()
        print(f'GOING TO LOGIN PAGE')
        print(f'...WAITING FOR INPUTING USERNAME...')
        ## Input username
        login_input = wait.until(EC.visibility_of_element_located((By.ID, 'id_username')))
        login_input.send_keys(username)
        print(f'LISTENER USERNAME: {username}')
        ## Input password
        print(f'...WAITING FOR INPUTING PASSWORD...')
        password_input = wait.until(EC.visibility_of_element_located((By.ID, 'id_password')))
        password_input.send_keys(password)
        ## Submit form
        print(f'...WAITING TO SUBMIT CREDENTIALS...')
        login_input.submit()
        print('SUBMITTED LOGIN CREDENTIALS')
        ## Return the enviornment
        print('QUIT NOW OR REQUIRED TO KILL')
        time.sleep(wait_time)
        print('FINISHED STARTUP')
        return (driver)
    except Exception as e:
        print(f'STARTUP FAILED!\n{e}')
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
        except Exception as e:
            print(f"ERROR IN SCRAPE CHATBOX FUNC... \n{e}")

def ChaturBot2 (target_url, username, password, update_every, time_to_check, csv_file_path, wait_time):
    driver = startup(target_url, username, password, wait_time)
    driver.implicitly_wait(wait_time)
    while (True):
        print(f'OPENING ROOM...\n{target_url}')
        try : #attempts to find chat-box
            driver.get(target_url)
            print('LOCATING CHAT-BOX...')
            driver.find_element_by_class_name('chat-box')
            print('LOCATED CHAT-BOX')
            session = datetime.datetime.now()
            print(f'CREATED SESSION: {session}')
            x = 0
            while (x < time_to_check):
                try:
                    collection = list(pd.read_csv(csv_file_path).drop('Unnamed: 0', axis=1).to_dict(orient='index').values())
                    if (x == 0):
                        print(f'LOADED {csv_file_path}')
                except:
                    print(f'CSV NOT FOUND: CREATING NEW CSV {csv_file_path}!')
                    collection = []
                try:
                    scrapeMe = driver.find_element_by_class_name('chat-box').text
                    #START - AUXILARY FOR MILAN
                    chatbox_to_txt(scrapeMe, 'forMilan.txt')
                    #END
                    scrape_chatbox(collection, scrapeMe, session)
                    try:
                        print(f"CSV UPDATED: {collection[-1]['date']}")
                    except:
                        print('CSV UPDATED: NO LAST ENTRY')
                    pd.DataFrame(collection).to_csv(csv_file_path)
                    time.sleep(update_every)
                    x += update_every
                    driver.find_element_by_class_name('chat-box')
                except Exception as e:
                    print(f'SESSION HAS ENDED {datetime.datetime.now()}\nEXCEPTION:\n{e}')
                    break
            print(f'{time_to_check} REACHED!!\nCHECKING IF MODEL IS ONLINE...')
        except Exception as e:
            print(f'UNABLE TO LOCATE CHAT-BOX {datetime.datetime.now()}\nEXCEPTION:\n{e}')

ChaturBot2(target_url, username, password, update_every, time_to_check, csv_file_path, 60)
