from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
from pyhtml2pdf import converter


# ####### Categories of the News Releases ########
# Corporate
# Vorabbekanntmachung
# Directors Dealings
# Hauptversammlung
# Ad-hoc
# Gesamtstimmrechte
# Media
# Stimmrechtsanteile
# Kapitalmarktinformationen
# Press Release == UK Regulatory
# UK Regulatory
# Übernahmeangebot
# Related Party Transactions
# FR Regulatory


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define static variables
MONTH_DICT_GERMAN = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12
    }
# Since we are using the german website, we also need to define the german month names (see URL).
# Provide the english month names for the month_dict, in case you want to use english website settings.
BASE_URL = "https://www.eqs-news.com/de/"
HEADERS = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
        }
REQUEST_TIMEOUT = 60
SAVE_PDF = False
SAVE_CSV = False
PATH_SAVE = r"/Users/Robert_Hennings/Downloads"
NUM_TO_SCRAPE = 50
ISIN_LIST = ["DE0007164600", "DE0007236101", "DE000BAY0017", "DE0008404005", "DE000BASF111",
             "DE0005557508", "DE0007100000", "DE0007664005"]

class EQSScraper:
    def __init__(
            self,
            base_url: str=BASE_URL,
            isin_list: str=ISIN_LIST,
            num_to_scrape: int=None,
            month_dict: Dict[str, int]=MONTH_DICT_GERMAN,
            headers: Dict[str, str]=HEADERS,
            request_timeout: int=REQUEST_TIMEOUT
            ):
        self.base_url = base_url
        self.isin_list = isin_list
        self.num_to_scrape = num_to_scrape
        self.month_dict = month_dict
        self.headers = headers
        self.request_timeout = request_timeout

    # ############ Internal Helper Methods ############
    def __check_path_existence(
            self,
            path: str
            ):
        """Internal helper method - serves as generous path existence
           checker when saving and reading of an kind of data from files
           suspected at the given location
        !!!!If given path does not exist it will be created!!!!

        Args:
            path (str): full path where expected data is saved
        """
        folder_name = path.split("/")[-1]
        path = "/".join(path.split("/")[:-1])
        # FileNotFoundError()
        # os.path.isdir()
        if folder_name not in os.listdir(path):
            print(f"{folder_name} not found in path: {path}")
            folder_path = f"{path}/{folder_name}"
            os.mkdir(folder_path)
            print(f"Folder: {folder_name} created in path: {path}")


    def __replace_german_months(
            self,
            date_str
            ) -> str:
        for month, num in self.month_dict.items():
            date_str = date_str.replace(month, str(num))
        return date_str


    def scrape_initial_link(self) -> List[pd.DataFrame]:
        isin_df_list = []
        for isin in self.isin_list:
            isin_df = pd.DataFrame()
            # Scrape the initial link for every ISIN provided in the ISIN_LIST
            """Scrapes the base link provided and returns lists of release links, dates, and types."""
            try:
                initial_url = f"{self.base_url}search-results/?searchtype=news&searchword={isin}"
                logging.info(f"Scraping initial URL for ISIN: {isin}")
                response = requests.get(timeout=self.request_timeout, url=initial_url, headers=self.headers)
                response.raise_for_status()
                initial_soup = BeautifulSoup(response.content, "html.parser")

                num_all_releases = int(initial_soup.find("p", {"class": "search-news__results"}).text.strip().split()[-2])
                logging.info(f"Found {num_all_releases} news releases for ISIN: {isin}")

                url = f"{self.base_url}search-results/?searchtype=news&searchword={isin}&searchphrase=all&ordering=newest&pageLimit={num_all_releases}"
                soup = BeautifulSoup(requests.get(timeout=self.request_timeout, url=url, headers=self.headers).content, "html.parser")

                news_links = [link.get('href') for link in soup.find("div", {"class": "search-news"}).find_all("a")]
                release_dates = [date.text for date in soup.find_all("div", {"class": "col-auto search-news-grid__date"})]
                release_types = [r_type.text for r_type in soup.find_all("div", {"class": "col-auto search-news-grid__type"})]

                logging.info(f"Found {len(news_links)} links for news releases.")
                if self.num_to_scrape:
                    news_links = news_links[:self.num_to_scrape]
                    release_dates = release_dates[:self.num_to_scrape]
                    release_types = release_types[:self.num_to_scrape]
                # Add the information to the DataFrame
                isin_df = pd.DataFrame({
                    "link": news_links,
                    "release_date": release_dates,
                    "release_type": release_types
                })
                isin_df["isin"] = isin
            except Exception as e:
                logging.error(f"Error scraping initial link for ISIN {isin}: {e}")
            isin_df_list.append(isin_df)
        return isin_df_list
       

    def get_soup_from_link(
            self,
            links: List[str]
            ) -> List[BeautifulSoup]:
        """Creates BeautifulSoup objects for a list of links."""
        soup_list = []
        for ind, link in enumerate(links):
            try:
                # logging.info(f"Creating soup object for link: {link} (Progress: {round((ind / len(links)) * 100, 1)}%)")
                response = requests.get(timeout=self.request_timeout, url=link, headers=self.headers)
                response.raise_for_status()
                soup_list.append(BeautifulSoup(response.content, "html.parser"))
            except Exception as e:
                logging.error(f"Error creating soup object for link {link}: {e}")
        return soup_list


    def extract_title_and_company(
            self,
            soup: BeautifulSoup,
            link: str
            ) -> dict:
        """Extracts the company name and release title."""
        title_dict = {"Company_Name": None, "Release_Title": None}
        try:
            title_element = soup.find('h1', {"class": "news-details__title pb-2"})
            if title_element:
                release_title = title_element.text.strip().split("\n")
                title_dict["Company_Name"] = release_title[0]
                title_dict["Release_Title"] = release_title[1]
            else:
                logging.warning(f"Title element not found for link: {link}")
        except Exception as e:
            logging.error(f"Error extracting title and company name for link {link}: {e}")
        return title_dict


    def extract_header_metadata(
            self,
            soup: BeautifulSoup,
            link: str,
            ) -> list:
        """Extracts the Meta Data from the Header section of the single respective
           News Release

        Args:
            soup (BeautifulSoup): Soup of the given link
            link (str): single link of the news release

        Returns:
            list: _description_
        """
        header_meta_data_dict = {"Company_Name": None,
                                 "Release_Title": None,
                                 "Release_Date": None}
        header_meta_data_err = []
        release_header = []
        try:
            # in some cases we have a dedicated news_top section we can parse but not for every release type
            if soup.find('p', {"class": "news_top"}):
            #if r_type in ["Vorabbekanntmachung",
            #              "Hauptversammlung",
            #              "Ad-hoc",
            #              "Media",
            #              "Stimmrechtsanteile",
            #              "Kapitalmarktinformationen",
            #              "Press Release",
            #              "UK Regulatory"]:
                for line in soup.find('p', {"class": "news_top"}):
                    release_header.append(line.text.strip().replace("\n", ""))
                header_meta_data = [item for item in release_header if item != ""]
            else:  # would fail at: Übernahmeangebot
                header_meta_data = soup.find('div', {"class": "news-details__content"}).find_all("p")[0].text.strip().split("\n")
                # Drop all the empty list items
                header_meta_data = [item for item in header_meta_data if item != ""]
        except:
            print(f"Problems with Header Meta Data at: {link}")
            header_meta_data_err.append({
                "isin": isin,
                "link": link
                })
        return release_header, header_meta_data_err


    def extract_release_body_title(
            self,
            soup: BeautifulSoup,
            link: str
            ) -> list:
        """Extracts the Body Title of the News Release

        Args:
            soup_article (BeautifulSoup): Soup of the given link
            r_link (str): single link of the news release

        Returns:
            list: Release Body Title
        """
        release_body_title = ""
        try:
            release_body_title = soup.find('div', {"class": "news-details__content"}).find_all("p")[1].text.strip()
        except:
            print(f"Problems Release Body Title at: {link}")
        return release_body_title


    def extract_release_description_text(
            self,
            soup: BeautifulSoup,
            link: str
            ) -> list:
        """Extracts the Description Text, unfortunately this section is not
           always available, therefore it has to be handled with care

        Args:
            soup_article (BeautifulSoup): Soup of the given link
            r_link (str): single link of the news release

        Returns:
            list: Optional News Release Description Text
        """
        # not always existend in the body of the website, the short description slot
        disc_text = []
        if soup.find_all("ul", {"type": "disc"}):
            for l_i in soup.find_all("ul", {"type": "disc"}):
                disc_text.append(l_i.text)
            disc_text = " ".join(disc_text)
        else:
            print(f"No Release Description Text available for: {link}")
        return disc_text


    def extract_release_body_text(
            self,
            soup: BeautifulSoup,
            link: str,
            ) -> list:
        """Extracts the main body text from the release."""
        release_text = ""
        try:
            body_elements = soup.find('div', {"class": "news-details__content"}).find_all("p")
            release_text = " ".join([line.text.strip() for line in body_elements if line.text.strip()])
        except Exception as e:
            logging.error(f"Error extracting release body text for link {link}: {e}")
        return release_text


    def extract_metadata_bottom(
            self,
            soup: BeautifulSoup,
            ) -> dict:
        """Extracts Meta Data from the bottom of the news release
           Caution: This is not always available
        Args:
            soup (BeautifulSoup): Soup of the given link

        Returns:
            dict: list and a bigger dict with descriptive information
        """
        # also get the Meta data at the very end of the webpage
        # watch out: is not always available
        metadata_webpage_bottom = []
        if soup.find('table', {"class": "news_footer_layout"}):
            for line in soup.find('table', {"class": "news_footer_layout"}).find_all("tr"):
                metadata_webpage_bottom.append(line.text.strip().replace("\n", " "))
        # Save the metadata in a dict
        metadata_webpage_bottom_dict = {}
        for item in metadata_webpage_bottom:
            if ":" in item:
                key, value = item.split(': ')
                metadata_webpage_bottom_dict[key] = value
        return metadata_webpage_bottom, metadata_webpage_bottom_dict


    def add_scraped_data_to_df_list(
            self,
            isin_df_list: List[pd.DataFrame]
            ) -> List[pd.DataFrame]:
        """Enriches the DataFrame with the relevant information."""
        enriched_isin_df_list = []
        for isin_df in isin_df_list:
            try:
                # Extract the ISIN from the DataFrame
                isin = isin_df["isin"].iloc[0]
                logging.info(f"Enriching DataFrame for ISIN: {isin}")
                # Create a new DataFrame to hold the enriched data
                enriched_df = pd.DataFrame(columns=["isin", "link", "release_date", "release_type",
                                                    "company_name", "release_title", "body_title",
                                                    "description_text", "body_text", "metadata_bottom",
                                                    "header_metadata"])
                # Loop through each link in the DataFrame
                for index, row in isin_df.iterrows():
                    # Calculate progress percentage
                    progress = round((index + 1) / len(isin_df) * 100, 1)
                    logging.info(f"Progress for ISIN {isin}: {progress}%")

                    link = row["link"]
                    release_date = row["release_date"]
                    release_type = row["release_type"]
                    # Create a soup object for the link
                    soup = self.get_soup_from_link([link])[0]
                    # Extract the title and company name
                    title_dict = self.extract_title_and_company(soup=soup, link=link)
                    # Extract the body title
                    body_title = self.extract_release_body_title(soup=soup, link=link)
                    # Extract the description text
                    description_text = self.extract_release_description_text(soup=soup, link=link)
                    # Extract the body text
                    body_text = self.extract_release_body_text(soup=soup, link=link)
                    # Extract metadata from the bottom of the page
                    metadata_bottom, metadata_bottom_dict = self.extract_metadata_bottom(soup=soup)
                    # Extract header metadata
                    header_metadata, header_errors = self.extract_header_metadata(soup=soup, link=link)

                    # Append the data to the enriched DataFrame
                    isin_data_df = pd.DataFrame({
                        "isin": [isin],
                        "link": [link],
                        "release_date": [release_date],
                        "release_type": [release_type],
                        "company_name": [title_dict.get("Company_Name")],
                        "release_title": [title_dict.get("Release_Title")],
                        "body_title": [body_title],
                        "description_text": [description_text],
                        "body_text": body_text,
                        "metadata_bottom": [metadata_bottom],
                        "header_metadata": [header_metadata]
                    })
                    
                    enriched_df = pd.concat([
                        enriched_df,
                        isin_data_df
                        ],
                        ignore_index=True
                        )
            except Exception as e:
                logging.error(f"Error enriching DataFrame for ISIN {isin}: {e}")
            enriched_isin_df_list.append(enriched_df)
        return enriched_isin_df_list


    def save_data(
            self,
            isin_df_list: List[pd.DataFrame],
            path_save: str=None,
            save_pdf: bool=False,
            save_csv: bool=False,
            ):
        for isin_df in isin_df_list:
            # Extract all the article links from the DataFrame
            isin = isin_df["isin"].iloc[0]
            isin_df["release_date"] = isin_df["release_date"].apply(self.__replace_german_months)
            # Consider only the PDF for each scraped article link
            if save_pdf or save_csv:
                path_save_isin = f"{path_save}/{isin}"
                self.__check_path_existence(path=path_save_isin)
            if save_pdf:
                try:
                    link_list_isin_df = isin_df["link"]
                    for i in range(len(link_list_isin_df)):
                        # Extract the link and publication date
                        link = link_list_isin_df.iloc[i]
                        release_date = pd.to_datetime(isin_df["release_date"].iloc[i], dayfirst=True)
                        # For each of the respective links in the list save the pdf
                        file_name = f"{isin}_{release_date.strftime('%d-%m-%Y')}.pdf"
                        self.__check_path_existence(path=f"{path_save_isin}/{file_name}")
                        logging.info(f"Saving PDF file: {file_name} in path: {path_save_isin}")
                        converter.convert(link, f"{path_save_isin}/{file_name}")
                except Exception as e:
                    logging.error(f"Error saving .pdf: {e}")
            if save_csv:
                file_name = f"ISIN_DF_{isin}.csv"
                self.__check_path_existence(path=f"{path_save_isin}/{file_name}")
                logging.info(f"Saving CSV file: {file_name} in path: {path_save_isin}")
                isin_df.to_csv(f"{path_save_isin}/{file_name}", index=False)

# Example Usage:
# Step 1) Scrape the initial links for every ISIN provided in the ISIN_LIST
isin = "DE0007164600"
eqs_scraper_instance = EQSScraper(
                isin_list=[isin],
                num_to_scrape=NUM_TO_SCRAPE,
            )
isin_df_list = eqs_scraper_instance.scrape_initial_link()
print(isin_df_list[0])
# This ist holds a pd.DataFrame for each provided ISIN in the ISIN_LIST
# Each DataFrame contains the links, release dates, and release types.
# Step 2) Enrich the DataFrame with the relevant information
enriched_isin_df_list = eqs_scraper_instance.add_scraped_data_to_df_list(isin_df_list=isin_df_list)
print(enriched_isin_df_list[0].columns)
print(enriched_isin_df_list[0])
print(enriched_isin_df_list[0]["body_text"].iloc[0])
# Step 3) For each ISIN DataFrame save the full DataFrame as .csv and each article link as .pdf
eqs_scraper_instance.save_data(
            isin_df_list=enriched_isin_df_list,
            path_save=PATH_SAVE,
            save_pdf=SAVE_PDF,
            save_csv=SAVE_CSV
        )
