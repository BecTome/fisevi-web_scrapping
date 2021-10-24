# @author: BecTome

# This script gets FISEVI web url and extracts the most recent jobs published.

# Output:
#     1. File with all the jobs in the last page
#     2. File with job offers which haven't expired at our current time
#     3. Sends a mail with the hottest offers

# Recommended call:
#     C:\Users\Abecerrat\Documents\GitHub\fisevi-web_scrapping> python main.py \
#          1>logging/$(Get-Date -f yyy-MM-dd-HHmm).err 2>&1

# This way we can store stdout and stderr together in a logging folder

################### IMPORT NECESSARY LIBRARIES #################################
from datetime import datetime
import math
import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from lib.tuple_csv import tuple_csv
from lib.globals import FISEVI_URL, OUTPUT, CRED_PATH, SMTP_CLIENT, RECEIVERS
import unidecode
import locale
import time
import re
from lib.SendEmail import SendEmail
import json
import logging
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
start_time = math.trunc(time.time())
################### SET LOGGING FORMAT #########################################
# File where logs are written
logfile = 'logging/{:%Y-%m-%d-%H%M}.log'.format(datetime.now())

# Two handlers are set: one to send to a file and the other to console
handlers = [logging.FileHandler(logfile, mode='w'),
            logging.StreamHandler()]

# All messages from INFO on are displayed
logging.basicConfig(level='INFO', 
                    format='%(asctime)s %(levelname)-6s | %(message)s',
                    handlers=handlers)

######################## UDF ###################################################
def web_parser(url, parser='html.parser', 
               header={'User-Agent': 'Mozilla/5.0'}):
    '''
    Function which downloads HTML code from a given URL and parses it with 
    Beautiful Soup.

    Returns a BS4 object
    '''
    req = Request(url, headers=header)
    webpage = urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(webpage, parser)
    return soup

def date_formatter(pattern, 
                   date, 
                   join_pat="%H:%M_%d_%B_%Y",
                   date_out_pat="%d/%m/%Y",
                   hour_pat="%H:%M"):
    '''
    Extract date from a string `date` using `pattern`. After that, it's joined
    with underscore and we can assign each part to a dateformat using `join_pat`.

    Finally, we bouild a date with `date_out_pat` format and an hour with 
    `hour_pat` format. 
    '''
    ls_date = re.search(pattern, date).groups()
    date = '_'.join(ls_date)
    date_dt = time.strptime(date, join_pat)
    date = time.strftime(date_out_pat, date_dt)
    hora = time.strftime(hour_pat, date_dt)
    return date, hora

################### EXTRACT INFO FROM URL ######################################
# URL to job posts from FISEVI
parsed_url = FISEVI_URL
logging.info('PARSED WEB: {}'.format(parsed_url))
# Parse the web
soup = web_parser(url=parsed_url)
# The hrefs are under <a> tags
tags = soup('a')
# Pattern to extract expiration date
date_pat = r'.* (\d+:\d+).* (\d+) de (.*) de (\d+)'

# Iterate to extract the info of interest
ls_hrefs = []
for tag in tags:
    # Get the title of the job offer
    title = tag.get('title', None)
    if (title is not None):
        title = unidecode.unidecode(title)
        logging.info(title)
        # Get the hyper references
        href = tag.get('href', None)
        data =  [title, href]
        if (len(str(href)) > 5):
            # It doesn't make sense a href with less than 5 char (http://...)
            # References are parsed too in order to extract in depth information
            soup_l2 = web_parser(url=href)
            # Expiration dates are underlined <u>
            tags_u = soup_l2('u')
            if len(tags_u) > 1:
                date = str(list(tags_u)[-1])
                hora = ''
                try:
                    # It's prefered to format dates so that they are more generic
                    logging.info('PROCESSING DATE...')
                    date, hora = date_formatter(date_pat, date)
                except:
                    pass
                data = data + [date, hora]
            else:
                data = data + ['']
            ls_hrefs.append(data)
        else: 
            pass
    else:
        pass

# All the offers from last page are extracted. However, we are mainly interested
# in those which haven't expired yet
logging.info('DATA EXTRACTED')
logging.info('FILTER ACTIVE OFFERS')
ls_uptodate = [x for x in ls_hrefs if re.match('\d+/\d+/\d+', x[-2])]
ls_uptodate = [x for x in ls_uptodate if (datetime.strptime(x[-2], "%d/%m/%Y") >= 
                                       datetime.now())]

################### EXPORT INTO CSV FILES ######################################
# Create output folder
# Create target directory & all intermediate directories if don't exists
try:
    os.makedirs(OUTPUT)    
    print("Directory " , OUTPUT ,  " Created ")
except FileExistsError:
    print("Directory " , OUTPUT ,  " already exists")  

update_offers = os.path.join(OUTPUT, 'fisevi_scraper_update.csv')
last_page_offers = os.path.join(OUTPUT, 'fisevi_scraper.csv') 

logging.info('EXPORT LAST PAGE OFFERS TO: {}'.format(last_page_offers))                                    
tuple_csv(ls_hrefs, last_page_offers, headers=['Puesto', 'Link', 'Fecha', 'Hora'])

logging.info('EXPORT ACTIVE OFFERS TO: {}'.format(update_offers)) 
tuple_csv(ls_uptodate, update_offers, headers=['Puesto', 'Link', 'Fecha', 'Hora'])

################### SEND RESULTS BY MAIL #######################################
# Get credentials from file {"User": "example@gmail.com", "Password": "ex123"}
logging.info('SEND RESULTS BY MAIL')

cred_path = CRED_PATH
logging.info('READ CREDENTIALS FROM: {}'.format(cred_path))
with open(cred_path, 'rb') as json_file:
    cred = json.load(json_file)
    user = cred['User']
    pwd = cred['Password']

# Instantiate email sender with user data and SMTP client
se = SendEmail(user=user, pwd=pwd, client=SMTP_CLIENT)

# List images in HTML and their aliases and put it in a dict
ls_imgs = ['img/squares.gif',
           'img/logo-fisevi.png',]
ls_ids = ['header', 'logo']
d_images = dict(zip(ls_ids, ls_imgs))

# Do the same with attached data
ls_data = [update_offers, last_page_offers]

# Create iteratively the list in HTML with job offers
ls_jobs=""
for x in ls_uptodate:
    job, href, fecha = tuple(x[:3])
    ls_jobs_i ="<li><a href='{}' style='color:#ffffff;font-size:35px'>[{}] -- {}</a></li><br>".format(href, fecha, job)
    ls_jobs += ls_jobs_i

# HTML mail body
html_txt = '''
        <html lang="es">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>FISEVI - Bot</title>
            </head>

            <table style='background-color: #000000; width: 100%'>
            <td align='center' bgcolor='#000000' style='height: 25%;'>
                <p>
                <img src='cid:{}' alt='Creating Email Magic' width='1239' height='567.88'/>
                </p>
                <p>
                <a href="http://fisevi.com/" class="navbar-brand custom-logo-link default-logo" rel="home">
                                        
                <svg width="200px" height="50px" viewBox="0 0 180 36" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                    <g id="Symbols" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
                        <g id="Logotipo-horizontal" fill="#FFFFFF">
                            <img src='cid:{}'>
                            </g>
                        </g>
                    </g>
                </svg>					</a>
                
                </p>        
                        <p style='color:#ffffff; font-weight: bold; font-size:50px'>Dear Job Seeker,</p>
                        <p style='color:#ffffff; font-weight: bold; font-size:50px'>Here you have the daily FISEVI Newsletter</p>
                <ul style='color:#ffffff;font-size:35px'>
                    {list}
                </ul>
                <p style='color:#ffffff; font-weight: bold; font-size:30px'>Kind Regards</p>
                </td>
                <p>&nbsp</p>
                </td>
            </table>
            </html>
            '''.\
                format(*d_images.keys(), list=ls_jobs)

# Attach and send
logging.info('GENERATE MAIL')
receivers = RECEIVERS
email_msg = se.generate_email(html_txt=html_txt,
                              subject='Daily Newsletter',
                              to_list=receivers,
                              data_paths=ls_data)
logging.info('ATTACH MAIL DATA')
for id, path in d_images.items():
    se.attach_image(email_msg, path, id)

logging.info('SEND IT TO {}'.format(receivers))
se.send_email(email_msg)

end_time = math.trunc(time.time())

# Duration: Calculates number of hours, minutes and seconds 
duration = end_time - start_time   # Total duration in seconds    
duration_minutes = math.trunc(duration / float(60))
duration_seconds = duration - 60*duration_minutes
duration_hours = math.trunc(duration_minutes / float(60))
duration_minutes = duration_minutes - 60*duration_hours

logging.info(f"Start={datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Stop ={datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")

if (duration_hours > 0):
    logging.info("Processing ended after " + str(duration_hours) + " hours and "\
         + str(duration_minutes) + " minutes and " + str(duration_seconds) +\
              " seconds (" + str(duration) + " seconds total)." )
else:
    logging.info(f"Processing ended after " + str(duration_minutes) + \
        " minutes and " + str(duration_seconds) + " seconds (" +\
             str(duration) + " seconds total)." )
logging.info("-------------------  END  -------------------")