from pprint import pprint
from bs4 import BeautifulSoup
import requests
from string import Template
from datetime import datetime, timedelta
import time

months_dict = {
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4,
    'май': 5, 'июнь': 6, 'июль': 7, 'авг': 8,
    'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
}

regions_map = {
    'Санкт-Петербург': 2,
    'Новосибирск': 4897,
}
URL_NSK = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=4897&sort=creation_date_desc')

# URL_NSK = f'https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p={page}&region=4897&sort=creation_date_desc'
URL_SPB = ''
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36'}


def parse_datetime(raw_datetime: str):
    offer_pub_datetime = raw_datetime.split()
    if len(offer_pub_datetime) > 2:
        day = int(offer_pub_datetime[0])
        month = offer_pub_datetime[1][:-1]
        hours_minutes = offer_pub_datetime[2].split(':')
        hours = int(hours_minutes[0])
        minutes = int(hours_minutes[1])
        offer_pub_datetime = datetime(day=day, month=months_dict[month],
                                      year=parsing_depth.year, hour=hours, minute=minutes)
        return offer_pub_datetime
        # print(offer_pub_datetime - parsing_depth)
        # print(type(timestamp))
        # print(timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute)


def parse_urls_from_paginated(city_url, parsing_depth: int) -> list:  # TODO insert city_name instead of link
    result = []
    PARSING_START = datetime.now()
    parsing_depth = PARSING_START - timedelta(days=parsing_depth)
    page = 14
    job_finished = False
    while not job_finished:
        url = city_url.substitute(page=page)
        print(url)
        html_source = requests.get(url, headers=HEADERS).text
        # soup_page = BeautifulSoup(html_source, 'lxml')
        soup_page = BeautifulSoup(html_source, 'html.parser')
        flats_articles = soup_page.find_all('article', class_='_93444fe79c--container--Povoi _93444fe79c--cont--OzgVc')
        for flat in flats_articles:
            raw_timestamp = flat.find('div', class_='_93444fe79c--absolute--yut0v').text
            print(f'raw timestamp = {raw_timestamp}')
            raw_timestamp = raw_timestamp.split()
            offer_pub_datetime = datetime.now()
            if len(raw_timestamp) > 2:
                day = int(raw_timestamp[0])
                month = raw_timestamp[1][:-1]
                offer_pub_datetime = offer_pub_datetime.replace(day=day, month=month)
            elif raw_timestamp[0] == 'вчера,':
                offer_pub_datetime = offer_pub_datetime - timedelta(days=1)
            hours_minutes = raw_timestamp[-1].split(':')
            hours = int(hours_minutes[0])
            minutes = int(hours_minutes[1])
            offer_pub_datetime = offer_pub_datetime.replace(hour=hours, minute=minutes)
            print(f'offer_pub_datetime = {offer_pub_datetime}')
            print(f'parsing_depth = {parsing_depth}')
            print(f'calculation_result = {offer_pub_datetime - parsing_depth}')
            print('')
            if offer_pub_datetime - parsing_depth < timedelta(0):
                job_finished = True
                break
            link = flat.find('a', class_='_93444fe79c--link--eoxce').attrs.get('href')
            result.append({link: offer_pub_datetime})
        page += 1
        print('*** GO TO NEXT PAGE ***')
        time.sleep(5)
    return result


def search_or_create_building(address: str) -> None:
    pass


def create_offer_entry(url: str):
    search_or_create_building('типа адрес в моём формате')
    'creating db entry'


def parse_card_to_db(url: str):
    create_offer_entry('url from urls list')


if __name__ == '__main__':
    flats_links = parse_urls_from_paginated(URL_NSK, parsing_depth=1)
    print(flats_links)




    # html_source = requests.get(city_url).text
    # soup = BeautifulSoup(html_source, 'lxml')
    # flat = soup.find('div', class_='_93444fe79c--card--ibP42')
    # address_whole = flat.find('div', class_='_93444fe79c--labels--L8WyJ')
    # price = flat.find('div', class_='_93444fe79c--container--aWzpE')
    # flat_summary = flat.find('span', class_='_93444fe79c--color_black_100--kPHhJ _93444fe79c--lineHeight_28px--whmWV _93444fe79c--fontWeight_bold--ePDnv _93444fe79c--fontSize_22px--viEqA _93444fe79c--display_block--pDAEx _93444fe79c--text--g9xAG _93444fe79c--text_letterSpacing__normal--xbqP6')
    # flat_link = flat.find('a', class_='_93444fe79c--link--eoxce').attrs.get('href')
    # print(flat_link)
    # print(flat_link.attrs.get('href'))

