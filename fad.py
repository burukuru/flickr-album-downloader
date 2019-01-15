#!/usr/bin/python3

import flickrapi
import json
import os
import urllib
import urllib.parse
import shutil
import csv
import configparser
from multiprocessing import Pool
from ratelimit import limits, sleep_and_retry

# Config
class FAD():

    def __init__(self):
        self.read_config('fad.conf')
        # Connect
        self.flickr = flickrapi.FlickrAPI(self.api_key, self.api_secret, format='parsed-json')
        self.flickr_etree = flickrapi.FlickrAPI(self.api_key, self.api_secret)
        # Get albums
        self.sets = self.flickr.photosets.getList(user_id=self.user_id)

    def read_config(self, configfile):
        config = configparser.ConfigParser()
        config.read(configfile)
        self.api_key = config['flickr']['api_key']
        self.api_secret = config['flickr']['api_secret']
        self.user_id = config['flickr']['user_id']
        self.flickr_url = config['flickr']['flickr_url']
        self.dest_dir = config['flickr']['dest_dir']


    def make_dir(self, dest_dir):
        try:
            os.makedirs(dest_dir, 0o755, exist_ok=True)
        except OSError:
            print (f"Creation of directory {dest_dir} failed.")
            pass
        else:
            print (f"Creation of directory {dest_dir} succeeded.")
            pass

    def download_all_albums(self):
        # Create parent dir
        self.make_dir(self.dest_dir)

        album_and_photolist = [ [set['title']['_content'], list(self.get_photo_list(set['id']))] for set in self.sets['photosets']['photoset'] ]

        pool = Pool(5)
        results = pool.map(self.download_album, album_and_photolist)
        pool.close()
        pool.join()


    def download_album(self, album_and_photolist):
        print(album_and_photolist[0])

        # Create album directory
        album_dir = os.path.join(self.dest_dir, album_and_photolist[0])
        self.make_dir(album_dir)

        # TODO
        # - write album API info to file
        # album_api_response = open(os.path.join(self.dest_dir, 'album_api_response.txt'), 'w')
        # album_api_response.write(photos)

        # Create index to order photos
        index = 1
        try:
            os.remove(os.path.join(album_dir, 'album.csv'))
        except:
            pass
        csvfile = open(os.path.join(album_dir, 'album.csv'), 'a')
        csvwriter = csv.writer(csvfile)

        for photo in album_and_photolist[1]:
            url = photo.get('url_o')
            print(url)
            url_ = urllib.parse.urlparse(url)
            filename = str(index).zfill(3) + '_' + os.path.basename(url_.path)
            title = photo.get('title')

            # Write photo title to CSV file
            csvwriter.writerow([str(index).zfill(3), filename, title])
            full_dest_path = os.path.join(album_dir, filename)
            # Download file
            self.download_photo(url, album_dir, full_dest_path)
            index += 1
        csvfile.close()

    def download_photo(self, url, album_dir, full_dest_path):
        try:
            # urllib.request.urlretrieve(url, full_dest_path)

            # response = urllib.request.urlopen(url)
            # out_file = open(full_dest_path, 'wb')
            # shutil.copyfileobj(response, out_file)
            os.system(f'wget --continue {url} -O "{full_dest_path}" -a "{album_dir}/download.log" --random-wait --waitretry=5 --retry-connrefused --retry-on-host-error')
        except urllib.error.URLError as e:
            print(f"{url} failed to download")
            print(e)

    @sleep_and_retry
    @limits(calls=1, period=1)
    def get_photo_list(self, album_id):
        photos = self.flickr_etree.walk_set(album_id, extras='url_o')
        return photos

def main():
    fad = FAD()
    fad.download_all_albums()

if __name__ == '__main__':
    main()
