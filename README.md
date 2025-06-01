# WorkingStudent_ChairOfFinanceUniDUE

<p align="center">
  <img src="https://raw.githubusercontent.com/RobertHennings/WorkingStudent_ChairOfFinanceUniDUE/refs/heads/main/Pictures/HEMF_Logo.png" 
       width="400"/>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/RobertHennings/WorkingStudent_ChairOfFinanceUniDUE/refs/heads/main/Pictures/Chair_Logo.png" 
       width="400"/>
</p>

## ToDO
* [ ] SSRN Scraper: Search in the single respective Conference Sub-SSRN Pages for more details like Submission format (i.e. LaTex, Word, PDF, etc) and also for the explicit Submission Deadline
* [ ] SSRN Scraper: Check Automation Process and write it as VBA-Standalone Code
* [X] EQS Scraper: Change the output format to a pd.DataFrame for ease of use, also in the saved .txt files as structure
* [X] EQS Scraper: Change the filename of the saved files to ISIN_ReleaseDate_EQSNewsID for .txt and .pdf files
* [X] EQS Scraper: Sanity Check if all Release Sections are scraped properly
* [X] EQS Scraper: Impement Release Type sensitive scraping to better cope with different url strcutures, types are the following:
  * [X] Corporate
  * [X] Vorabbekanntmachung
  * [X] Directors Dealings
  * [X] Hauptversammlung
  * [X] Ad-hoc
  * [X] Gesamtstimmrechte
  * [X] Media
  * [X] Stimmrechtsanteile
  * [X] Kapitalmarktinformationen
  * [X] Press Release
  * [X] UK Regulatory

## Documentation EQS Scraper
### DISCLAIMER: This Scraper is not associated with the EQS Group in any kind - it is a pure personal - nonprofit/non commercial open source software project
The main purpose of this simple Webscraper is to source the single open market publications that can be found [here](https://www.eqs-news.com/de/) that primarily stem from small to mid cap sized comapnies, listed on the german stock exchange.
Since the publication of such information is quite scarce and the arbitrage opportunities especially in these market segments due to information asymmetries not to ignore, this scraper should help gather them.


## Useful Links
### Reuters Eikon Python API
* https://developers.refinitiv.com/en/article-catalog/article/eikon-data-api-cheat-sheet
* https://github.com/Refinitiv-API-Samples/Example.DataLibrary.Python/blob/main/Examples/2-Content/2.06-Search/EX-2.06.01-Search.ipynb
* https://github.com/Refinitiv-API-Samples/Example.RDPLibrary.Python.ConvertSymbology
* https://community.developers.refinitiv.com/questions/94450/how-to-retrieve-exchange-specific-ric-from-isin-in.html
* https://community.developers.refinitiv.com/questions/102323/filter-list-in-discovery-search-function.html
* https://cdn.refinitiv.com/public/rd-lib-python-doc/1.0.0.0/book/en/sections/intro.html
* https://github.com/Refinitiv-API-Samples/Example.DataLibrary.Python/tree/main/Examples
* https://community.developers.refinitiv.com/questions/96545/ric-search-tool-api.html
* https://community.developers.refinitiv.com/questions/101641/help-with-news-api-for-python-more-details.html
* https://community.developers.refinitiv.com/questions/99828/api-for-fetching-news-feed-data-of-companies.html

### EQS News Article Dashboard
* https://www.eqs-news.com/de/

### SSRN Notifications and Announcements
* https://www.ssrn.com/index.cfm/en/janda/professional-announcements/?annsNet=203
