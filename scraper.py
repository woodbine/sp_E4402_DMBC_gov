# -*- coding: utf-8 -*-
import sys
reload(sys) # Reload does the trick!
sys.setdefaultencoding('UTF8')
import os
import re
import requests
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil.parser import parse

# Set up variables
entity_id = "E4402_DMBC_gov"
url = "http://www.doncaster.gov.uk/services/the-council-democracy/local-transparency-payments-to-suppliers"
errors = 0
# Set up functions
def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    year, month = int(date[:4]), int(date[5:7])
    now = datetime.now()
    validYear = (2000 <= year <= now.year)
    validMonth = (1 <= month <= 12)
    if all([validName, validYear, validMonth]):
        return True
def validateURL(url):
    try:
        r = requests.get(url, verify=False, allow_redirects=True)
        return r.status_code == 200
    except:
        raise
def validateFiletype(url):
    try:
        r = requests.head(url, verify=False, allow_redirects=True)
        sourceFilename = r.headers.get('Content-Disposition')

        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        elif r.headers['Content-Type'] == 'text/csv':
            ext = '.csv'
        else:
            ext = os.path.splitext(url)[1]

        if ext in ['.csv', '.xls', '.xlsx']:
            return True
    except:
        raise
def convert_mth_strings ( mth_string ):

    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    #loop through the months in our dictionary
    for k, v in month_numbers.items():
#then replace the word with the number

        mth_string = mth_string.replace(k, v)
    return mth_string
# pull down the content from the webpage
html = urllib2.urlopen(url)
soup = BeautifulSoup(html, 'lxml')
# find all entries with the required class
block = soup.find('div', attrs = {'class':'content content-primary '})
links = block.find_all('a', href =True)
for link in links:
    csvfile = link.text
    if 'Payment to suppliers' in csvfile:
        links_url = 'http://www.doncaster.gov.uk/' + '/'.join(link['href'].split('/')[3:6])
        html_csv = urllib2.urlopen(links_url)
        soup_csv = BeautifulSoup(html_csv, 'lxml')
        blocks_csv = soup_csv.find_all('a')
        for block_csv in blocks_csv:
            if 'Payment' in block_csv.text:
                if '.csv' in block_csv['href']:
                    url_csv = block_csv['href']
                    csvfiles = block_csv.text
                    csvMth = csvfiles.split(' ')[-2].strip()[:3]
                    csvYr = csvfiles.split(' ')[-1].strip()
                    csvMth = convert_mth_strings(csvMth.upper())
                    filename = entity_id + "_" + csvYr + "_" + csvMth
                    todays_date = str(datetime.now())
                    file_url = url_csv.strip()
                    if not validateFilename(filename):
                        print filename, "*Error: Invalid filename*"
                        print file_url
                        errors += 1
                        continue
                    if not validateURL(file_url):
                        print filename, "*Error: Invalid URL*"
                        print file_url
                        errors += 1
                        continue
                    if not validateFiletype(file_url):
                        print filename, "*Error: Invalid filetype*"
                        print file_url
                        errors += 1
                        continue
                    scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
                    print filename
if errors > 0:
   raise Exception("%d errors occurred during scrape." % errors)
