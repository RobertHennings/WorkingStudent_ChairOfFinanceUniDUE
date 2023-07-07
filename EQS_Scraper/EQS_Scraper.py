import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import xlwings as xw
import glob
from pyhtml2pdf import converter


glob.os.getcwd()
glob.os.chdir(glob.os.path.join("/Users/Robert_Hennings/Dokumente/Uni/MusterBewerbung/MeineArbeitgeber/SHK Uni DUE FIN/Arbeitsordner/"))

def scrape_eqs_releases(isin: str, save_pdf: bool, save_txt: bool, path_save: str, num_to_scrape: int):
    # Do first scrape to see how many releases we have to edit the url and directly scrape all the releases at once
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
    }
    initial_url = f"https://www.eqs-news.com/de/search-results/?searchtype=news&searchword={isin}"
    print(f"Scraping initial url for isin: {isin}")
    initial_soup = BeautifulSoup(requests.get(initial_url, headers=headers).content, "html.parser")

    num_all_releases = int(initial_soup.find("p", {"class": "search-news__results"}).text.strip().split()[-2])
    print(f"Found {num_all_releases} news releases for isin: {isin}")
    # Edit the url to get the max number of results
    url = f"https://www.eqs-news.com/de/search-results/?searchtype=news&searchword=DE0005494165&searchphrase=all&ordering=newest&pageLimit={num_all_releases}"
    soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")

    # Scrape all the single links to the very own news pages that should be scraped
    # Here we have to add also a clicker that clicks itslef through the single results pages
    news_links = []
    for link in soup.find("div", {"class": "search-news"}).find_all("a"):
        news_links.append(link.get('href'))
    print(f"Scraping {len(news_links)} links for news releases")
    print("Scraping every single news release...")
    for link in news_links[:num_to_scrape]:
        # for debugging
        # link = "https://www.eqs-news.com/de/news/media/entscheidung-ueber-deutsches-hinweisgeberschutzgesetz-vertagt-weiter-keine-rechtssicherheit-fuer-whistleblower-eqs-group-bedauert-dass-das-gesetz-wegen-details-nicht-verabschiedet-wurde/1751575"
        print(f"Scraping news release: {link.split('/')[-2]}")
        # First determine if the article should be saved somewhere
        time = dt.datetime.now().strftime(f"%d_%m_%Y_%M_%S_{isin}")
        if save_pdf:
            file_name = time + ".pdf"
            print(f"Saving file: {file_name} in path: {path_save}")
            try:
                converter.convert(link, path_save + "//" + file_name)
            except:
                print(f"Problems solving pdf file for release: {link.split('/')[-2]}")
        # Next we need to scrape every single webpage from the news search
        soup_article = BeautifulSoup(requests.get(link, headers=headers).content, "html.parser")
        # Get the title element
        release_title = soup_article.find('h1', {"class": "news-details__title pb-2"}).text.strip().split("\n")
        # Next get the messsage body itself
        # Element 0 needs special treatment
        header_meta_data = soup_article.find('div', {"class": "news-details__content"}).find_all("p")[0].text.strip().split("\n\n\n")
        # element 1 is the title of the release
        release_body_title = soup_article.find('div', {"class": "news-details__content"}).find_all("p")[1].text.strip()
        # not always existend in the body of the website, the short description slot
        disc_text = []
        if soup_article.find_all("ul", {"type": "disc"}):
            for l_i in soup_article.find_all("ul", {"type": "disc"}):
                # print(l_i.text)
                disc_text.append(l_i.text)
        # Rest of the text
        # the release body lasts until one of the following keywords 
        counter_contact = 0
        for line in soup_article.find('div', {"class": "news-details__content"}).find_all("p")[1:]:
            if (("kontakt:") or ("contact:")) not in line.text.strip().lower():
                counter_contact +=1
            else:
                counter_contact +=1
                break

        release_text = []
        for line in soup_article.find('div', {"class": "news-details__content"}).find_all("p")[2:counter_contact]:
            release_text.append(line.text.strip())

        # next get all the text content that is below the release contact details
        release_text_after_contact = []
        for line in soup_article.find('div', {"class": "news-details__content"}).find_all("p")[counter_contact:]:
            release_text_after_contact.append(line.text.strip())

        # also get the Meta data at the very end of the webpage
        # watch out: is not always available
        if soup_article.find('table', {"class": "news_footer_layout"}):
            metadata_webpage_bottom = []
            for line in soup_article.find('table', {"class": "news_footer_layout"}).find_all("tr"):
                # print(line.text)
                metadata_webpage_bottom.append(line.text.strip().replace("\n", " "))

        # Finally save the whole scraped content in a .txt file as well
        if save_txt:
            file_name = time + ".txt"
            print(f"Saving file: {file_name} in path: {path_save}")
            with open(path_save + "//" + file_name, "w") as f:
                f.write("".join(release_title)) # Save title
                f.write("".join(header_meta_data)) # Save the meta data from the header
                f.write("".join(release_body_title)) # save the title of the actual textual body
                if disc_text:
                    f.write("".join(disc_text)) # if exists save the brief bullet points from short description
                f.write("".join(release_text))
                f.write("".join(release_text_after_contact))
                f.write("".join(metadata_webpage_bottom))
                f.close()
    print("Finished scraping all found releases")

isin = "DE0005494165"
save_pdf = True
save_txt = True
path_save = glob.os.path.join("/Users/Robert_Hennings/Dokumente/Uni/MusterBewerbung/MeineArbeitgeber/SHK Uni DUE FIN/Arbeitsordner/EQS_News_Scraper/Article_PDF")
num_to_scrape = 20
scrape_eqs_releases(isin, save_pdf, save_txt, path_save, num_to_scrape)
# Next step: also save metadata from the search list, like category or source and date of submission
