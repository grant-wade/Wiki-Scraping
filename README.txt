
Author: Grant Wade (grant@gwade.co)
Project: Wikipedia Scraping

Usage:
    Simple test that collects information from all the pages in the 
    category "Office suites for Linux"`. This is a built in basic test
    to demonstrate collecting a number of pages from a category
    get their summary, image if they have one and the categorys that
    the page is in, then place in an sqlite databse.
        python3 wikipedia-scraping.py 

    This script can be used to scrape any wikipedia category given too.
    This category was used for the project is the intended use of the script.
    Takes around 20 minutes to collect ~8000 pages with ~1800 images
        python wikipedia-scraping.py "Linux software"
