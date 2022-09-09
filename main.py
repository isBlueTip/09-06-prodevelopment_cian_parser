from pprint import pprint
from bs4 import BeautifulSoup
import requests
from string import Template
from datetime import datetime, timedelta
import time
import db
import re
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s')

LOG_NAME = 'cian_scrapper.log'
file_handler = logging.FileHandler(LOG_NAME)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)



months_dict = {
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4,
    'май': 5, 'июнь': 6, 'июль': 7, 'авг': 8,
    'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
}

offer_types = {
    'Вторичка': 'flatSale',
    'Новостройка': 'newBuildingFlatSale',
}

# regions_map = {
#     'Санкт-Петербург': 2,
#     'Новосибирск': 4897,
# }

CITIES_LIST = []

URL_NSK = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=4897&sort=creation_date_desc')
URL_SPB = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=2&sort=creation_date_desc')

CITIES_LIST.append(URL_NSK, URL_SPB)

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
    page = 1
    # page = 15  # TODO change to 1 before prod
    job_finished = False
    while not job_finished:
        url = city_url.substitute(page=page)
        try:
            html_source = requests.get(url, headers=HEADERS).text
        except Exception as error:
            logger.error(f'an error {error} has occurred during parsing {url} page')
        else:
            logger.info(f'getting response from {url} page is successful')
        # with open('html.html', 'r') as file:
        #     html_source = file.read()
        # job_finished = True

        soup_page = BeautifulSoup(html_source, 'lxml')
        # soup_page = BeautifulSoup(html_source, 'html.parser')
        flats_articles = soup_page.find_all('article', class_='_93444fe79c--container--Povoi _93444fe79c--cont--OzgVc')
        for flat in flats_articles:
            raw_timestamp = flat.find('div', class_='_93444fe79c--absolute--yut0v').text
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

            if offer_pub_datetime - parsing_depth < timedelta(0):
                job_finished = True
                break
            link = flat.find('a', class_='_93444fe79c--link--eoxce').attrs.get('href')
            result.append({link: offer_pub_datetime})
        page += 1
        logger.info(f'list parsing - leaving {url} page')
        time.sleep(3)
    return result


def parse_card_info(url_timestamp) -> dict:
    card_info = {}
    url = list(url_timestamp.keys())[0]
    card_info['offer_datetime'] = url_timestamp.get(url)

    print('***   START CARD SCRAPING   ***')
    html_source = requests.get(url, headers=HEADERS).text
    soup_page = BeautifulSoup(html_source, 'lxml')
    # soup_page = BeautifulSoup(html_source, 'html.parser')
    card_info['parse_datetime'] = datetime.now()

    card_info['offer_id'] = int(url.split('/')[-2])
    card_info['category'] = offer_types.get(soup_page.find('span', class_='a10a3f92e9--value--Y34zN').text)

    price = soup_page.find('span', class_='a10a3f92e9--price_value--lqIK0').text
    card_info['price'] = int(price[:-1].replace('\xa0', ''))

    total_area = soup_page.find('div', class_='a10a3f92e9--info-value--bm3DC').text
    card_info['total_area'] = float(total_area.split()[0])

    floor_num = soup_page.find(
        'div', class_='a10a3f92e9--info-value--bm3DC',
        text=re.compile('из *')).text
    card_info['floors_count'] = int(floor_num.split()[-1])
    card_info['floor_num'] = int(floor_num.split()[0])

    address_list = soup_page.find('address', class_='a10a3f92e9--address--F06X3').findChildren()
    card_info['city'] = address_list[1].text
    card_info['street'] = address_list[3].text[:-4]
    card_info['house'] = address_list[4].text

    building_about = soup_page.find_all('div', class_='a10a3f92e9--value--G2JlN')
    card_info['year_house'] = int(building_about[0].text)
    card_info['house_material_type'] = building_about[1].text

    coordinates_script = soup_page.find('script', type='text/javascript', text=re.compile('"coordinates":*')).string
    card_info['lat'] = float(re.search('"lat":(\d+)(\.)(\d+)', coordinates_script).group(0).split(':')[-1])
    card_info['lon'] = float(re.search('"lng":(\d+)(\.)(\d+)', coordinates_script).group(0).split(':')[-1])

    print('***   CARD SCRAPING IS DONE   ***')
    return card_info


def search_or_create_building_entry(object_data: dict, connection) -> int:
    address = f'Россия, {card_info.get("city")}, улица {card_info.get("street")}, {card_info.get("house")}'
    search_building = f'''
    SELECT building.building_id
    FROM building
    WHERE building.address = "{address}";
    '''
    object_entry = db.read_query(connection, query=search_building)
    if len(object_entry):
        print('***   BUILDING ENTRY DOES EXIST   ***')
        building_id = int(object_entry[0][0])
    else:
        print('***   CREATING BUILDING ENTRY   ***')

        city = object_data.get('city')
        lat = object_data.get('lat')
        lon = object_data.get('lon')
        year_house = object_data.get('year_house')
        floors_count = object_data.get('floors_count')
        house_material_type = object_data.get('house_material_type')

        create_building = f'''
        INSERT INTO building (location, lat, lon, address, year_house, floors_count, house_material_type) VALUES
        ("{city}", {lat}, {lon}, "{address}", {year_house}, {floors_count}, "{house_material_type}");
        '''
        db.execute_query(connection, query=create_building)
        # building_id = connection.cursor().lastrowid
        building_id = search_or_create_building_entry(object_data, connection)  # TODO добывать id по-человечески!
    return building_id


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
    pass


def create_or_update_offer_entry(object_data: dict, connection):
    pprint(object_data)
    building_id = search_or_create_building_entry(object_data, connection)
    # offer_id = object_data.get('offer_id')
    offer_id = 8
    query = f'''
    SELECT offer.offer_id
    FROM offer
    WHERE offer_id = {offer_id};
    '''
    object_entry = db.read_query(connection, query=query)
    if len(object_entry):
        return f'object {offer_id} updated successfully'
        # print('***   UPDATING OFFER ENTRY   ***')
    else:
        # print('***   CREATING OFFER ENTRY   ***')
        category = object_data.get('category')
        price = object_data.get('price')
        total_area = object_data.get('total_area')
        floor_num = object_data.get('floor_num')
        offer_datetime = object_data.get('offer_datetime').strftime("%Y-%m-%d %H:%M:%S")
        parse_datetime = object_data.get('parse_datetime').strftime("%Y-%m-%d %H:%M:%S")

        create_offer = f'''
        INSERT INTO offer (offer_id, category, price, total_area, floor_num, parse_datetime, offer_datetime, building_id) VALUES
        ({offer_id}, "{category}", {price}, {total_area}, {floor_num}, "{parse_datetime}", "{offer_datetime}", {building_id});
        '''
        db.execute_query(connection, create_offer)
        return f'object {offer_id} created successfully'


if __name__ == '__main__':
    flats_links = []
    for city_url in CITIES_LIST:
        try:
            flats_links += parse_urls_from_paginated(city_url, parsing_depth=2)
        except Exception as error:
            logger.error(f'an error {error} has occurred during link list parsing, link = {city_url}')
    try:
        connection = db.create_db_connection(db.HOST_NAME, db.USERNAME,
                                             db.PASSWORD, db.DB_NAME)
    except Exception as error:
        logger.error(f'an error {error} has occurred during establishing connection to db')
    # card_info = parse_card_info(flats_links[0])
    # create_or_update_offer_entry(card_info, connection)

    for flat in flats_links:
        try:
            card_info = parse_card_info(flat)
        except Exception as error:
            logger.error(f'an error {error} has occurred during object list parsing, object = {flat}')
        try:
            status = create_or_update_offer_entry(card_info, connection)
        except Exception as error:
            logger.error(f'an error {error} has occurred during object list parsing, object = {card_info}')
        else:
            logger.info(f'another object ahs been added to db with status: {status}')
        time.sleep(3)

