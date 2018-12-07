# -*- coding: utf-8 -*-  

import bs4
from bs4 import BeautifulSoup
import csv,json
from time import sleep
from retrying import retry
import re,os
import codecs
import requests
from requests.exceptions import ReadTimeout,ConnectionError,RequestException

def get_name(tag):
    return tag.has_attr('name') and tag.has_attr('content') and tag['name'] == 'title'
def get_desc(tag):
    return tag.has_attr('name') and tag.has_attr('content') and tag['name'] == 'description'
def get_keywords(tag):
    return tag.has_attr('name') and tag.has_attr('content') and tag['name'] == 'keywords'
def get_price(tag):
    return tag.has_attr('data-asin') and tag.has_attr('data-asin-currency-code') and tag.has_attr('data-asin-price')

def get_original_price(soup):
    pat = re.compile(r'£(?:\d+\.\d*|\.?\d+)')
    found = soup.find_all('td')
    for item in found:
        if item.string and item.string.strip() == 'RRP:':
            for each in item.find_next_siblings():
                val = re.search(pat, each.text.strip())
                if val:
                    return val.group()
    return None

@retry(wait_random_min = 5000, wait_random_max = 10000, stop_max_attempt_number = 3)
def AmzonParser(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'}

    response = requests.get(url, headers = headers)

    # print(response.status_code)

    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'lxml')

    #default value
    NAME = DESC = SALE_PRICE = KEYWORDS = RAW_ORIGINAL_PRICE = None
    RAW_CATEGORY = []
    RAW_BULLETS = []
    #NAME
    k = soup.find(get_name)
    if k != None:
        val = re.search('.*(?=: Amazon.co.uk:)', k['content'])
        if val != None:
            NAME = val.group()
        elif k != '':
            NAME = k
    #DESCRIPTION
    k = soup.find(get_desc)
    if k != None:
        val = re.search('.*(?=: Amazon.co.uk:)', k['content'])
        if val != None:
            DESC = val.group()
        elif k != '':
            NAME = k
    #KEYWORDS
    k = soup.find(get_keywords)
    if k != None:
        KEYWORDS = k['content']
    #PRICE
    k = soup.find(get_price)
    if k != None:
        SALE_PRICE = k['data-asin-price']
    #CATEGORY
    for k in soup.find_all("a", class_="a-link-normal a-color-tertiary"):
        RAW_CATEGORY.append(k.string.strip())
   
    CATEGORY = ' > '.join([i.strip() for i in RAW_CATEGORY]) if RAW_CATEGORY else None
    
    ORIGINAL_PRICE = ''.join(RAW_ORIGINAL_PRICE).strip() if RAW_ORIGINAL_PRICE else None
    #BULLETS
    TAG_BULLETS = soup.find(id = 'feature-bullets')
    bullet_points = TAG_BULLETS.find_all('li')  
    for item in bullet_points:
        RAW_BULLETS.append(item.string.strip())
    BULLETS = ';'.join(RAW_BULLETS).strip() if RAW_BULLETS else None

    #MAPS
    MAPS = []
    k = soup.find('div', id = "imgTagWrapperId")
    for child in k.children:
        if isinstance(child, bs4.element.Tag):
            tagstr = child['data-a-dynamic-image'].replace('{','')
            maps = tagstr.split(',')
            for item in maps:
                if re.search('.*(?=:)', item):
                    MAPS.append(re.search('.*(?=:)', item).group())

    #AVAILABILITY
    k = soup.find('div',id = "availability")
    AVAILABILITY = k.text.strip() if k else None
    ORIGINAL_PRICE = get_original_price(soup)
    data = {
            'STATUS':'OK',
            'NAME':NAME,
            'SALE_PRICE':SALE_PRICE,
            'KEYWORDS':KEYWORDS,
            'CATEGORY':CATEGORY,
            'BULLETS':BULLETS,
            'DESCRIPTION':DESC,
            'AVAILABILITY':AVAILABILITY,
            'URL':url,
            'ORIGINAL_PRICE':ORIGINAL_PRICE,
            'MAPS':MAPS,
            }

    return data

def ReadAsin():
    # AsinList = csv.DictReader(open(os.path.join(os.path.dirname(__file__),"Asinfeed.csv")))
    AsinList = [
    'B00LMDWOEO',
    'B07DDYDP57',
    ]
    extracted_data = []

    for item in AsinList:
        url = "http://www.amazon.co.uk/dp/" + item
        print ("Processing: ", url)

        product = {
            'STATUS':'FAILED',
            'URL':url,
            }
        try:
            product = AmzonParser(url)
        except:
            pass  

        extracted_data.append(product)
        sleep(10)

    with codecs.open('data.json','w', encoding = 'utf-8') as f:
        json.dump(extracted_data, f, indent = 4) 
 
if __name__ == "__main__":
    ReadAsin()