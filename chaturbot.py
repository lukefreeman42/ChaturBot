from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import pandas as pd
import time, re, json, sys, datetime, os
from configparser import ConfigParser

###### FUNCTIONS #######

def startup(requirements_path, target_url, login, settings):
    try:
        ##unpack paramenters
        headless = settings['headless']
        geckodriver = settings['geckodriver']
        timeout = settings['timeout']
        csv_update = settings['csv_update']
        restart_after = settings['time_till_restart']
        ### Startup geckodriver
        gecko_path = requirements_path + geckodriver
        options = Options()
        options.headless = headless
        driver = webdriver.Firefox(options = options, executable_path=gecko_path)
        ## Wait 60 seconds before timeouts
        driver.implicitly_wait(timeout)
        print(f'MAX WAIT TIME BETWEEN STATUS UPDATES: {timeout}s')
        print(f'UPDATE CSV EVERY: {csv_update} SECONDS')
        print(f'TIME UNTIL RESTART: {restart_after}s')
        ### Go to target url
        driver.get(target_url)
        print(f'\nFOUND {target_url}')
        ## Click I accept over 18
        driver.find_element_by_id('close_entrance_terms').click()
        print(f'ACCEPTED 18YR OLD CHECK')
        print(f'...WAITING FOR LOGIN PAGE...')
        ## Redirect to Login Page
        driver.find_element_by_class_name('login-link').click()
        print(f'GOING TO LOGIN PAGE')
        print(f'...WAITING FOR INPUTING USERNAME...')
        ## Input username
        username = login['username']
        driver.find_element_by_id('id_username').send_keys(username)
        print(f'\nLISTENER USERNAME: {username}')
        ## Input password
        print(f'...WAITING FOR INPUTING PASSWORD...')
        password_input = driver.find_element_by_id('id_password')
        password_input.send_keys(login['password'])
        ## Submit form
        print(f'...WAITING TO SUBMIT CREDENTIALS...')
        password_input.submit()
        print('SUBMITTED LOGIN CREDENTIALS')
        ## Return the enviornment
        print('FINISHED STARTUP')
        print('\nQUIT NOW OR REQUIRED TO KILL')
        time.sleep(timeout)
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

def tips_to_csv(first, csv_update, driver, csv_file_path, session):
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
        time.sleep(csv_update)
        return True
    except Exception as e:
        print(f"TIPS TO CSV FAILED!!!\nENDING SESSION!!!\nEXCEPTION:{e}")
        return False

def scrape_chatbox(data, scrapeMe, session):
    
    pattern = re.compile(r'Notice: (\{[^\}]*\})') #sender.js determines pattern of data sent
    date = re.compile(r'"date":(\d*)\}')
    matches = pattern.finditer(scrapeMe) #find all matches of useful data in Chat-Box
    x = len(data)
    for match in matches:
        Json = match.group(1)
        try:
            dt = int(date.search(Json).group(1)) 
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
    try:
        print(f"CSV LAST-ENTRY: {data[-1]['date']}")
    except:
        print('CSV UPDATED: NO LAST ENTRY')

def ChaturBot_csv (requirements_path, target_url, login, settings, csv_file_path):
    csv_update = settings['csv_update']

    driver = startup(requirements_path, target_url, login, settings)
    while (True):
            sessionKey = create_sessionKey(driver)
            if sessionKey:
                # begin tips_to_csv function
                print(f'BEGINNING {tips_to_csv}')
                for first in range(0, settings.time_till_restart, csv_update):
                    if not tips_to_csv(first, csv_update, driver, csv_file_path, sessionKey):
                        break
                print(f'\nCHECKING IF MODEL IS ONLINE...')
            else:
                print(f'FAILED...\nCHECKING IF MODEL ONLINE IN {csv_update}s')
                time.sleep(csv_update)

def main():
    #path to required files
    requirements_path = './req/'
    
    
    #grab client
    client = sys.argv[1] if len(sys.argv) > 1 else 'TEST_CB'
    print(f'CLIENT IS "{client}"')
    #read config file
    try:
        config = ConfigParser()
        config.read(requirements_path+'keys.config')
        #listening bot login info
        login = {'username': config.get(client, 'username'),
                 'password': config.get(client, 'password')
        }
        #target location
        target_url = config.get(client, 'target_url')
        #data storage
        csv_file_dir = config.get(client, 'csv_file_dir')
        csv_file_path = csv_file_dir + config.get(client, 'csv_file_name')
        os.makedirs(csv_file_dir, exist_ok=True)
        #settings
        settings = {'headless': bool(int(config.get('SETTINGS', 'headless'))), 
                    'geckodriver': config.get('SETTINGS', 'geckodriver_OS'), 
                    'time_till_restart': int(config.get('SETTINGS', 'time_till_restart')), 
                    'csv_update': int(config.get('SETTINGS', 'update_csv_every')),
                    'timeout': int(config.get('SETTINGS', 'wait_x_then_timeout')),
                    }
    except Exception as e:
        printf(f'EXCEPTION!!:{e}')
        return -1
    #begin
    ChaturBot_csv(requirements_path, target_url, login, settings, csv_file_path)
    return 0

if __name__ == "__main__":
    main()