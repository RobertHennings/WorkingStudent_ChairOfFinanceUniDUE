# Web Scraping SSRN - Chair of Finance project
# Scope: Scrape the important Information from the webpage
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import xlwings as xw
import re
import glob
# Section mapping that has to be always actual, is sometimes changed by the website
# what causes errors while scraping
section_mapping_dict = {
    "Call for papers and participants - Conference": "AnnType_1",
    "Call for Papers - Journals and Books": "AnnType_2",
    "Awards, Grants, Fellowships & Scholarships": "AnnType_3",
    "Call for Papers - Competitions": "AnnType_4",
    "Call for Participants - Conference": "AnnType_5",
    "Other Announcement": "AnnType_6",
    "Call for Applications - Academic Programs": "AnnType_7",
    "Journal and Books of interest": "AnnType_8"
                        }

def extract_submission_deadline(text):
    # Define a regular expression pattern to find the word "submission"
    submission_pattern = r'\bsubmission\b'

    # Search for the word "submission" in the text
    submission_match = re.search(submission_pattern, text, re.IGNORECASE)

    if submission_match:
        # Get the index where "submission" is found
        submission_index = submission_match.end()

        # Define a regular expression pattern to search for date formats after the index of "submission"
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2})\s+\d{1,2}(?:,)?\s+\d{4}\b'

        # Search for the date pattern in the text after the index of "submission"
        date_match = re.search(date_pattern, text[submission_index:], re.IGNORECASE)

        if date_match:
            submission_deadline = date_match.group(0)
            return submission_deadline
        else:
            return None
    else:
        return None


def scrape_ssrn_notifications(url: str, section_to_scrape: str, save: bool,
                              path_save: str, file_name: str,
                              section_mapping_dict: dict) -> pd.DataFrame:
    """Scrapes the SSRN Notifications website that publishes news and announcements regarding
       conference applications and or jobs

    Args:
        url (str): SSRN url to scrape
        section_to_scrape (str): SSRN provides seven distinct Sections or categories that can be scraped
        save (bool): Save the returned pd.DataFrame with the given name at the given place
        path_save (str): Disc place where to save the scraping result
        file_name (str): File name of the saved scrape

    Returns:
        pd.DataFrame: Scraping result of the regarding SSRN category
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
    }
    section_to_scrape = section_mapping_dict[section_to_scrape]
    # Create the soup from the request
    soup = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")

    # Create the final table, since AnnType_1 has is distinct from every other section we need a separte case
    if section_to_scrape == "AnnType_1":
        conference_df = pd.DataFrame(columns=["Conference", "Dates", "Location", "Posted", "Conf_Link", "Section"])
    else:
        # less entries
        conference_df = pd.DataFrame(columns=["Conference", "Posted", "Conf_Link", "Section"])
    # Check if the respective section exists in the first place to avoid scraping errors
    if soup.find("div", {"id": section_to_scrape}):
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
                    try:
                        conf_dates_start.append(pd.Timestamp(item[0].text.replace("Conference Dates: ", "").split(" - ")[0]))
                        conf_dates_end.append(pd.Timestamp(item[0].text.replace("Conference Dates: ", "").split(" - ")[1]))
                    except:
                        print("Problems while transforming item into a pd.Timestamp at conf_dates_start/conf_dates_end")
                elif "Posted" in item[0].text:
                    try:
                        conf_dates_start.append(pd.Timestamp(item[0].text.replace("Posted: ", "")))
                        conf_dates_end.append("")
                    except:
                        print("Problems while transforming item into a pd.Timestamp at Posted Version")
                else:
                    try:
                        conf_dates_start.append(pd.Timestamp(item[0].text.replace("Conference Date: ", "")))
                        conf_dates_end.append("")
                    except:
                        print("Problems while transforming item into a pd.Timestamp")
                conf_location.append(item[1].text.replace("Location: ", ""))
                conf_posted_dates.append(pd.Timestamp(item[2].text.replace("Posted: ", "")))
        else:
            conf_posted_dates = []
            for p_date in soup.find("div", {"id": section_to_scrape}).find_all("p", {"class": "posted-date"}):
                try:
                    conf_posted_dates.append(pd.Timestamp(p_date.text.replace("Posted: ", "")))
                except:
                    print("Problems while transforming item into a pd.Timestamp at conf_dates_posted")
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
            conference_df["Duration"] = str(pd.Series(conf_dates_end) - pd.Series(conf_dates_start))

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
    else:
        print(f"Section: {section_to_scrape} not available at the current url: {url}")


url = "https://www.ssrn.com/index.cfm/en/janda/professional-announcements/?annsNet=203"
section_to_scrape = "Call for papers and participants - Conference"
save = False
path_save = "//Users//Robert_Hennings//Dokumente//Uni//MusterBewerbung//MeineArbeitgeber//SHK Uni DUE FIN//Arbeitsordner//"
file_name = "SSRN_scraped"
history = False
scrape_ssrn_notifications(url=url, section_to_scrape=section_to_scrape,
                          save=save, path_save=path_save, file_name=file_name,
                          section_mapping_dict=section_mapping_dict)

# to keep consitent track of the historical evolvement of the announcements we need to keep a historic overview
# also highlight if there are new entries that werent in the last scraped version
# also integrate that if there are new releases and infos regarding Patricks Selection in his most recent excel file, it should automatically recognize the already existing names in the file
# we should also scrape multiple Website sections, so different AnnTypes

database = scrape_ssrn_notifications(url=url, section_to_scrape=section_to_scrape, save=save, path_save=path_save, file_name=file_name)
# database = pd.read_excel("//Users//Robert_Hennings//Dokumente//Uni//MusterBewerbung//MeineArbeitgeber//SHK Uni DUE FIN//Arbeitsordner//SSRN_scraped.xlsx", sheet_name="ScrapingHistory", engine="openpyxl")
# also incorporate all the information that has been scraped from the single conference websites
# Lets now also investigate if we can get more data from the single conference websites from SSRN
# take one example: https://www.ssrn.com/index.cfm/en/janda/announcement/?id=13401
def scrape_single_ssrn_conf_links(link: str) -> pd.DataFrame:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
    }
    # For debugging
    # link = database.Conf_Link[2]
    soup = BeautifulSoup(requests.get(link, headers=headers).content, "html.parser")
    # Extract the whole text and its single passages from the website
    # get the conference dates
    conf_dates = soup.find_all("div", {"class": "form-group"})[0].text.strip().replace("\n", " ")
    # get the location
    conf_location = soup.find_all("div", {"class": "form-group"})[1].text.strip().replace("\n", " ")
    # get the actual website text
    # Word Description from the text, its sub-headline
    # soup.find_all("div", {"class": "form-group"})[2].text.strip().split("\n")[0]
    # raw text
    string_list = []
    for i in soup.find_all("div", {"class": "form-group"})[2].stripped_strings:
        string_list.append(i)

    website_text = " ".join(string_list).replace("o\t", "")
    deadline_date = extract_submission_deadline(website_text)
    deadline_date = pd.to_datetime(deadline_date).strftime("%Y-%d-%m")
    # Now we have to find the keywords in the soup
    # find submission deadline date, try out different word combinations but then still
    # the problem is until where to take out the values to get the actual date
    # different variants: PAPER SUBMISSION, Submission Deadline, Deadline for submission, Submission Deadline, SUBMISSION DEADLINE
    # but when the string chain is found, how to extract the actual dates?

    # word = "submission"
    # start_word = soup.text.lower().find(word)
    # end_word = start_word + len("submission")
    # offset = 60

    # soup.text.lower()[start_word:end_word+offset]

    # find format of submission
    # search for the word "format" or alternatively direct for the version of the format
    # if we find a certain format we save the number of its occurrences in the dict
    submission_formats = {"pdf": [],
                        "word": [],
                        "docx": [],
                        "doc": [],
                        "latex": [],
                        "tex": []} # especially for the tex variant we need the second search variant because otherwise text will be identified
    submission_formats_position = {"pdf": [],
                        "word": [],
                        "docx": [],
                        "doc": [],
                        "latex": [],
                        "tex": []}
    links = []
    # generic find function in the text that finds first occurrence of the word
    for form in submission_formats_position.keys():
        submission_formats_position[form].append(website_text.lower().find(form) if website_text.lower().find(form) != -1 else "")
    # second variant that counts ALL occurrences in the single words
    for form in submission_formats.keys():
        for word in website_text.split():
            if form in word.lower():
                submission_formats[form].append(1)
    # Extract the Homepage or any other affiliated websites by searching for http
    for word in website_text.split():
        if "http" in word.lower():
            links.append(word)

    website_df = pd.DataFrame(index=range(1))
    website_df["link"] = link
    website_df["scraped_website_links"] = ", ".join(links)
    website_df["submission_deadline"] = deadline_date
    website_df["scraped_website_text"] = website_text

    for it in submission_formats_position.items():
        submission_formats[it[0]] = 1 if submission_formats_position[it[0]] != [''] else 0

    for it in submission_formats.items():    
        website_df[it[0]] = it[1]

    return website_df

# Loop over the single links stored in the database

master_link_df = pd.DataFrame()
for li in database.Conf_Link:
    temp_df = scrape_single_ssrn_conf_links(li)
    master_link_df = pd.concat([master_link_df, temp_df])
master_link_df.reset_index(drop=True, inplace=True)

# Merge both dataframes
database = pd.merge(database, master_link_df, left_on="Conf_Link", right_on="link")

# Now update if its necessary
file_name = "Finance_Conferences_Overview_most_recent.xlsx"
file_path = "//Users//Robert_Hennings//Dokumente//Uni//MusterBewerbung//MeineArbeitgeber//SHK Uni DUE FIN//Arbeitsordner//"
sheet_name = "Conference_Overview"
sheet_name_keep = ["Journals_Overview"]

def update_conferences(file_name, file_path, sheet_name, database, sheet_name_keep) -> pd.DataFrame:
    # Read in the existing Overview Sheet that needs to be updated
    to_be_updated_conf = pd.read_excel(file_path + "//" + file_name, sheet_name=sheet_name, engine="openpyxl")
    for sh in sheet_name_keep:
        vars()[sh] = pd.read_excel(file_path + "//" + file_name, sheet_name=sh, engine="openpyxl")
    # Merge both dataframes based on the common conference names and update the old data
    update = pd.merge(database, to_be_updated_conf, left_on="Conference", right_on="Name")
    # Loop over every conference and update its values
    for conf in update.Conference:
        # Watch out: Names must be 100% identical to have a match and be updatable
        # Update the Duration
        to_be_updated_conf.loc[to_be_updated_conf.Name == conf, "Duration\n(days)"] = int(update[update.Conference == conf].Duration[0].days)
        # Update the Date
        start = update[update.Conference == conf]["Dates Start"].dt.strftime("%d-%m")[0]
        end = update[update.Conference == conf]["Dates End"].dt.strftime("%d-%m-%Y")[0]

        to_be_updated_conf.loc[to_be_updated_conf.Name == conf, "Date"] = start + " to " + end
        # Update the location
        to_be_updated_conf.loc[to_be_updated_conf.Name == conf, "Place"] = update[update.Conference == conf].Location.values[0]
    # After the update the current values in the given sheet should be overriden and saved again
    # Here watch out to keep all the other sheets and contents of the existing file
    with pd.ExcelWriter(file_path + "//" + file_name, mode="a", if_sheet_exists="replace") as writer:
        to_be_updated_conf.to_excel(writer, sheet_name=sheet_name, index=False)
        for sh in sheet_name_keep:
            vars()[sh].to_excel(writer, sheet_name=sheet_name, index=False)

update_conferences(file_name, file_path, sheet_name, database, sheet_name_keep)


#database.to_excel("SSRN_scraped.xlsx", index=False)
