from pprint import pprint
from bs4 import BeautifulSoup
import requests

URL = 'https://novosibirsk.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4897&sort=creation_date_desc'

if __name__ == '__main__':
    html_source = requests.get(URL).text
    soup = BeautifulSoup(html_source, 'lxml')
    # flats = soup.find_all('span', class_='_93444fe79c--link-area--NQqFo')
    flat = soup.find('div', class_='_93444fe79c--card--ibP42')
    address_whole = flat.find('div', class_='_93444fe79c--labels--L8WyJ')
    price = flat.find('div', class_='_93444fe79c--container--aWzpE')
    flat_summary = flat.find('span', class_='_93444fe79c--color_black_100--kPHhJ _93444fe79c--lineHeight_28px--whmWV _93444fe79c--fontWeight_bold--ePDnv _93444fe79c--fontSize_22px--viEqA _93444fe79c--display_block--pDAEx _93444fe79c--text--g9xAG _93444fe79c--text_letterSpacing__normal--xbqP6')
    flat_link = flat.find('a href', class_='_93444fe79c--link--eoxce')
    print(flat_link)
    print(flat_link.text)

    # category
    # lat
    # lon
    ## price
    # total_area
    # floor_num
    # datetime
    # offer_id
    ## address
