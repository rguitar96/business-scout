'''
Script to scout and get general business details in a given location.

Get Google Places API key:
https://developers.google.com/maps/documentation/places/web-service/get-api-key
Get OpenWeatherPortal API key:
https://home.openweathermap.org/api_keys

Optional Google Places parameters (if you want to edit the code):
-keyword: term to be matched against all page indexed content
-language: one of https://developers.google.com/maps/faq#languagesupport
-maxprice: 0-4 from affordable to expensive
-minprice: 0-4 from affordable to expensive
-pagetoken: search with same parameters as former pagetoken
-radius: max distance from location in meters
-rankby: 'prominence'|'distance'
-type: one of https://developers.google.com/maps/documentation/places/web-service/supported_types

'''

import requests
import urllib
import json
import csv
import time

def get_url(base_url, parameters):
    p = urllib.parse.urlencode(parameters)
    final_url = base_url + '?' + p
    return final_url

def get_response(url):
    session = requests.Session()
    response = session.get(url)
    return response

def request_results(base_url, parameters, content_keyword='results'):
    url = get_url(base_url, parameters)
    response = get_response(url)
    content = response.content
    results_json = json.loads(content)
    token = results_json['next_page_token'] if 'next_page_token' in results_json else ''
    results = results_json[content_keyword]

    return results, token

location = input('Enter location:')
search_radius = input('Enter radius in meters:')
keyword = input('Enter keyword: ')
google_api_key = input('Enter Google Places API key (https://developers.google.com/maps/documentation/places/web-service/get-api-key): ')
geocoding_api_key = input('Enter OpenWatherMap Geocoding API key (https://home.openweathermap.org/api_keys): ')

geocoding_base_url = 'https://api.openweathermap.org/geo/1.0/direct'
geocoding_parameters = {'q': location,'limit': 1, 'appid': geocoding_api_key}

geocoding_url = get_url(geocoding_base_url, geocoding_parameters)
response = get_response(geocoding_url)
content = response.content
geocoding_results = json.loads(content)

lat = geocoding_results[0]['lat']
lon = geocoding_results[0]['lon']

place_type = 'establishment'
detailed_fields = ['name','formatted_address','url','formatted_phone_number','website']

places_base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
place_parameters = {
    'keyword': keyword,
    'location': ','.join([str(lat),str(lon)]),
    'radius': search_radius,
    'type': place_type,
    'key': google_api_key
}

# GETTING THE PLACES
places_results = []
new_results, token = request_results(places_base_url, place_parameters)
places_results += new_results

while token:
    print('Paging more results...')
    # https://stackoverflow.com/a/21266061/8817682
    time.sleep(3)
    place_parameters['pagetoken'] = token
    new_results, token = request_results(places_base_url, place_parameters)
    places_results += new_results

with open(location + '-' + keyword + '.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=detailed_fields)

    writer.writeheader()

    # GETTING THE DETAILS
    for place in places_results:
        place_id = place['place_id']
        details_base_url = 'https://maps.googleapis.com/maps/api/place/details/json'
        detailed_parameters = {
            'place_id': place_id,
            'fields': ','.join(detailed_fields),
            'key': google_api_key
        }
        
        detailed_results, _ = request_results(details_base_url,
                                              detailed_parameters,
                                              content_keyword='result')

        print('\n\n *** PROCESSING PLACE DETAILS *** \n')
        row_values = []
        for field in detailed_fields:
            if field in detailed_results:
                print(field + ': ' + detailed_results[field])
                row_values.append(detailed_results[field])
            else:
                print(field + ': not available.')
                row_values.append('-')

        zip_iterator = zip(detailed_fields, row_values)
        row_dict = dict(zip_iterator)

        writer.writerow(row_dict)