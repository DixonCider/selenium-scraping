# src: https://medium.com/swlh/web-scraping-stock-images-using-google-selenium-and-python-8b825ba649b9
import requests
import os
import io
from PIL import Image
import hashlib
import selenium
import time
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

def fetch_image_urls(query:str, max_links_to_fetch:int, wd:webdriver, sleep_between_interactions:int=3, verbose:bool=False):
    def scroll_to_end(wd, scroll_range, partitions=1000):
        for _ in range(partitions):
            wd.execute_script(f"window.scrollBy(0, {scroll_range / partitions});")
            time.sleep(sleep_between_interactions/partitions)

    # build the unsplash query
    search_url = f"https://unsplash.com/s/photos/{query}"
    # load the page
    wd.get(search_url)
    time.sleep(sleep_between_interactions)  
    
    image_urls = set()
    
    pixel_velocity = 5000

    with tqdm(total=max_links_to_fetch) as pbar:
        while len(image_urls) < max_links_to_fetch:
            scroll_to_end(wd, pixel_velocity)
            time.sleep(5)
            thumb = wd.find_elements_by_css_selector("img._2zEKz")
            time.sleep(5)
            n_unique = len(image_urls)
            for img in thumb:
                if verbose:
                    print(img)
                    print(img.get_attribute('src'))
                image_urls.add(img.get_attribute('src'))
                time.sleep(.5)
            n_duplicate = len(thumb)
            n_unique = len(image_urls) - n_unique
            pbar.update(n_unique)

            if verbose:
                print(f"Found: {len(image_urls)} total search results. Extracting links...")
                print(f"Duplicate: {n_duplicate}, Unique: {n_unique}")
    return image_urls

def persist_image(folder_path:str, url:str, verbose:bool=False):
    try:
        # headers = {'User-agent': 'Chrome/64.0.3282.186'}
        headers={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
        image_content = requests.get(url, headers=headers).content
        
    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")
    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path,hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            image.save(f, "PNG", quality=100)
        if verbose:
            print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

def search_and_download(search_term:str,driver_path:str,verbose=False,
                        target_path='./images-UNSPLASH',number_images=200):
    target_folder = os.path.join(target_path,'_'.join(search_term.lower().split(' ')))
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    options = Options()
    options.headless = 'DISPLAY' not in os.environ # headless if no display environment
    with webdriver.Firefox(executable_path=driver_path, options=options) as wd:
        res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=3, verbose=verbose)
        print(f'res count {len(res)}')
        for elem in res:
            persist_image(target_folder,elem,verbose=verbose)

def main():
    search_terms = ['dog']
    driver_path = './geckodriver'
    for search_term in search_terms:
        search_and_download(search_term=search_term, driver_path=driver_path, number_images=20000, verbose=False)

if __name__ == '__main__':
    main()
