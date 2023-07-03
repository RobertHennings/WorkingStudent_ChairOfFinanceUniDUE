# Web Scraping SSRN - Chair of Finance project
# Scope: Scrape the important Information from the webpage
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import xlwings as xw

url = "https://www.ssrn.com/index.cfm/en/janda/professional-announcements/?annsNet=203"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
}
soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")

# Call for papers and participants = AnnType_1
# Call for Papers - Competitions = AnnType_2
# Call for Papers - Journals and Books = AnnType_3
# Call for Applications - Academics Programs = AnnType_4
# Awards, Grants, Fellowships & Scholarships = AnnType_5
# Journal and Books of interest = AnnType_6
# Call for Authors / Editors /Topics = AnnType_7
# Other Announcement = AnnType_8
# Call for Participants - Conference = AnnType_9

# Get the section name
soup.find("div", {"id": "AnnType_9"}).find("h2")

# Get all the links to the Conferences or Journals
soup.find("div", {"id": "AnnType_9"}).find_all("a")
# Get the Posted Date from the conference
soup.find("div", {"id": "AnnType_9"}).find_all("p", {"class": "posted-date"})


# Get all the links to the Conferences or Journals
soup.find("div", {"id": "AnnType_1"}).find_all("a")


soup.find("div", {"id": "AnnType_2"}).find_all("a")


# Get the Posted Date from the conference
soup.find("div", {"id": "AnnType_1"}).find_all("p", {"class": "posted-date"})

# Slice the long list into chunks of 3 items per conference
soup.find("div", {"id": "AnnType_1"}).find_all("p")





# Putting it all together
conference_df = pd.DataFrame(columns=["Conference", "Dates", "Location", "Posted", "Conf_Link", "Section"])

# Get the text that masks the link
titles = []
for item in soup.find("div", {"id": "AnnType_3"}).find_all("a"):
    titles.append(item.string)


# for every other section we now only need to get the posted date and the link
soup.find("div", {"id": "AnnType_2"}).find_all("p", {"class": "posted-date"})
conf_posted_dates = []

for p_date in soup.find("div", {"id": "AnnType_3"}).find_all("p", {"class": "posted-date"}):
    conf_posted_dates.append(p_date.text)

# Split the whole content into chunks of 3 items that are reprensenting one whole entry set
line = []
for i,j in zip(range(0, int(len(soup.find("div", {"id": "AnnType_2"}).find_all("p"))), 2), range(3, int(len(soup.find("div", {"id": "AnnType_2"}).find_all("p"))), 2)):
    print(i, j)
    # print("Entry:", soup.find("div", {"id": "AnnType_1"}).find_all("p")[i:j])
    # line.append(soup.find("div", {"id": "AnnType_2"}).find_all("p")[i:j])
# Split the chunk of 3 items further into its subparts
conf_dates = []
conf_location = []
conf_posted_dates = []

for item in line:
    conf_dates.append(item[0].text)
    conf_location.append(item[1].text)
    conf_posted_dates.append(item[2].text)

# get only the links
conf_links = []
for link in soup.find("div", {"id": "AnnType_3"}).find_all("a"):
    conf_links.append(link.get("href"))

# Fill the DataFrame
conference_df["Conference"] = titles
conference_df["Dates"] = conf_dates
conference_df["Location"] = conf_location
conference_df["Posted"] = conf_posted_dates
conference_df["Conf_Link"] = conf_links
conference_df["Section"] = soup.find("div", {"id": "AnnType_9"}).find("h2").text






# conference_df.to_excel("//Users//Robert_Hennings//Dokumente//Uni//MusterBewerbung//MeineArbeitgeber//SHK Uni DUE FIN//Arbeitsordner//SSRN_scraped.xlsx", index=False)

# Creating a function out of this script
def scrape_ssrn_notifications(url: str, section_to_scrape: str, save: bool, path_save: str, file_name: str) -> pd.DataFrame:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
    }
    # Create the soup from the request
    soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")

    # Create the final table, since AnnType_1 has is distinct from every other section we need a separte case
    if section_to_scrape == "AnnType_1":
        conference_df = pd.DataFrame(columns=["Conference", "Dates", "Location", "Posted", "Conf_Link", "Section"])
    else:
        # less entries
        conference_df = pd.DataFrame(columns=["Conference", "Posted", "Conf_Link", "Section"])

    # Get the text that masks the link, independent of section
    titles = []
    for item in soup.find("div", {"id": section_to_scrape}).find_all("a"):
        titles.append(item.string)

    # Split the whole content into chunks of 3 items that are reprensenting one whole entry set
    if section_to_scrape == "AnnType_1":
        line = []
        for i,j in zip(range(0, int(len(soup.find("div", {"id": section_to_scrape}).find_all("p")))+1, 3), range(3, int(len(soup.find("div", {"id": section_to_scrape}).find_all("p")))+1, 3)):
            # print("Entry:", soup.find("div", {"id": "AnnType_1"}).find_all("p")[i:j])
            line.append(soup.find("div", {"id": section_to_scrape}).find_all("p")[i:j])
        # Split the chunk of 3 items further into its subparts
        conf_dates = []
        conf_dates_start = []
        conf_dates_end = []

        conf_location = []
        conf_posted_dates = []

        for item in line:
            conf_dates.append(item[0].text.replace("Conference Dates: ", ""))
            if len(item[0].text.replace("Conference Dates: ", "").split(" - ")) == 2:
                conf_dates_start.append(pd.Timestamp(item[0].text.replace("Conference Dates: ", "").split(" - ")[0]))
                conf_dates_end.append(pd.Timestamp(item[0].text.replace("Conference Dates: ", "").split(" - ")[1]))
            else:
                conf_dates_start.append(pd.Timestamp(item[0].text.replace("Conference Date: ", "")))
                conf_dates_end.append("")

            conf_location.append(item[1].text.replace("Location: ", ""))
            conf_posted_dates.append(pd.Timestamp(item[2].text.replace("Posted: ", "")))
    else:
        conf_posted_dates = []
        for p_date in soup.find("div", {"id": section_to_scrape}).find_all("p", {"class": "posted-date"}):
            conf_posted_dates.append(pd.Timestamp(p_date.text.replace("Posted: ", "")))

    # get only the links, independet of section
    conf_links = []
    for link in soup.find("div", {"id": section_to_scrape}).find_all("a"):
        conf_links.append(link.get("href"))

    # Fill the DataFrame
    conference_df["Conference"] = titles
    conference_df["Posted"] = conf_posted_dates
    conference_df["Conf_Link"] = conf_links
    conference_df["Section"] = soup.find("div", {"id": section_to_scrape}).find("h2").text
    conference_df["Updated"] = pd.Timestamp(dt.datetime.now())

    if section_to_scrape == "AnnType_1":
        conference_df["Location"] = conf_location
        conference_df["Dates"] = conf_dates
        conference_df["Dates Start"] = conf_dates_start
        conference_df["Dates End"] = conf_dates_end
        conference_df["Duration"] = (pd.Series(conf_dates_end) - pd.Series(conf_dates_start))

    if save:
        with pd.ExcelWriter(path_save + "//" + file_name + ".xlsx") as writer:
            conference_df.to_excel(writer, sheet_name="Actual", index=False)
    else:
        return conference_df
    if history:
        # open the existing file and search the respective ribbon called scraping history
        # append the new scrape

        # Check if theres content in the respetcive sheet
        book = xw.Book(path_save + "//" + file_name + ".xlsx")
        hist = book.sheets[0]["A1"].options(pd.DataFrame, expand='table').value
        book.close()
        hist = hist.reset_index()
        all_hist = pd.concat([hist, conference_df])

        with pd.ExcelWriter(path_save + "//" + file_name + ".xlsx") as writer:
            all_hist.to_excel(writer, sheet_name="ScrapingHistory", index=False)

    return conference_df



url = "https://www.ssrn.com/index.cfm/en/janda/professional-announcements/?annsNet=203"
section_to_scrape = "AnnType_1"
save = False
path_save = "//Users//Robert_Hennings//Dokumente//Uni//MusterBewerbung//MeineArbeitgeber//SHK Uni DUE FIN//Arbeitsordner//"
file_name = "SSRN_scraped"
history = True
scrape_ssrn_notifications(url=url, section_to_scrape=section_to_scrape, save=save, path_save=path_save, file_name=file_name)

# to keep consitent track of the historical evolvement of the announcements we need to keep a historic overview
# also highlight if there are new entries that werent in the last scraped version
# also integrate that if there are new releases and infos regarding Patricks Selection in his most recent excel file, it should automatically recognize the already existing names in the file
# we should also scrape multiple Website sections, so different AnnTypes


# Now update if its necessary
file_name = "Finance_Conferences_Overview.xlsx"
file_path = "//Users//Robert_Hennings//Dokumente//Uni//MusterBewerbung//MeineArbeitgeber//SHK Uni DUE FIN//Arbeitsordner//"
sheet_name = "Conference_Overview"
database = scrape_ssrn_notifications(url=url, section_to_scrape=section_to_scrape, save=save, path_save=path_save, file_name=file_name)
# database = pd.read_excel("//Users//Robert_Hennings//Dokumente//Uni//MusterBewerbung//MeineArbeitgeber//SHK Uni DUE FIN//Arbeitsordner//SSRN_scraped.xlsx", sheet_name="ScrapingHistory", engine="openpyxl")

def update_conferences(file_name, file_path, sheet_name, database) -> pd.DataFrame:
    # Read in the existing Overview Sheet that needs to be updated
    to_be_updated_conf = pd.read_excel(file_path + "//" + file_name, sheet_name=sheet_name, engine="openpyxl")

    # Merge both dataframes based on the common conference names and update the old data
    update = pd.merge(database, to_be_updated_conf, left_on="Conference", right_on="Name")
    # Loop over every conference and update its values
    for conf in update.Conference:
        # Update the Duration
        to_be_updated_conf[to_be_updated_conf.Name == conf]["Duration\n(days)"] = update[update.Conference == conf].Duration
        # Update the Date
        start = update[update.Conference == conf]["Dates Start"].dt.strftime("%d-%m")
        end = update[update.Conference == conf]["Dates End"].dt.strftime("%d-%m-%Y")

        to_be_updated_conf[to_be_updated_conf.Name == conf]["Date"] = start + " to " + end


update_conferences(file_name, file_path, sheet_name, database)

# Lets now also invetigate if we can get more data from the single conference websites from SSRN
# take one example: https://www.ssrn.com/index.cfm/en/janda/announcement/?id=13401

url = "https://www.ssrn.com/index.cfm/en/janda/announcement/?id=13401"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
}
soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")


# Now we have to find the keywords in the soup
soup.text.lower().find("submission")

soup.text.lower()[980:1000]
