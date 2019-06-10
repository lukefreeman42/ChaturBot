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
import time, re, json, sys, datetime, os, difflib
from configparser import ConfigParser

###### ARGUMENTS ######
requirements_path = './req/'

client = sys.argv[1] if len(sys.argv) > 1 else 'TEST'

print(f'CLIENT IS "{client}"')
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

def startup(target_url, username, password, wait_time, time_to_check):
    try:
        ### Use Headless browser
        gecko_path = requirements_path+'geckodriver'
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options = options, executable_path=gecko_path)
        ## Wait 60 seconds before timeouts
        driver.implicitly_wait(wait_time)
        print(f'MAX WAIT TIME BETWEEN OUTPUT: {wait_time}s')
        print(f'MAX TIME TO CHECK: {time_to_check}s')
        ### Go to target url
        driver.get(target_url)
        print(f'\nFOUND {target_url}')
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
        print(f'\nLISTENER USERNAME: {username}')
        ## Input password
        print(f'...WAITING FOR INPUTING PASSWORD...')
        password_input = wait.until(EC.visibility_of_element_located((By.ID, 'id_password')))
        password_input.send_keys(password)
        ## Submit form
        print(f'...WAITING TO SUBMIT CREDENTIALS...')
        login_input.submit()
        print('SUBMITTED LOGIN CREDENTIALS')
        ## Return the enviornment
        print('FINISHED STARTUP')
        print('\nQUIT NOW OR REQUIRED TO KILL')
        time.sleep(wait_time)
        print(f'\nOPENING ROOM...\n{target_url}')
        return (driver)
    except Exception as e:
        print(f'\nSTARTUP FAILED!\n{e}')
        driver.quit()
        sys.exit()

def create_sessionKey(driver):
    try:
        driver.get(target_url)
        print('LOCATING CHAT-BOX...')
        driver.find_element_by_class_name('chat-box')
        print('LOCATED CHAT-BOX')
        session = datetime.datetime.now()
        print(f'\nCREATED SESSION: {session}')
        return session
    except Exception as e:
        print(f'\nUNABLE TO LOCATE CHAT-BOX {datetime.datetime.now()}\nEXCEPTION:\n{e}')
        return False

##### TIP TRACKER ######

def tips_to_csv(first, update_every, driver, csv_file_path, session):
    try:
        try:
            collection = list(pd.read_csv(csv_file_path).drop('Unnamed: 0', axis=1).to_dict(orient='index').values())
            if not first:
                print(f'\nLOADED {csv_file_path}')
        except:
            print(f'\nCSV NOT FOUND: CREATING NEW CSV {csv_file_path}!')
            collection = []
        scrapeMe = driver.find_element_by_class_name('chat-box').text
        scrape_chatbox(collection, scrapeMe, session)
        pd.DataFrame(collection).to_csv(csv_file_path)
        time.sleep(update_every)
        #driver.find_element_by_class_name('chat-box')
        return True
    except Exception as e:
        print(f"TIPS TO CSV FAILED!!!\nENDING SESSION!!!\nEXCEPTION:{e}")
        return False

def scrape_chatbox(data, scrapeMe, session):
    
    pattern = re.compile(r'Notice: (\{[^\}]*\})') #sender.js determines pattern of data sent
    date = re.compile(r'"date":(\d*)\}')
    matches = pattern.finditer(scrapeMe) #find all matches of useful data in Chat-Box
    try:
        print(f"CSV LAST-ENTRY: {data[-1]['date']}")
    except:
        print('CSV UPDATED: NO LAST ENTRY')
    for match in matches:
        Json = match.group(1)
        try:
            dt = int(date.search(Json).group(1)) 
            x = len(data)
            if x: #check if dataframe is empty or existing
                if (dt > int(data[-1]['date'])): #if json we found is newer than last entry in df, append
                    Json = json.loads(Json)
                    Json['session'] = session #add session key to json object before appending
                    data.append(Json)
            else:
                Json = json.loads(Json)
                Json['session'] = session
                data.append(Json)  
        except Exception as e:
            print(f"\nERROR IN SCRAPE CHATBOX FUNC... \n{e}")
    print(f"APPENDED {len(data) - x} ENTRIES")

##### COMPETITION TRACKER #####

def competition_chat(update_every, driver, target_url, session):
    try:
        name = model_name(target_url)
        new_data = driver.find_element_by_class_name('chat-box').text
        chatbox_to_txt(new_data, name+session, name)
        print(f'UPDATED {name}/{name+session}')
        time.sleep(update_every)
        return True
    except:
        return False

def chatbox_to_txt(newData, txt_path, dir_path):
    try:
        os.mkdir(dir_path, '0755' )
        print(f'CREATED {dir_path}!!')
    except:
        print(f'FOUND {dir_path}...')
    f = open(f"{dir_path+txt_path}", 'w')
    f.close()
    f = open(f"{dir_path+txt_path}", 'r')
    oldD = f.read()
    f.close()
    diff = list(difflib.Differ().compare(oldD, newData))
    appendme = ""
    f = open(f"{dir_path+txt_path}", 'a')
    for x in diff:
        if(x[0] == '+'):
            appendme = appendme+x[2]
    print(appendme, file=f)
    f.close()

def model_name(target_url):
    pattern = re.compile(r'(https://chaturbate.com/)([^/]*)/?')
    match = pattern.search(target_url)
    return match.group(2)


##### MAIN BOT ##### 


def ChaturBot_csv (target_url, username, password, update_every, time_to_check, csv_file_path, wait_time):
    driver = startup(target_url, username, password, wait_time, time_to_check)
    driver.implicitly_wait(wait_time)
    while (True):
            sessionKey = create_sessionKey(driver)
            if sessionKey:
                print(f'BEGINNING {tips_to_csv}')
                for first in range(0, time_to_check, update_every):
                    if not tips_to_csv(first, update_every, driver, csv_file_path, sessionKey):
                        break
                print(f'\n{time_to_check} REACHED!!\nCHECKING IF MODEL IS ONLINE...')
            else:
                print('FAILED')

def ChaturBot_competition (target_url, username, password, update_every, time_to_check, csv_file_path, wait_time):
    driver = startup(target_url, username, password, wait_time, time_to_check)
    driver.implicitly_wait(wait_time)
    while (True):
            sessionKey = create_sessionKey(driver)
            if sessionKey:
                print(f'BEGINNING {tips_to_csv}')
                for _ in range(0, time_to_check, update_every):
                    if not competition_chat(update_every, driver, target_url, sessionKey):
                        break
                print(f'\n{time_to_check} REACHED!!\nCHECKING IF MODEL IS ONLINE...')
            else:
                print('FAILED')

ChaturBot2(target_url, username, password, update_every, time_to_check, csv_file_path, 60)