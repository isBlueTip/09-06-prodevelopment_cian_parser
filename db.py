import mysql.connector
from mysql.connector import Error
import pandas as pd

HOST_NAME = 'localhost'
USERNAME = 'root'
PASSWORD = 'root'
DB_NAME = 'real_estate_objects'


def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password
        )
        print('MySQL Database connection successful')
    except Error as err:
        print(f'Error: {err}')

    return connection


def create_database(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print('Database created successfully')
    except Error as err:
        print(f'Error: {err}')


def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")

def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")


if __name__ == '__main__':
    create_building_table = '''
    CREATE TABLE building (
      building_id INT PRIMARY KEY,
      location VARCHAR(30),
      lat VARCHAR(30),
      lon VARCHAR(30),
      address VARCHAR(70) UNIQUE,
      year_house INT(4),
      floors_count INT(3),
      house_material_type VARCHAR(20)
      );
     '''
    create_offer_table = '''
    CREATE TABLE offer (
      offer_id INT PRIMARY KEY,
      category VARCHAR(30) NOT NULL,
      price INT(10) NOT NULL,
      total_area FLOAT(10) NOT NULL,
      floor_num INT(3),
      parse_datetime DATE NOT NULL,
      offer_datetime DATE NOT NULL,
      address VARCHAR(70) UNIQUE
      );
     '''
    pop_building = '''
    INSERT INTO building (location, lat, lon, address, year_house, floors_count, house_material_type) VALUES
        ('Новосибирск', 18.15, 20.16, 'Россия, Новосибирск, улица Дуси Ковальчук, 238', 2013, 16, 'Панельный');
    '''
    pop_offer = '''
    INSERT INTO offer (offer_id, category, price, total_area, floor_num, offer_datetime, building_id) VALUES
        (277952875, 'flatSale', 15000000, 200.16, 8, '2016-09-13 00:00:00', 2);
    '''

    # first_name
    # VARCHAR(40)
    # NOT
    # NULL,
    # last_name
    # VARCHAR(40)
    # NOT
    # NULL,
    # language_1
    # VARCHAR(3)
    # NOT
    # NULL,
    # language_2
    # VARCHAR(3),
    # dob
    # DATE,
    # tax_id
    # INT
    # UNIQUE,
    # phone_no
    # VARCHAR(20)

    # create_database_query = 'CREATE DATABASE real_estate_objects'
    # connection = create_server_connection(HOST_NAME, USERNAME, PASSWORD)
    # create_database(connection, create_database_query)

    connection = create_db_connection(HOST_NAME, USERNAME, PASSWORD, DB_NAME)
    # execute_query(connection, pop_building)
    execute_query(connection, pop_offer)
    # connection.close()
