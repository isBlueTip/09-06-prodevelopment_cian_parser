import json
import logging
import re
import time
from datetime import datetime, timedelta
from string import Template

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

import db

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(lineno)d | %(message)s')

LOG_NAME = '/home/bluetip/dev/test_tasks/09-06-prodevelopment_cian_parser/cian_scrapper.log'
file_handler = logging.FileHandler(LOG_NAME)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


building_material_types = {
    'monolithBrick': 'Монолитно-кирпичный',
    'panel': 'Панельный',
    'brick': 'Кирпичный',
    'monolith': 'Монолитный',
    'stalin': 'Сталинка',
}

# regions_map = {
#     'Санкт-Петербург': 2,
#     'Новосибирск': 4897,
# }

CITIES_LIST = []

URL_NSK = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=4897&sort=creation_date_desc')
URL_SPB = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=2&sort=creation_date_desc')

CITIES_LIST.append(URL_NSK)
CITIES_LIST.append(URL_SPB)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'}


def search_or_create_building_entry(object_data: dict, connection) -> int:
    address = object_data.get('address')
    search_building = f'''
    SELECT building.building_id
    FROM building
    WHERE building.address = "{address}";
    '''
    object_entry = db.read_query(connection, query=search_building)
    if len(object_entry):  # building does exist
        building_id = int(object_entry[0][0])
    else:  # create building entry
        location = object_data.get('location')
        lat = object_data.get('lat')
        lon = object_data.get('lon')
        year_house = object_data.get('year_house')
        floors_count = object_data.get('floors_count')
        house_material_type = object_data.get('house_material_type')

        create_building = f'''
        INSERT INTO building (location, lat, lon, address, year_house, floors_count, house_material_type) VALUES
        ("{location}", {lat}, {lon}, "{address}", {year_house}, {floors_count}, "{house_material_type}");
        '''
        building_id = db.execute_query(connection, query=create_building)
        logger.info(f'building {address} created')
    return building_id


def create_or_update_offer_entry(object_data: dict, connection):
    building_id = search_or_create_building_entry(object_data, connection)

    offer_id = object_data.get('offer_id')
    category = object_data.get('category')
    price = object_data.get('price')
    total_area = object_data.get('total_area')
    floor_num = object_data.get('floor_num')
    offer_datetime = object_data.get('offer_datetime').strftime("%Y-%m-%d %H:%M:%S")
    parse_datetime = object_data.get('parse_datetime').strftime("%Y-%m-%d %H:%M:%S")

    query = f'''
    SELECT offer.offer_id
    FROM offer
    WHERE offer_id = {offer_id};
    '''
    object_entry = db.read_query(connection, query=query)
    if len(object_entry):
        update_offer = f'''
        UPDATE offer
        SET category="{category}", price={price}, total_area={total_area}, floor_num={floor_num}, parse_datetime="{parse_datetime}", offer_datetime="{offer_datetime}", building_id={building_id} 
        WHERE offer_id = {offer_id};
        '''
        db.execute_query(connection, update_offer)
        logger.info(f'offer {offer_id} updated')
        return f'object {offer_id} updated successfully'
    else:
        create_offer = f'''
        INSERT INTO offer (offer_id, category, price, total_area, floor_num, parse_datetime, offer_datetime, building_id) VALUES
        ({offer_id}, "{category}", {price}, {total_area}, {floor_num}, "{parse_datetime}", "{offer_datetime}", {building_id});
        '''
        db.execute_query(connection, create_offer)
        logger.info(f'offer {offer_id} created')
        return offer_id


def get_html(url: str) -> str:
    session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    result = session.get(url, headers=HEADERS, timeout=15).text
    return result


def parse_paginated_offers(connection, city_url, parsing_depth: int) -> int:  # TODO insert city_name instead of link
    failed_items = []
    offer_cnt = 0
    country = 'Россия'
    parsing_start = datetime.now()
    parsing_depth = parsing_start - timedelta(days=parsing_depth)
    page = 1
    while 1:
        url = city_url.substitute(page=page)
        try:
            html_source = get_html(url)
        except Exception as error:
            logger.error(f'an error "{error}" has occurred during parsing {url} page')
            continue
        else:
            logger.info(f'response from {url} is OK')

        soup_page = BeautifulSoup(html_source, 'lxml')
        script = soup_page.find_all('script', type='text/javascript')[3].string

        script = script.split(').concat([')[-1]
        script = script.split(']);')[0]

        delimiter = '{"key"'
        dict_list = [delimiter + obj for obj in script.split(delimiter) if obj]
        offers = dict_list[-1]
        offers = json.loads(offers).get('value').get('results').get('offers')
        logger.info(f'offers number found on page {url} = {len(offers)}')

        for offer in offers:
            try:
                object_data = {}
                raw_timestamp_creation = offer.get('creationDate').split('.')[:-1][0]
                offer_datetime = datetime.strptime(raw_timestamp_creation, '%Y-%m-%dT%H:%M:%S')
                if offer_datetime - parsing_depth < timedelta(0):
                    break
                object_data['offer_datetime'] = offer_datetime
                object_data['parse_datetime'] = datetime.now()

                object_data['offer_id'] = offer.get('cianId')
                object_data['category'] = offer.get('category')

                object_data['price'] = offer.get('bargainTerms').get('price')
                object_data['total_area'] = offer.get('totalArea')
                object_data['floor_num'] = offer.get('floorNumber')

                geo = offer.get('geo')
                object_data['lat'] = geo.get('coordinates').get('lat')
                object_data['lon'] = geo.get('coordinates').get('lng')

                address = geo.get('address')
                object_data['address'] = f'{country}'
                cnt = 0
                for item in address:
                    if item.get('type') == 'location' and cnt < 2:
                        object_data['location'] = item.get('fullName')
                        cnt += 1
                    if item.get('isFormingAddress'):
                        object_data['address'] += ', '
                        object_data['address'] += item.get('fullName')

                building = offer.get('building')
                year_house = building.get('buildYear')
                if year_house is None:
                    try:
                        year_house = building.get('deadline').get('year', 0)
                    except AttributeError:
                        year_house = 0

                object_data['year_house'] = year_house
                material_type = building.get('materialType')
                if material_type is None:
                    object_data['house_material_type'] = ''
                else:
                    object_data['house_material_type'] = building_material_types.get(material_type, material_type)
                object_data['floors_count'] = building.get('floorsCount')

                try:
                    create_or_update_offer_entry(object_data, connection)
                except Exception as error:
                    failed_items.append(object_data)
                    logger.error(f'an {error} has occurred during creating db entry, see "failed_items" list')
                offer_cnt += 1
            except Exception as error:
                failed_items.append(object_data)
                logger.error(f'an {error} has occurred during parsing object, see "failed_items" list')
        else:
            logger.info(f'page # {page} parsing is finished')
            page += 1
            time.sleep(30)
            continue
        break
    if len(failed_items) > 0:
        logger.warning(f'failed items: {failed_items}')
    return offer_cnt


def parse_cities(cities):
    offer_cnt = 0
    try:
        connection = db.create_db_connection(db.HOST_NAME, db.USERNAME,
                                             db.PASSWORD, db.DB_NAME)
    except Exception as error:
        logger.error(f'an error "{error}" has occurred during establishing connection to db')
    else:
        logger.info(f'successfully connected to db')

    for city_url in cities:
        offer_cnt += parse_paginated_offers(connection, city_url, parsing_depth=2)
        logger.info(f'changing city to {city_url}')

    logger.info(f'offers parsing is finished, {offer_cnt} found')


if __name__ == '__main__':
    parse_cities(CITIES_LIST)
