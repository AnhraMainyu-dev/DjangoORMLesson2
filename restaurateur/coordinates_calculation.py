import requests
from geopy import distance
from foodcartapp.models import Address


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def fetch_coordinates_for_addresses(yandex_apikey, addresses):
    known_addresses = Address.objects.filter(address__in=addresses)
    known_address_strings = {address.address for address in known_addresses}
    not_known_addresses = set(addresses) - set(known_address_strings)

    new_addresses = []
    for address in not_known_addresses:
        try:
            coordinates = fetch_coordinates(yandex_apikey, address)
        except requests.exceptions.RequestException:
            coordinates = None

        lat, lon = None, None
        if coordinates:
            lon, lat = coordinates

        new_addresses.append(Address(address=address, lat=lat, lon=lon))

    Address.objects.bulk_create(new_addresses)

    coordinates_by_address = {}
    for address in list(known_addresses) + new_addresses:
        if address.lat is None or address.lon is None:
            coordinates_by_address[address.address] = None
        else:
            coordinates_by_address[address.address] = (address.lat, address.lon)

    return coordinates_by_address

def get_distance(coordinates_1, coordinates_2):
    return distance.distance(coordinates_1, coordinates_2).km

