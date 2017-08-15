#! /usr/bin/env python3

"""Airbnb listing scraping
"""

import sys, threading
import json
from collections import namedtuple
import pickle
try:
    import Queue
except ImportError:
    import queue as Queue
import requests
import sqlite3

import click
from lxml import html
# We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
# the libcurl tutorial for more info.
try:
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except ImportError:
    pass
import validators


__author__     = "Carter Harwood"
__copyright__  = "2017"
__credits__    = ["Carter Harwood"]
__license__    = "MIT"
__version__    = "0.0.3"
__maintainer__ = "Carter Harwood"
__email__      = "Harwood@users.noreply.github.com"
__status__     = "Prototype"

# Source: https://stackoverflow.com/a/15882054
def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)


class PropertyScraper(object):
    """Handles scraping Airbnb pages and pulling out listing details

    Attributes:
    site_url: web url of Airbnb listing
    """

    def __init__(self, url):
        """Inits PropertyScraper with url of listing"""
        try:
            self.site_url = url
            self.html = self.__set_full_site_html()
            self.listing = self.__set_listing()
        except requests.exceptions.MissingSchema:

            print("Invalid URL (?)", url)
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

        # The substring is used to remove surrounding <!-- -->
        try:
            return json.loads(react_items[2].text[4:-3])
        except IndexError:
            sys.stderr.write('Experiencing throttling from Airbnb. Stopping.')
            sys.exit()

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


class DownloadManager(object):
    """Handles init and threading of scraping
    """

    class Worker(threading.Thread):
        """Thread worker
        """

        def __init__(self, db, queue):
            """Constructor"""
            threading.Thread.__init__(self)
            self.db = db
            self.db_conn = sqlite3.connect(self.db, check_same_thread = False)
            self.queue = queue

        def __store_db(self, url, listing):
            """Insert listing into db"""
            c = self.db_conn.cursor()

            amenities = []

            for amenity in listing.listing_amenities:
                if amenity.is_present:
                    amenities.append(amenity.name)

            c.execute('insert into listings values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (url,
                       listing.name,
                       listing.market,
                       str(listing.review_details_interface.review_score),
                       str(listing.review_details_interface.review_count),
                       listing.room_and_property_type,
                       listing.bed_label,
                       listing.bathroom_label,
                       listing.guest_label,
                       listing.price_formatted_for_embed,
                       listing.photos[0].large_cover.split('?')[0],
                       listing.description,
                       ','.join(amenities)))
            self.db_conn.commit()
            c.close()

        def run(self):
            """Thread Main"""
            while 1:
                try:
                    url = self.queue.get_nowait()
                except Queue.Empty:
                    break

                ps = PropertyScraper(url)
                self.__store_db(url, ps.listing)


    def __init__(self, db, conn, urls):
        """Constructor"""
        self.db = db
        self.db_conn = sqlite3.connect(self.db)
        self.__init_db()

        self.conn = conn
        self.urls = urls
        self.queue = self.__process_input()
        self.threads = []


    def __init_db(self):
        """Setup db if file does not already exists"""
        c = self.db_conn.cursor()
        try:
            # Create table
            c.execute('''create table listings (url text, name text,
                      market text, rating num, review_count num, type text,
                      bed text, bath text, guest text, price text,
                      photo_url text, description text, amenities text)''')
            self.db_conn.commit()
        except sqlite3.OperationalError:
            pass
        c.close()


    def __process_input(self):
        """Builds queue from input urls"""
        queue = Queue.Queue()

        print('Processing urls...')
        input = []

        try:
            input = click.open_file(self.urls, 'r')
        except FileNotFoundError:
            if validators.url(self.urls):
                input.append(self.urls.strip())

        with click.progressbar(input) as url_file:
            for url in url_file:
                url = url.strip()

                if not url or url[0] == "#":
                    continue

                queue.put(url)

        return queue


    def run(self):
        """Spawns threads based number of urls and desired concurrent threads.
        """
        try:
            assert self.queue.queue, "no URLs given"
        except AssertionError:
            sys.stderr.write('No URLs given')
            sys.exit()


        n_conn = min(self.conn, len(self.queue.queue))
        try:
            assert 1 <= n_conn <= 10000, "invalid number of concurrent connections"
        except AssertionError:
            sys.stderr.write('invalid number of concurrent connections')

        for url in range(n_conn):
            thread = self.Worker(self.db, self.queue)
            thread.start()

            self.threads.append(thread)

        print('Scraping begins...')

        with click.progressbar(self.threads) as threads:
            for thread in threads:
                thread.join()



def read_urls_file(file):
    """Read urls from file"""
    with open(file) as f:
        for line in f:
            print(line, __is_valid_url(line))

def __is_valid_url(string):
    """ """
    return validators.url(string)

def __handle_any_missing_modules():
    """Prints error when required python modules are missing"""
    if missing_modules:
        sys.stderr.write('Missing required modules. Fix:')
        sys.stderr.write('   pip3 install ', ' '.join(missing_modules))
        sys.exit()


@click.command()
@click.option('--conn',
              default=10,
              nargs=1,
              help='Number of simultaneous connections, defaults to 10.')
@click.option('--db',
              default='listings.db',
              type=click.Path(exists=False,
                              file_okay=True,
                              dir_okay=False,
                              writable=True,
                              readable=False),
              help='SQLite database to create/use, defaults to listings.db.')
@click.argument('file',
                nargs=1)
def main(conn, db, file):
    """Main"""

    dm = DownloadManager(db, conn, file)
    dm.run()

if __name__ == "__main__":
    """Entry point"""
    main()
