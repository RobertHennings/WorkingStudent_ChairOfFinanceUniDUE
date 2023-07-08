import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import xlwings as xw
import glob
from pyhtml2pdf import converter

def scrape_eqs_releases(isin: str, save_pdf: bool, save_txt: bool, path_save: str, num_to_scrape: int):
    """Scrapes the News website EQS News for a given Company ISIN

    Args:
        isin (str): Company identifier, primarily for DE ISIN
        save_pdf (bool): If True saves a pdf copy of the news release webpage
        save_txt (bool): If True saves a .txt conatining the scraped text from the news release webpage
        path_save (str): Path where to save the .pdf and .txt files
        num_to_scrape (int): Number of news release webpages to scrape

    Raises:
        TypeError: Type and Var
        TypeError: Type and Var
        TypeError: Type and Var
    """
    # Check if all the datatypes are valid
    for var in [isin, path_save]:
        if not isinstance(var, str):
            raise TypeError(f"{var} not type string")
    for var in [save_pdf, save_txt]:
        if not isinstance(var, bool):
            raise TypeError(f"{var} not type bool")
    for var in [num_to_scrape]:
        if not isinstance(var, int):
            raise TypeError(f"{var} not type int")

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
    url = f"https://www.eqs-news.com/de/search-results/?searchtype=news&searchword={isin}&searchphrase=all&ordering=newest&pageLimit={num_all_releases}"
    soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")

    # Scrape all the single links to the very own news pages that should be scraped
    # Here we have to add also a clicker that clicks itslef through the single results pages
    news_links = []
    for link in soup.find("div", {"class": "search-news"}).find_all("a"):
        news_links.append(link.get('href'))
    # Also save the publication date of the news release
    release_dates = []
    for date in soup.find_all("div", {"class": "col-auto search-news-grid__date"}):
        release_dates.append(date.text)
    # Also get the type of news release
    release_type = []
    for r_type in soup.find_all("div", {"class": "col-auto search-news-grid__type"}):
        release_type.append(r_type.text)
    
    print(f"Scraping {len(news_links)} links for news releases")
    print("Scraping every single news release...")
    # Loop through every scraped single news release link and safe respective date and type
    for link, r_date, r_type in zip(news_links[:num_to_scrape], release_dates[:num_to_scrape], release_type[:num_to_scrape]):
        # for debugging
        link = "https://www.eqs-news.com/de/news/press-release/baywa-beteiligung-mrmrs-homes-raeumt-innovationspreis-ab-und-geht-deutschlandweit-in-die-flaeche-wohnhaus-konfigurator-revolutioniert-das-bauen-fuer-jedermann/1412925"
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
        title_dict = {"Company_Name": None,
                      "Release_Title": None}
        release_title = soup_article.find('h1', {"class": "news-details__title pb-2"}).text.strip().split("\n")
        try:
            title_dict["Company_Name"] = release_title[0]
            title_dict["Release_Title"] = release_title[1]
        except:
            print("Problems saving title elements in dict")
        # Next get the messsage body itself
        # Element 0 needs special treatment
        header_meta_data_dic = {"Company_Name": None,
                                "Release_Title": None,
                                "Release_Date": None}
        
        header_meta_data = soup_article.find('div', {"class": "news-details__content"}).find_all("p")[0].text.strip().split("\n")
        # Drop all the empty list items
        header_meta_data = [item for item in header_meta_data if item != ""]
        try:
            # Save the Company Name
            header_meta_data_dic["Company_Name"] = header_meta_data[0]
            # Save the Release_Title
            header_meta_data_dic["Release_Title"] = header_meta_data[1]
        except:
            print("Problems saving Header Metadata in dict")
        # Find the Publication Date in the metadata
        header_meta_data_dic["Release_Date"] = [item for item in header_meta_data if "CET/CEST" in item]
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
        # Save the metadata in a dict
        metadata_webpage_bottom_dict = {}
        for item in metadata_webpage_bottom:
            if ":" in item:
                key, value = item.split(': ')
                metadata_webpage_bottom_dict[key] = value

        # Finally save the whole scraped content in a .txt file as well
        if save_txt:
            file_name = time + ".txt"
            print(f"Saving file: {file_name} in path: {path_save}")
            with open(path_save + "//" + file_name, "w") as f:
                f.write("Published:\n" + r_date)
                f.write("\nRelease_Type:\n" + r_type)
                f.write("\nRelease_Title:\n" + "\n".join(release_title)) # Save title
                f.write("\nMeta_Data:\n" + "\n".join(header_meta_data)) # Save the meta data from the header
                f.write("\nRelease_Body_Title:\n" + "".join(release_body_title)) # save the title of the actual textual body
                if disc_text:
                    f.write("\nDescription_Bullets:\n" + "\n".join(disc_text)) # if exists save the brief bullet points from short description
                f.write("\nRelease_Text:\n" + "\n".join(release_text))
                f.write("\nRelease_Contact:\n" + "\n".join(release_text_after_contact))
                f.write("\nMetadata_WebpageBottom:\n" + "\n".join(metadata_webpage_bottom))
                f.close()
    print("Finished scraping all found releases")

isin = "DE0005194062"
save_pdf = True
save_txt = True
path_save = glob.os.path.join("/Users/Robert_Hennings/Dokumente/Uni/MusterBewerbung/MeineArbeitgeber/SHK Uni DUE FIN/Arbeitsordner/EQS_News_Scraper/Article_PDF")
num_to_scrape = 20
scrape_eqs_releases(isin, save_pdf, save_txt, path_save, num_to_scrape)
# Next step: also save metadata from the search list, like category or source and date of submission
