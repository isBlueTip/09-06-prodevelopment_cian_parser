from pprint import pprint
from bs4 import BeautifulSoup
import requests
from string import Template
from datetime import datetime, timedelta
import time
import db
import re

months_dict = {
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4,
    'май': 5, 'июнь': 6, 'июль': 7, 'авг': 8,
    'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
}

offer_types = {
    'Вторичка': 'flatSale',
    'Новостройка': 'newBuildingFlatSale',
}

regions_map = {
    'Санкт-Петербург': 2,
    'Новосибирск': 4897,
}

URL_NSK = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=4897&sort=creation_date_desc')

URL_SPB = ''
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36'}


# def parse_datetime(raw_datetime: str):
#     offer_pub_datetime = raw_datetime.split()
#     if len(offer_pub_datetime) > 2:
#         day = int(offer_pub_datetime[0])
#         month = offer_pub_datetime[1][:-1]
#         hours_minutes = offer_pub_datetime[2].split(':')
#         hours = int(hours_minutes[0])
#         minutes = int(hours_minutes[1])
#         offer_pub_datetime = datetime(day=day, month=months_dict[month],
#                                       year=parsing_depth.year, hour=hours, minute=minutes)
#         return offer_pub_datetime
#         # print(offer_pub_datetime - parsing_depth)
#         # print(type(timestamp))
#         # print(timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute)


def parse_urls_from_paginated(city_url, parsing_depth: int) -> list:  # TODO insert city_name instead of link
    result = []
    PARSING_START = datetime.now()
    parsing_depth = PARSING_START - timedelta(days=parsing_depth)
    page = 15  # TODO change to 1 before prod
    job_finished = False
    while not job_finished:
        url = city_url.substitute(page=page)
        print(url)

        # html_source = requests.get(url, headers=HEADERS).text

        with open('html.html', 'r') as file:
            html_source = file.read()
            # file.write(html_source)
        # print(html_source)
        job_finished = True


        soup_page = BeautifulSoup(html_source, 'lxml')
        # soup_page = BeautifulSoup(html_source, 'html.parser')
        flats_articles = soup_page.find_all('article', class_='_93444fe79c--container--Povoi _93444fe79c--cont--OzgVc')
        for flat in flats_articles:
            raw_timestamp = flat.find('div', class_='_93444fe79c--absolute--yut0v').text
            # print(f'raw timestamp = {raw_timestamp}')
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
            # print(f'offer_pub_datetime = {offer_pub_datetime}')
            # print(f'parsing_depth = {parsing_depth}')
            # print(f'calculation_result = {offer_pub_datetime - parsing_depth}')
            # print('')
            if offer_pub_datetime - parsing_depth < timedelta(0):
                job_finished = True
                break
            link = flat.find('a', class_='_93444fe79c--link--eoxce').attrs.get('href')
            result.append({link: offer_pub_datetime})
        page += 1
        # print('*** GO TO NEXT PAGE ***')
        time.sleep(5)
    return result


def search_or_create_building(address: str) -> None:
    pass


def create_offer_entry(url: str):
    search_or_create_building('типа адрес в моём формате')
    'creating db entry'


def parse_card_to_db(url_timestamp, connection):
    url = list(url_timestamp.keys())[0]
    offer_datetime = url_timestamp.get(url)
    print(url)

    html_source = requests.get(url, headers=HEADERS).text
    soup_page = BeautifulSoup(html_source, 'lxml')
    # soup_page = BeautifulSoup(html_source, 'html.parser')
    parse_datetime = datetime.now()  # TODO or during page reading

    offer_id = int(url.split('/')[-2])
    print(f'offer_id = {offer_id}')

    category = offer_types.get(soup_page.find('span', class_='a10a3f92e9--value--Y34zN').text)
    print(f'category = {category}')

    price = soup_page.find('span', class_='a10a3f92e9--price_value--lqIK0').text
    price = price[:-1].strip(' ')
    print(f'price = {price}')

    total_area = soup_page.find('div', class_='a10a3f92e9--info-value--bm3DC').text
    total_area = float(total_area.split()[0])
    print(f'total_area = {total_area}')

    floor_num = soup_page.find('div', class_='a10a3f92e9--info-value--bm3DC', text=re.compile('из *')).text

    floors_count = int(floor_num.split()[-1])
    print(f'floors_count = {floors_count}')
    floor_num = int(floor_num.split()[0])
    print(f'floor_num = {floor_num}')

    address_list = soup_page.find('address', class_='a10a3f92e9--address--F06X3').findChildren()

    print(f'parse_datetime = {parse_datetime}')
    print(f'offer_datetime = {offer_datetime}')
    # print(f'building_id = {building_id}')  # primary key for building table

    # # location = from the above list  # (название города)
    # # coordinates = soup_page.find('path', id='current-offer-svg-a')
    # coordinates = soup_page.find('div', class_='a10a3f92e9--map_container--UEQBG')
    city = address_list[1].text
    street = address_list[3].text[:-4]
    house = address_list[4].text
    address = f'Россия, {city}, улица {street}, {house}'  # (Россия, Новосибирск, улица Дуси Ковальчук, 238)

    # building_about = soup_page.find('div', class_='a10a3f92e9--column--XINlk').findChildren()
    # for child in building_about:
    #     print(f'child = {child.text}')
    building_about = soup_page.find_all('div', class_='a10a3f92e9--value--G2JlN')

    year_house = int(building_about[0].text)
    house_material_type = building_about[1].text

    print('*******************************************************************************************')

    # print(f'location = {address}')
    # print(f'lat = {coordinates}')
    # print(f'lon = {type(coordinates)}')
    print(f'address = {address}')
    print(f'year_house = {year_house}')
    print(f'house_material_type = {house_material_type}')



    # query = f'''
    # SELECT offer.offer_id
    # FROM offer
    # WHERE offer_id = {offer_id};
    # '''
    # object = db.read_query(connection, query=query)
    # if len(object):
    #     print('len == 1')
    #     # update entry only
    # else:
    #     print('len == 0')
    #     # get_or_create building and create offer entry

    # create_offer_entry('url from urls list')
    # db.execute_query(connection, pop_offer)


if __name__ == '__main__':
    flats_links = parse_urls_from_paginated(URL_NSK, parsing_depth=1)
    # connection = db.create_db_connection(db.HOST_NAME, db.USERNAME,
    #                                      db.PASSWORD, db.DB_NAME)
    connection = 'DEBUG STRING'
    parse_card_to_db(flats_links[0], connection)
    # for flat in flats_links:
    #     parse_card_to_db(flat, connection)
    #     sleep(3)
