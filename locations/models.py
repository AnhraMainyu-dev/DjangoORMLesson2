import requests
from django.conf import settings
from django.db import models

from .geo_functions import fetch_coordinates


class AddressQuerySet(models.QuerySet):
    def get_coordinates(self, addresses):
        known_addresses = list(self.filter(address__in=addresses))
        known_address_strings = {address.address for address in known_addresses}
        unknown_addresses = set(addresses) - known_address_strings

        new_addresses = self.bulk_create(
            Address.geocode_address(address) for address in unknown_addresses
        )

        return {
            address.address: address.coordinates
            for address in known_addresses + list(new_addresses)
        }


class Address(models.Model):
    address = models.CharField("адрес", max_length=100, unique=True)
    lat = models.FloatField("широта", null=True, blank=True)
    lon = models.FloatField("долгота", null=True, blank=True)

    objects = AddressQuerySet.as_manager()

    class Meta:
        verbose_name = "адрес"
        verbose_name_plural = "адреса"

    def __str__(self):
        return self.address

    @classmethod
    def geocode_address(cls, address):
        try:
            coordinates = fetch_coordinates(settings.YANDEX_API_KEY, address)
        except requests.exceptions.RequestException:
            coordinates = None

        if not coordinates:
            return cls(address=address)

        lon, lat = coordinates
        return cls(address=address, lat=lat, lon=lon)

    @property
    def coordinates(self):
        if self.lat is None or self.lon is None:
            return None
        else:
            return self.lat, self.lon
