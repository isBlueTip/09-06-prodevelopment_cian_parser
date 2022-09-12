from bs4 import BeautifulSoup
import requests
from string import Template
from datetime import datetime, timedelta
import time
import db
import re
import logging
from requests.adapters import HTTPAdapter, Retry
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(lineno)d | %(message)s')

LOG_NAME = 'cian_scrapper.log'
file_handler = logging.FileHandler(LOG_NAME)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


months_dict = {
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4,
    'май': 5, 'июнь': 6, 'июль': 7, 'авг': 8,
    'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
}

# regions_map = {
#     'Санкт-Петербург': 2,
#     'Новосибирск': 4897,
# }

CITIES_LIST = []

URL_NSK = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=4897&sort=creation_date_desc')
URL_SPB = Template('https://cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=$page&region=2&sort=creation_date_desc')

CITIES_LIST.append(URL_NSK)
# CITIES_LIST.append(URL_SPB)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'}


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


def get_html(url: str) -> str:
    session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    # session.get('http://httpstat.us/500')
    result = session.get(url, headers=HEADERS, timeout=15).text
    # result = session.get(url, timeout=15).text
    return result


def parse_paginated_offers(city_url, parsing_depth: int) -> list:  # TODO insert city_name instead of link
    country = 'Россия'
    parsing_start = datetime.now()
    parsing_depth = parsing_start - timedelta(days=parsing_depth)  # TODO change before prod
    # parsing_depth = parsing_start - timedelta(hours=6)
    page = 1
    job_finished = False
    while not job_finished:
        url = city_url.substitute(page=page)
        logger.debug(f'url = {url}')
        try:
            html_source = get_html(url)
        except Exception as error:
            logger.error(f'an error "{error}" has occurred during parsing {url} page')
            continue
        else:
            logger.info(f'response from {url} is OK')

        soup_page = BeautifulSoup(html_source, 'lxml')
        # soup_page = BeautifulSoup(html_source, 'html.parser')
        script = soup_page.find_all('script', type='text/javascript')[3].string

        script = script.split(').concat([')[-1]
        script = script.split(']);')[0]

        delimiter = '{"key"'
        dict_list = [delimiter + obj for obj in script.split(delimiter) if obj]
        offers = dict_list[-1]
        offers = json.loads(offers).get('value').get('results').get('offers')
        logger.info(f'offers number found on page {url} = {len(offers)}')

        for offer in offers:
            logger.debug('**********************************************')
            logger.debug(' ')
            logger.debug(' ')
            logger.debug(' ')
            logger.debug('**********************************************')

            # logger.debug(f'offer = {offer}')

            object_data = {}
            object_data['offer_id'] = offer.get('cianId')
            object_data['category'] = offer.get('category')



            raw_timestamp_creation = offer.get('creationDate')
            logger.debug(f'raw_timestamp_creation type = {type(raw_timestamp_creation)}')
            logger.debug(f'raw_timestamp_creation = {raw_timestamp_creation}')
            # object_data['offer_datetime'] = offer.get('creationDate')
            parse_datetime = datetime.now()

            parse_datetime

            object_data['parse_datetime'] = parse_datetime
            # object_data['parse_datetime'] = datetime.now()



            object_data['price'] = offer.get('bargainTerms').get('price')
            object_data['total_area'] = offer.get('bargainTerms').get('totalArea')
            object_data['floor_num'] = offer.get('bargainTerms').get('floorNumber')

            geo = offer.get('geo')
            # logger.debug(f'geo = {geo}')
            object_data['lat'] = geo.get('coordinates').get('lat')
            object_data['lon'] = geo.get('coordinates').get('lng')

            address = geo.get('address')
            object_data['address'] = f'{country}'
            for item in address:
                if item.get('isFormingAddress'):
                    object_data['address'] += ', '
                    object_data['address'] += item.get('fullName')

            building = offer.get('building')
            year_house = building.get('buildYear')
            if year_house == 'None':
                building.get('deadline').get('year')

            object_data['house_material_type'] = building.get('materialType')
            object_data['floors_count'] = building.get('floorsCount')

            logger.debug(f'object_data = {object_data}')
            # TODO call offer_create
        break
        page += 1
        time.sleep(15)


        # for flat in flats_articles:
        #     raw_timestamp = flat.find('div', class_='_93444fe79c--absolute--yut0v').text
        #     raw_timestamp = raw_timestamp.split()
        #     offer_pub_datetime = datetime.now()
        #     if len(raw_timestamp) > 2:
        #         day = int(raw_timestamp[0])
        #         month = months_dict.get(raw_timestamp[1][:-1])
        #         offer_pub_datetime = offer_pub_datetime.replace(day=day, month=month)
        #     elif raw_timestamp[0] == 'вчера,':
        #         offer_pub_datetime = offer_pub_datetime - timedelta(days=1)
        #     hours_minutes = raw_timestamp[-1].split(':')
        #     hours = int(hours_minutes[0])
        #     minutes = int(hours_minutes[1])
        #     offer_pub_datetime = offer_pub_datetime.replace(hour=hours, minute=minutes)
        #
        #     if offer_pub_datetime - parsing_depth < timedelta(0):
        #         job_finished = True
        #         break
    return None


def parse_card_info(url_timestamp) -> dict:
    card_info = {}
    url = list(url_timestamp.keys())[0]  # TODO uncomment before prod!
    # url = 'https://novosibirsk.cian.ru/sale/flat/278147129/'
    logger.debug(f'url = {url}')
    card_info['offer_datetime'] = url_timestamp.get(url)
    try:
        # html_source = requests.get(url, headers=HEADERS).text
        html_source = get_html(url)
    except Exception as error:
        html_source = ''
        card_info['empty_flag'] = True
        logger.error(f'an error "{error}" has occurred during parsing {url}')
    else:
        logger.info(f'response from {url} is OK')

    # logger.debug(f'html_source = {html_source}')  # TODO

    soup_page = BeautifulSoup(html_source, 'lxml')
    # soup_page = BeautifulSoup(html_source, 'html.parser')
    card_info['parse_datetime'] = datetime.now()

    card_info['offer_id'] = int(url.split('/')[-2])
    # card_info['category'] = offer_types.get(soup_page.find('span', class_='a10a3f92e9--value--Y34zN').text)  # TODO delete?

    price = soup_page.find('span', class_='a10a3f92e9--price_value--lqIK0').text
    card_info['price'] = int(price[:-1].replace('\xa0', ''))

    total_area = soup_page.find('div', class_='a10a3f92e9--info-value--bm3DC').text
    card_info['total_area'] = float(total_area.split()[0].replace(',', '.'))

    floor_num = soup_page.find(
        'div', class_='a10a3f92e9--info-value--bm3DC',
        text=re.compile('из *')).text
    card_info['floors_count'] = int(floor_num.split()[-1])
    card_info['floor_num'] = int(floor_num.split()[0])

    address_list = soup_page.find('address', class_='a10a3f92e9--address--F06X3').findChildren()
    card_info['city'] = address_list[1].text
    # # card_info['street'] = address_list[3].text[:-4]
    # # card_info['house'] = address_list[4].text
    #
    # building_about = soup_page.find_all('div', class_='a10a3f92e9--value--G2JlN')
    # # if len(building_about) == 7:  # if building is not finished
    # #     year_house = int(building_about[0].text)
    # #     house_material_type = building_about[1].text
    # # else:
    # #     year_house = '0'
    # #     house_material_type = '-'
    # # # card_info['year_house'] = year_house
    # # card_info['house_material_type'] = house_material_type

    script = soup_page.find('script', type='text/javascript', text=re.compile('"coordinates":*')).string
    # logger.debug(f'script = {script}')  # TODO

    street = re.search('"street","name":".+?(?=")', script)
    logger.debug(f'street = {street}')
    if street is not None:
        street = street.group(0).split('"')[-1]
    else:
        street = re.search('"mikroraion","name":".+?(?=")', script).group(0).split('"')[-1]
    logger.debug(f'street = {street}')
    house = re.search('"house","name":".+?(?=")', script).group(0).split('"')[-1]
    house = house.replace('\\u002F', '/')
    logger.debug(f'house = {house}')
    category = re.search('"offer":\{"category":".+?(?=")', script).group(0).split('"')[-1]
    logger.debug(f'category = {category}')

    year_house = re.search('"buildYear":.+?(?=,)', script)
    if year_house is not None:
        year_house = year_house.group(0).split(':')[-1]
    else:
        year_house = re.search('"finishDate": {"quarter": 1, "year":.+?(?=})', script)
        if year_house is not None:
            year_house = year_house.group(0).split(':')[-1]
        else:
            year_house = '0'

    logger.debug(f'year_house = {year_house}')


    house_material_type = re.search('"building": \{"materialType": ".+?(?=,)', script)
    if house_material_type is not None:
        house_material_type = house_material_type.group(0).split(':')[-1]
    else:
        house_material_type = '-'


    card_info['street'] = street
    card_info['house'] = house
    card_info['year_house'] = year_house
    card_info['category'] = category
    card_info['house_material_type'] = house_material_type

    card_info['lat'] = float(re.search('"lat":(\d+)(\.)(\d+)', script).group(0).split(':')[-1])
    card_info['lon'] = float(re.search('"lng":(\d+)(\.)(\d+)', script).group(0).split(':')[-1])
    logger.debug(card_info)

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
    # pass


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
        return f'object {offer_id} updated successfully'
    else:
        create_offer = f'''
        INSERT INTO offer (offer_id, category, price, total_area, floor_num, parse_datetime, offer_datetime, building_id) VALUES
        ({offer_id}, "{category}", {price}, {total_area}, {floor_num}, "{parse_datetime}", "{offer_datetime}", {building_id});
        '''
        db.execute_query(connection, create_offer)
        return offer_id


if __name__ == '__main__':
    flats_links = 0
    try:
        connection = db.create_db_connection(db.HOST_NAME, db.USERNAME,
                                             db.PASSWORD, db.DB_NAME)
    except Exception as error:
        logger.error(f'an error "{error}" has occurred during establishing connection to db')
    else:
        logger.info(f'successfully connected to db')

    for city_url in CITIES_LIST:
        # try:
        flats_links += parse_paginated_offers(city_url, parsing_depth=2)
        # except Exception as error:
        #     logger.error(f'an error "{error}" has occurred during link list parsing, link = {city_url}')

    logger.info(f'links parsing is finished, {flats_links} offers found')
    # logger.debug(f'flats_links = {flats_links}')

    for flat in flats_links:
        logger.debug(f'flat = {flat}')
        if not flat.get('empty_flag'):
            try:
                card_info = parse_card_info(flat)
            except Exception as error:
                logger.error(f'an error "{error}" has occurred during object list parsing, object = {flat}')
            try:
                offer_id = create_or_update_offer_entry(card_info, connection)
            except Exception as error:
                logger.error(f'an error "{error}" has occurred during object list parsing, object = {card_info}')
            else:
                logger.info(f'object {offer_id} has been added to db')
            time.sleep(15)
    logger.info(f'parsing task is finished')

