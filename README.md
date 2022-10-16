# webscraping-snooker-results
Scrapes historical snooker results and pre-game odds from oddsportal.com and stores them in a .csv file.

Instructions for use:
1. PyCharm IDE was used to write this code.
2. You will need chrome and the chrome driver suitable for the version you are using. It is available at https://chromedriver.chromium.org/downloads.
2. The chrome driver location must be specified on lines 11 and 12 of the code
3. The selenium libraries need to be installed. Instructions are available at https://stackoverflow.com/questions/24333330/using-selenium-with-pycharm-ce for use with PyCharm.
4. All results will be stored in a file called results.csv. Execution takes around three hours. It scrapes about 30000 results.
5. Once scraped, data analysis can be used to find which players have historically provided a positive return on bets, and therefore which players should be backed in the future. The "Analyse-Snooker-Results" repository can be used to obtain the results... 
