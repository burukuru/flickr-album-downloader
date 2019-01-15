#!/usr/bin/python3

import flickrapi
import json
import os
import urllib
import urllib.parse
import csv
import configparser
from multiprocessing import Pool as ThreadPool

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
        else:
            print (f"Creation of directory {dest_dir} succeeded.")

    def download_all_albums(self):
        # Create parent dir
        self.make_dir(self.dest_dir)

        pool = ThreadPool(2)
        results = pool.map(self.download_album, [self.sets['photosets']['photoset'][0], self.sets['photosets']['photoset'][1]])

    def download_album(self, set):
        print(set['title']['_content'])

        # Create album directory
        album_title = set['title']['_content']
        album_dir = os.path.join(self.dest_dir, album_title)
        self.make_dir(album_dir)

        photos = self.flickr_etree.walk_set(set['id'], extras='url_o')

        # TODO
        # - write album API info to file
        # album_api_response = open(os.path.join(self.dest_dir, 'album_api_response.txt'), 'w')
        # album_api_response.write(photos)

        # Create index to order photos
        index = 1
        try:
            os.remove(os.path.join(album_dir, 'album.csv'))
        except:
            print('album.csv does not exist.')

        csvfile = open(os.path.join(album_dir, 'album.csv'), 'a')
        csvwriter = csv.writer(csvfile)

        for photo in photos:
            url = photo.get('url_o')
            print(f"{album_title}: {url}")
            url_ = urllib.parse.urlparse(url)
            filename = str(index) + '_' + os.path.basename(url_.path)
            title = photo.get('title')

            # Write photo title to CSV file
            csvwriter.writerow([str(index), filename, title])
            full_dest_path = os.path.join(album_dir, filename)
            # Download file
            try:
                urllib.request.urlretrieve(url, full_dest_path)
                index += 1
            except urllib.error.ContentTooShortError as e:
                print(f"{album_title}: {e.msg} - {e.content}")
        csvfile.close()

def main():
    fad = FAD()
    fad.download_all_albums()

if __name__ == '__main__':
    main()
