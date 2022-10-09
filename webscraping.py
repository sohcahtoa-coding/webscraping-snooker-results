import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
os.environ['PATH'] += r"/usr/local/share/chromedriver"
s = Service('/usr/local/share/chromedriver')
driver = webdriver.Chrome(service=s)
driver.implicitly_wait(10)
start_time = time.time()

FIRST_PLAYERS_XPATH = "//*[@id='tournamentTable']/tbody/tr[4]/td[2]/a"
TOURNAMENT_BODY = '//*[@id="tournamentTable"]/tbody'
TOURNAMENT_TABLE = '//*[@id="tournamentTable"]'
SEASONS_XPATH = '//*[@id="col-content"]/div[3]/ul/li[1]/span/strong/a'


def check_accept_cookies_window():
    try:
        action = driver.find_element(By.XPATH, value='//*[@id="onetrust-accept-btn-handler"]')
        action.click()
    except NoSuchElementException:
        pass


def check_exists_by_xpath(xpath):
    time.sleep(2)
    try:
        res = driver.find_element(By.XPATH, value=xpath)
        if len(res.text) == 0:
            return False
    except NoSuchElementException:
        return False
    res.click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TOURNAMENT_BODY)))

    return True


def check_exists_by_xpath_no_click(xpath):
    time.sleep(2)
    try:
        res = driver.find_element(By.XPATH, value=xpath)
        if len(res.text) == 0:
            return False
    except NoSuchElementException:
        return False
    return True


def check_next_page():
    current_page = driver.current_url
    time.sleep(2)
    try:
        next_page = driver.find_element(By.LINK_TEXT, value='»')
        print("current_page = ", current_page)
        print("next_page =", next_page.get_attribute('href'))
        if len(next_page.text) == 0 or (current_page == next_page.get_attribute('href')):
            print("Returning False because current_page and next_page are identical.")
            return False
    except NoSuchElementException:
        return False

    next_page.click()
    while True:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TOURNAMENT_TABLE)))
            time.sleep(2)
        except TimeoutException:
            logging.exception("Error 1 - Problem loading next page. Refreshing. Details below...")
            driver.refresh()
            time.sleep(10)
            continue
        break
    return True


def collect_match_results(year, tournament):

    result = []
    odds_p1 = []
    odds_p2 = []
    namelist = []
    pop_list = []
    namelist_elements = []

    while True:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TOURNAMENT_BODY)))
        except TimeoutException:
            logging.exception("Error 2 - Page not loaded properly. Trying page refresh. Details below...")
            driver.refresh()
            time.sleep(10)
            continue
        break

    while True:
        try:
            namelist_elements = driver.find_elements(By.XPATH, value='//*[@id="tournamentTable"]/tbody/tr[*]/td[2]/a')
            if namelist_elements[0].text == "":
                print("namelist_elements is empty. Trying to rectify...")
                driver.refresh()
                time.sleep(10)
                continue
        except:
            print("Failure. Trying again...")
            driver.refresh()
            time.sleep(10)
            continue
        break

    for idx, namelist_element in enumerate(namelist_elements):
        namelist.append(namelist_element.text)
        print(idx, namelist[idx])

    result_elements = driver.find_elements(By.XPATH, value='//*[@id="tournamentTable"]/tbody/tr[*]/td[3]')
    time.sleep(1)

    for idx, result_element in enumerate(result_elements):
        if result_element.text != "":
            result.append(result_element.text)
            print(idx, result_element.text)

    odds_p1_elements = driver.find_elements(By.XPATH, value='//*[@id="tournamentTable"]/tbody/tr[*]/td[4]/*')
    time.sleep(1)

    for idx, odds_p1_element in enumerate(odds_p1_elements):
        odds_p1.append(odds_p1_element.text)
        print(idx, "odds_p1", odds_p1[idx])

    odds_p2_elements = driver.find_elements(By.XPATH, value='//*[@id="tournamentTable"]/tbody/tr[*]/td[5]/*')
    time.sleep(1)

    for idx, odds_p2_element in enumerate(odds_p2_elements):
        odds_p2.append(odds_p2_element.text)
        print(idx, "odds_p2", odds_p2[idx])

    if len(result) == len(namelist) and len(result) == len(odds_p1) and len(result) == len(odds_p2):
        print("All list lengths match!")
    else:
        print("Mismatched list sizes. Cannot continue")
        exit()

    for x in range(0, len(odds_p1)):
        if "-" in odds_p1[x] or "-" in odds_p2[x] or result[x] == "w.o." or result[x] == "canc." or \
                 result[x] == "award.":
            print('Match found without odds or results. Adding to pop (remove) list')
            pop_list.append(x)
    print("pop_list =", pop_list)
    pop_list.reverse()
    print("pop_list reversed =", pop_list)

    for x in range(0, len(pop_list)):
        namelist.pop(pop_list[x])
        result.pop(pop_list[x])
        odds_p1.pop(pop_list[x])
        odds_p2.pop(pop_list[x])

    print(len(namelist), namelist)
    print(len(result), result)
    print(len(odds_p1), odds_p1)
    print(len(odds_p2), odds_p2)
    # Import matches on page into results.txt file
    for x in range(0, len(namelist)):
        namelist_split = namelist[x].split(' - ')
        result_split = result[x].split(':')
        print("Original Result =", result[x], "Split Result = ", result_split[0], result_split[1])
        if int(result_split[0]) < int(result_split[1]):
            result_split[0], result_split[1] = result_split[1], result_split[0]
            odds_p1[x], odds_p2[x] = odds_p2[x], odds_p1[x]
            namelist_split[0], namelist_split[1] = namelist_split[1], namelist_split[0]
        temp = (result_split[0], result_split[1])
        result[x] = ":".join(temp)

        print(namelist_split[0], ",", namelist_split[1], ",", result[x], ",", odds_p1[x], ",", odds_p2[x], ",", year,
              ",", tournament)
        filename = open('results.csv', 'a')
        print(namelist_split[0], ",", namelist_split[1], ",", result[x], ",", odds_p1[x], ",", odds_p2[x], ",", year,
              ",", tournament, file=filename)
    namelist.clear()
    result.clear()
    odds_p1.clear()
    odds_p2.clear()
    pop_list.clear()

# Generate list of tournament URLs


url_list = []
tournament_name_list = []
season_links_list = []
season_name_list = []
page_links_list = []
no_url_count = 0
no_matches_element_cnt = 0
no_season_element_cnt = 0
no_tournament_cnt = 0
no_match_cnt = 0

# Click on accept cookies to remove popup window if present
odds_button = '//*[@id="user-header-oddsformat-expander"]/span'
hk_odds = '//*[@id="user-header-oddsformat"]/li[4]/a/span'
while True:
    try:
        driver.get("https://www.oddsportal.com/snooker/results/")
        check_accept_cookies_window()
        action1 = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, odds_button)))
        time.sleep(1)
        action1.click()
        action2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, hk_odds)))
        time.sleep(1)
        action2.click()
    except TimeoutException:
        print("Problem loading page to click HK odds format. Trying again.")
        logging.exception("Error occurred - 3. Logging below...")
        continue
    break

print("Generating list of tournament URLs...")
time.sleep(5)
element_list = driver.find_elements(By.XPATH, value='//*[@id="col-content"]/div[*]/table/tbody/tr[*]/td[*]/a')
element_list_length = len(element_list)
print("Number of URLs is ", element_list_length)
for i in range(0, element_list_length):
    url_list.append(element_list[i].get_attribute('href'))
    tournament_name_list.append(element_list[i].text)

print("url_list = ", url_list)
print("tournament_name_list = ", tournament_name_list)

# Check cookies window hasn't reappeared
check_accept_cookies_window()
# Start collecting match results data
for url_cnt in range(0, element_list_length):
    print("Accessing Tournament", url_list[url_cnt] + "#/page/1")
    driver.get(url_list[url_cnt] + "#/page/1")
    print("Generating Season List...")
    while True:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, SEASONS_XPATH)))
        except TimeoutException:
            print("Problem loading tournament. Trying refresh")
            driver.refresh()
            continue
        break

    season_elements_list = driver.find_elements(By.XPATH, value='//*[@id="col-content"]/div[3]/ul/li[*]/span/strong/a')
    season_elements_length = len(season_elements_list)
    season_links_list.clear()
    season_name_list.clear()
    season_link = ""
    season_name = None

    for season_cnt in range(0, season_elements_length):

        season_link = season_elements_list[season_cnt].get_attribute('href')
        print("Season link = ", season_link)
        season_name = season_elements_list[season_cnt].text
    # Required to avoid Welsh Open problem of just "results" being returned in season_link.
        if "snooker" in season_link:
            season_links_list.append(season_link)
            season_name_list.append(season_name)
        else:
            print("Problem with season_link found. Ignoring. Snooker not in url =", season_link)
            season_elements_length = season_elements_length - 1
    print('Season Count =', season_elements_length)
    print("Season Links List =", season_links_list, "\n")
    print("Season Name List =", season_name_list, "\n")

    for season_cnt in range(0, season_elements_length):
        print("Accessing season:", season_links_list[season_cnt])

        if "/" in season_name_list[season_cnt]:
            season_name_list[season_cnt] = season_name_list[season_cnt][0:4]

        print("Season Name = ", season_name_list[season_cnt])
        if season_cnt != 0:

            while True:
                try:
                    driver.get(season_links_list[season_cnt])
                    print("Getting ", season_links_list[season_cnt])
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TOURNAMENT_TABLE)))
                except TimeoutException:
                    logging.exception("Err 4 - Problem loading new season. Trying again. Details below...")
                    continue
                break

        if check_exists_by_xpath_no_click(FIRST_PLAYERS_XPATH):
            collect_match_results(season_name_list[season_cnt], tournament_name_list[url_cnt])
            while check_next_page():
                collect_match_results(season_name_list[season_cnt], tournament_name_list[url_cnt])

driver.quit()
print("--- %s seconds ---" % (time.time() - start_time))
