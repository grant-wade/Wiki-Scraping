"""Scrapes data off of a wikipedia category collecting, a summary, image and page categories"""
# ======================================= #
# Author: Grant Wade (grant.wade@wsu.edu) #
# wikipedia-scraping.py scrapes data off  #
# of wikipedia using their API            #
# ======================================= #

# ======================== #
# Standard library modules #
# ======================== #
import os
import sys
import sqlite3
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


# =================== #
# Third party modules #
# =================== #
import requests


# ================================================== #
# Global Variables: The search vars maximise results #
# ================================================== #
WIKI_URL = "https://en.wikipedia.org/wiki/"
WIKI_API_URL = "https://en.wikipedia.org/w/api.php?"
SUMMARIES_SEARCH_VARS = "action=query&format=xml&prop=extracts&explaintext&exintro&titles="
CATEGORY_SEARCH_VARS = "action=query&list=categorymembers&format=xml&cmlimit=500&cmtitle=Category:"
TITLE_CAT_SEARCH_VARS = "format=xml&action=query&prop=categories&cllimit=500&titles="
PAGE_VIEWS_SEARCH_VARS = "format=xml&action=query&prop=pageviews&titles="
IMAGE_SEARCH_VARS = "action=query&prop=pageimages&pithumbsize=1000&format=xml&titles="


# =================================================== #
# Utility functions: status, create dir, sanatize url #
# =================================================== #
def progress_update(value, endvalue, title=''):
    """simple function to update stdout with current count"""
    sys.stdout.write("\r%i / %i %s" % (value, endvalue, title))
    sys.stdout.flush()


def create_image_directory():
    """creates a directory for images to be stored"""
    if not os.path.exists("Images"):
        os.makedirs("Images")


def sanatize_url(url):
    """replace special characters in url with proper ASCII escapes"""
    return urllib.parse.quote(url)


# ================================================ #
# Function that gather data with the wikipedia API #
# ================================================ #
def get_all_titles_from_catagory(category, titles, categories):
    """get every page from a wikipedia category and all sub categories recursivly"""
    wiki_request = requests.get(WIKI_API_URL+CATEGORY_SEARCH_VARS+category)
    categories.append(category) # add current category to list so no loops happen
    root = ET.fromstring(wiki_request.content)
    if root.find('continue') != None: # Runs if the results has a continue page (more than 500 results)
        continue_id = 'cmcontinue="' + root.find('continue').attrib['cmcontinue'] + '"'
        get_all_titles_from_catagory(category+"&"+continue_id, titles, categories)
    children = root.find('query/categorymembers') # find all category elements
    for child in children:
        title = child.attrib['title'].split(':', 1) # figure out if it's a category, page, etc
        if title[0] == "Category" and title[1] not in categories:
            print("\t-", title[1])
            get_all_titles_from_catagory(title[1], titles, categories)
        elif int(child.attrib['ns']) == 0: # if ns value is 0 (page) add to titles
            titles.append(child.attrib['title'])


def get_summaries(titles, title_data):
    """get summary from all wikipedia pages with a title in titles"""
    length = len(titles)
    index = 0
    while index < length:
        multi_title = sanatize_url(titles[index])
        for _ in range(20): # Collect 20 titles at a time
            if index < length:
                multi_title += '|' + sanatize_url(titles[index])
            else:
                break
            index += 1
        progress_update(index, length)
        wiki_request = requests.get(WIKI_API_URL+SUMMARIES_SEARCH_VARS+multi_title)
        root = ET.fromstring(wiki_request.content) # get 20 summaries
        pages = root.findall('query/pages/page') # find all pages
        for page in pages: # Add summaries to dict
            title_data[page.attrib['title']].append(page.find('extract').text)


def get_categories_from_title(titles, title_data):
    """get every category from every title in titles"""
    length = len(titles)
    index = 0
    while index < length:
        multi_title = sanatize_url(titles[index])
        for _ in range(20): # Collect 20 titles at a time
            if index < length:
                multi_title += '|' + sanatize_url(titles[index])
            else:
                break
            index += 1
        progress_update(index, length)
        wiki_request = requests.get(WIKI_API_URL+TITLE_CAT_SEARCH_VARS+multi_title)
        root = ET.fromstring(wiki_request.content)
        pages = root.findall('query/pages/page') # find all pages
        for page in pages: # collect and add page categories to dict
            categories = [cl.attrib['title'].split(':', 1)[1] for cl in page.findall('categories/cl')]
            title_data[page.attrib['title']].append(repr(categories))


def get_page_views_from_title(titles, title_data):
    """collects the total page views over the last 60 days"""
    length = len(titles)
    index = 0
    while index < length:
        multi_title = sanatize_url(titles[index])
        for _ in range(20): # get 20 pages at a time
            if index < length:
                multi_title += '|' + sanatize_url(titles[index])
            else:
                break
            index += 1
        progress_update(index, length)
        wiki_request = requests.get(WIKI_API_URL+PAGE_VIEWS_SEARCH_VARS+multi_title)
        root = ET.fromstring(wiki_request.content)
        pages = root.findall('query/pages/page') # get all pages
        for page in pages: # 
            page_view_total = sum([int(pv.text) if pv.text is not None else 0 for pv in page.findall('pageviews/pvip')])
            title_data[page.attrib['title']].append(page_view_total)


def get_all_urls(titles, title_data):
    """converts every title into """
    urls = []
    for title in titles:
        title_data[title].append(WIKI_URL+title)
    return urls


def get_images_from_titles(titles, title_data):
    """get the image url from each wikipedia page and save it"""
    length = len(titles)
    index = 0
    url_list = []
    while index < length:
        multi_title = sanatize_url(titles[index])
        for _ in range(20): # Collect 20 titles at a time
            if index < length:
                multi_title += '|' + sanatize_url(titles[index])
            else:
                break
            index += 1
        progress_update(index, length)
        wiki_request = requests.get(WIKI_API_URL+IMAGE_SEARCH_VARS+multi_title)
        root = ET.fromstring(wiki_request.content)
        pages = root.findall('query/pages/page') # find all pages
        for page in pages: # add image download path and urls to a list
            try:
                url_list.append(page[0].attrib['source'])
                title_data[page.attrib['title']].append("Images/"+page.attrib['pageimage'])
            except IndexError:
                title_data[page.attrib['title']].append("")
    download_images(url_list) # Download all urls


def download_images(url_list):
    """downloads all images from the url_list into the Images directory"""
    print("\nDownloading images into Images folder:")
    length = len(url_list)
    for index, url in enumerate(url_list): # download all images
        progress_update(index, length)
        name = url.split('/')[-1]
        if len(name) > 250: # change name if name is too long
            name = name[0:50] + name[-4:]
        try: # download file to Images dir
            urllib.request.urlretrieve(url, "Images/"+name)
        except ValueError: # catch ValueError
            pass
        except urllib.error.HTTPError: # catch HTTPError
            pass
    progress_update(length, length)


# ============================================================ #
# Main function - take inputs, collect data and create databse #
# ============================================================ #
def main():
    """takes input from sys.argv for the wikipedia scraping"""
    term = "Office suites for Linux" # default test term

    if len(sys.argv) == 1: # use default if no input given
        print("Starting (using default value):")
    else: # use user input
        print("Starting:")
        term = sys.argv[-1]

    titles = [] # initialize empty lists for titles and categories
    categories = []
    database_tuples = []
    print("Getting all titles from given category:")
    get_all_titles_from_catagory(term, titles, categories)

    titles = list(set(titles)) # make sure all titles are unique
    print("Pages found:", len(titles))
    title_data = {}
    for title in titles: # Initialize a dict with title as keys
        title_data[title] = []

    print("Getting a summary from every page:")
    get_summaries(titles, title_data) # get a summary for every page
    print("\nGetting total page views in the last 60 days:")
    get_page_views_from_title(titles, title_data)
    print("\nGetting all the categories from the pages:")
    get_categories_from_title(titles, title_data) # get categores page is in
    print("\nCreating image directory:")
    create_image_directory() # create the image directory
    print("Getting image url from each page if it exists:")
    get_images_from_titles(titles, title_data) # collect image urls and download
    print("\nGetting an url for each title")
    get_all_urls(titles, title_data)
    for title in titles: # create list of tuples for inserting into databse
        database_tuples.append((title, title_data[title][0], title_data[title][1],
                                title_data[title][3], title_data[title][2], title_data[title][4]))

    print("Initialize database and adding data:")
    drop_table = 'DROP TABLE IF EXISTS [' + term + '];'
    create_table = 'CREATE TABLE ['+term+'] (title, summary, page_views, image_path, categories, url)'
    insert_table = 'INSERT INTO ['+term+'] VALUES (?,?,?,?,?,?)' #
    connection = sqlite3.connect('wiki-scraping.db') # Create and/or connect to database
    cursor = connection.cursor()
    cursor.execute(drop_table) # drop table if current table exists
    cursor.execute(create_table) # create table with name of given category
    cursor.executemany(insert_table, database_tuples) # add all data to table
    connection.commit() # commit database
    connection.close() # close databse
    print("Finished adding data:")


if __name__ == "__main__":
    main()
