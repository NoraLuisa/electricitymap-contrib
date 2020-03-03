#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 17:14:32 2020

@author: nemmermann
"""

#importing all needed packages
import numpy as np
from bs4 import BeautifulSoup
from collections import defaultdict

import arrow
import logging, os, re
import requests
import xmltodict
import datetime
import sys
import argparse
import json
import pathlib

import pandas as pd

from parsers.lib.validation import validate
from parsers.lib.utils import sum_production_dicts

#setting security token
os.environ['ENTSOE_TOKEN'] = '3ba5596a-5e43-4937-8f69-33d18235d233'

#importing vie parsers.ENTSOE.py
from parsers.ENTSOE import *
from utils.ENTSOE_capacity_update import *

countrywise_data = {}
exchange_data = {}

for country in ENTSOE_DOMAIN_MAPPINGS:
    print('The country is:')
    print(country)
    countrywise_data[country] = {}
    try:
        countrywise_data[country]['consumption'] = fetch_consumption(country, session=None,
                    target_datetime=None, logger = logging.getLogger(__name__))
    except QueryError:
        countrywise_data[country]['consumption'] = None
    try:
        countrywise_data[country]['production'] = fetch_production(country, session=None,
                    target_datetime=None, logger=logging.getLogger(__name__))
    except QueryError:
        countrywise_data[country]['production'] = None
    try:
        countrywise_data[country]['price'] = fetch_price(country, session=None,
                    target_datetime=None, logger=logging.getLogger(__name__))
    except QueryError:
        countrywise_data[country]['price'] = None
    try:
        countrywise_data[country]['generation_forecast'] = fetch_generation_forecast(country,
                     session=None, target_datetime=None, logger=logging.getLogger(__name__))
    except QueryError:
        countrywise_data[country]['generation_forecast'] =  None
    try:
        countrywise_data[country]['consumption_forecast'] = fetch_consumption_forecast(country,
                    session=None, target_datetime=None, logger=logging.getLogger(__name__))
    except QueryError:
        countrywise_data[country]['consumption_forecast'] =  None
    try:
        countrywise_data[country]['wind_solar_forecast'] = fetch_wind_solar_forecasts(country,
                    session=None, target_datetime=None, logger=logging.getLogger(__name__))
    except QueryError:
        countrywise_data[country]['wind_solar_forecast'] = None
    
    #for exchange_country in ENTSOE_DOMAIN_MAPPINGS,3:
    #this is not symmetric!
    for exchange_country in ENTSOE_DOMAIN_MAPPINGS:
        print(exchange_country)
        exchange_data[country] = {}
        exchange_data[country][exchange_country] = {}
        try:
            exchange_data[country][exchange_country]['exchange'] = fetch_exchange(country,
                        exchange_country, session=None, target_datetime=None, logger=logging.getLogger(__name__))
        except QueryError:
            exchange_data[country][exchange_country]['exchange'] = None
        try:
            exchange_data[country][exchange_country]['exchange_forecast'] = fetch_exchange_forecast(country,
                        exchange_country, session=None, target_datetime=None, logger=logging.getLogger(__name__))
        except QueryError:
            exchange_data[country][exchange_country]['exchange_forecast'] = None

aggregated_production = {}
for zone in ZONE_KEY_AGGREGATES:
    print(zone)
    aggregated_production[zone] = fetch_production_aggregate(zone, session=None,
                         target_datetime=None, logger=logging.getLogger(__name__))

#Fehler im Code von electricitymap?
production_per_units = {}
for zone in ENTSOE_EIC_MAPPING:
    print(zone)
    production_per_units[zone] = fetch_production_per_units(zone, session=None,
                        target_datetime=None, logger=logging.getLogger(__name__))


#importing via utils.ENTSOE_capacity_update.py
print('starting capacity update...')
api_token = os.environ['ENTSOE_TOKEN']
zonesfile = pathlib.Path(__file__).parent / "config" / "zones.json"
if not os.path.exists(zonesfile):
    print("ERROR: Zonesfile {} does not exist.".format(zonesfile),
          file=sys.stderr)
    sys.exit(1)

u_data = {}
u_aggregated_data = {}

for country in ENTSOE_DOMAIN_MAPPINGS:
    print(country)
    try:
        u_data[country] = parse_from_entsoe_api(country, api_token)
    except:
        continue
    u_aggregated_data[country] = aggregate_data(u_data[country])

    print("Aggregated capacities: {}".format(json.dumps(u_aggregated_data[country])))
    print("Updating zone {}".format(country))

    update_zone(country, u_aggregated_data[country], zonesfile)