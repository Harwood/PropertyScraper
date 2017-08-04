#! /usr/bin/env python3

"""Airbnb listing scrapping
"""

import sys
from lxml import html
import json
from collections import namedtuple
import requests

__author__ = "Carter Harwood"
__copyright__ = "2017"
__credits__ = ["Carter Harwood"]
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Carter Harwood"
__email__ = "rob@spot.colorado.edu"
__status__ = "Prototype"

# Source: https://stackoverflow.com/a/15882054
def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)


class PropertyScrapper(object):
    """Handles scrapping Airbnb pages and pulling out listing details

    Attributes:
        site_url: web url of Airbnb listing
    """

    def __init__(self, url):
        """Inits PropertyScrapper with url of listing"""
        try:
            self.site_url = url
            self.html = self.__set_full_site_html()
            self.listing = self.__set_listing()
        except requests.exceptions.MissingSchema:
            print("Invalid URL")
            exit()

    def __set_full_site_html(self):
        """Retreives full html contents of site_url"""
        return requests.get(self.site_url)

    def get_full_site_html(self):
        """Returns full html contents of site_url"""
        return self.html

    def __get_full_site_json(self):
        """Extracts json object from site html"""
        page = self.get_full_site_html()
        tree = html.fromstring(page.content)
        react_items = tree.xpath("//script[@type='application/json']")

        #The substring is used to remove surrounding <!-- -->
        return json.loads(react_items[2].text[4:-3])

    def get_listing_json(self):
        """Pulls only json related to listing

        NOTE: This is required before calling json2obj() as
        json['bootstrapData']['headerParams'] contains keys
        that can not be converted. Ex: shared.Home
        """
        return self.__get_full_site_json()['bootstrapData']['listing']

    def __set_listing(self):
        """Sets self.listing"""
        return json2obj(json.dumps(self.get_listing_json()))

    def get_listing(self):
        """Returns self.listing"""
        return self.listing


def print_info(info):
    """Prints individual point of info"""
    for i in info:
        print(i)
    print("")


def print_listing(listing, info=[]):
    """Defines and prints desired listing information

    See sample.json for full list of available listing information
    """
    info.append(("Name:", "   " + listing.name))
    info.append(("Market:", "   " + listing.market))
    info.append(("Rating:", "   " + str(listing.review_details_interface.review_score) + "/100 - " + str(listing.review_details_interface.review_count) + " reviews"))
    info.append(("Property Type:",
        "   " + listing.room_and_property_type))
    info.append(("At a Glance:",
        "   " + listing.bed_label,
        "   " + listing.bathroom_label,
        "   Guests - " + listing.guest_label,
        ))
    info.append(("Price:", "   " + listing.price_formatted_for_embed))
    info.append(("Photo:", "   " + listing.photos[0].large_cover.split('?')[0]))
    info.append(("Description:", "   " + listing.description))

    for i in info:
        print_info(i)

    print("Amenities:")
    for a in listing.listing_amenities:
        if a.is_present:
            print("   " + a.name)

def usage_print(argv):
    """Prints cli usage info"""
    print("Usage:")
    print(argv[0] + " <listing_url>")
    print()

def main(argv):
    """Main"""
    ps = PropertyScrapper(argv[1])
    print_listing(ps.listing)


if __name__ == "__main__":
    """Entry and argv count check"""
    if len(sys.argv) == 2:
        main(sys.argv)
    else:
        usage_print(sys.argv)
        exit
