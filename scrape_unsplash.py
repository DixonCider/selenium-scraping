# src: https://medium.com/swlh/web-scraping-stock-images-using-google-selenium-and-python-8b825ba649b9
import requests
import os
import io
from PIL import Image
import hashlib
import selenium
import time
import shutil
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from datetime import timedelta

def fetch_image_urls(query:str, max_links_to_fetch:int, wd:webdriver, folder_path:str,
                     sleep_between_interactions:int=3, verbose:bool=False):
    def scroll_to_end(wd, scroll_range, partitions=1000, scroll_portion=0.6):
        for _ in range(partitions):
            wd.execute_script(f"window.scrollBy(0, {scroll_range / partitions});")
            time.sleep(sleep_between_interactions * scroll_portion / partitions)
        time.sleep(sleep_between_interactions * (1 - scroll_portion))

    def cache_urls(urls, fpath):
        with open(fpath, 'a') as f:
            for url in urls:
                print(url, file=f)

    def download(urls):
        newpid = os.fork()
        if newpid == 0:
            for url in urls:
                persist_image(folder_path=folder_path, url=url)
            os._exit(0)

    # build the unsplash query
    search_url = f"https://unsplash.com/s/photos/{query}"
    # load the page
    wd.get(search_url)
    time.sleep(sleep_between_interactions)  
    
    image_urls = set()
    
    pixel_velocity = 5000

    n_iter = 0
    avg_time = 0
    avg_exp = 0.8
    while len(image_urls) < max_links_to_fetch:
        tic = time.clock()
        scroll_to_end(wd, pixel_velocity)
        time.sleep(sleep_between_interactions)
        thumb = wd.find_elements_by_css_selector("img._2zEKz")
        time.sleep(sleep_between_interactions)
        n_unique = len(image_urls)
        new_urls = set()
        for img in thumb:
            if verbose:
                print(img)
                print(img.get_attribute('src'))
            new_urls.add(img.get_attribute('src'))
            time.sleep(.5)
        unique_urls = new_urls - image_urls
        image_urls = image_urls.union(new_urls)
        n_duplicate = len(thumb)
        n_unique = len(image_urls) - n_unique

        cache_urls(unique_urls, os.path.join(folder_path, 'url_cache'))
        download(unique_urls)

        toc = time.clock()
        avg_time = (toc - tic) if avg_time == 0 else avg_time * avg_exp + (toc - tic) * (1 - avg_exp) # (avg_time * (n_iter) + (toc - tic)) / (n_iter + 1)
        n_iter += 1
        remaining_time = int((max_links_to_fetch - len(image_urls)) * avg_time)

        print(f"total: {len(image_urls)}, duplicate: {n_duplicate}, unique: {n_unique}, time: {toc - tic:.3f}, avg time: {avg_time:.3f}, remaining: {str(timedelta(seconds=remaining_time))}")
        if n_unique == 0:
            break
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
        file_path = os.path.join(folder_path,hashlib.sha1(image_content).hexdigest()[:10] + '.png')
        with open(file_path, 'wb') as f:
            image.save(f, "PNG", quality=100)
        if verbose:
            print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

def search_and_download(search_term:str,driver_path:str,verbose=False,
                        target_path='./images-UNSPLASH',number_images=200):
    target_folder = os.path.join(target_path,'_'.join(search_term.lower().split(' ')))
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)
    os.makedirs(target_folder)
    options = Options()
    options.headless = 'DISPLAY' not in os.environ # headless if no display environment
    with webdriver.Firefox(executable_path=driver_path, options=options) as wd:
        res = fetch_image_urls(search_term, number_images, wd=wd, folder_path=target_folder,
                               sleep_between_interactions=5, verbose=verbose)
        print(f'res count {len(res)}')
        '''
        for elem in res:
            persist_image(target_folder,elem,verbose=verbose)
        '''

def main():
    search_terms = ['dog']
    driver_path = './geckodriver'
    for search_term in search_terms:
        search_and_download(search_term=search_term, driver_path=driver_path, number_images=20000, verbose=False)

if __name__ == '__main__':
    main()
