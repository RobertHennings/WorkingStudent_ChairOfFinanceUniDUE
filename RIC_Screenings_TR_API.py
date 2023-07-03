# Import necessary libraries
import refinitiv.data as rd
from refinitiv.data.content import search
import glob
import eikon as ek
import numpy as np
import pandas as pd
import time
import yaml
# Set api key and opening the workspace simulatenously
glob.os.chdir(glob.os.path.join('/Users/Robert_Hennings/Dokumente/Uni/MusterBewerbung/MeineArbeitgeber/SHK Uni DUE FIN/Arbeitsordner/RIC_Screening'))
# Load secrets
credentials = yaml.load(open('./secrets.yml'), Loader=yaml.FullLoader)

app_key = credentials['Reuters_Terminal']['Reuters_API_Key']
ek.set_app_key(app_key=app_key)
# First test the default function that is provided, transfering the ISIN to RIC
# Also test to get the Listing Status
ek.get_data('MUVGn.DE', 'TR.InstrumentListingStatus')
# Returns multiple RICs/ all that are known to the Data Vendor
ek.get_symbology(["DE0005774509"], from_symbol_type='ISIN', to_symbol_type='RIC', best_match=False).RICs[0]
# Shows all the delisted comps and not the actual ticker


# Next open a local session with the API Key
rd.open_session(app_key=app_key)

# Next write function that searches the corresponding RIC Code for a provided ISIN, restrict the returned list to top number
def find_ric_to_isin(isin: str, exchange_code: str, business_entity: str, include_listed_only: bool, top: int = 10) -> pd.DataFrame:
    response = search.Definition(
        view=search.Views.SEARCH_ALL,
        select="ExchangeCode, RIC, IssueISIN, DTSubjectName,ExchangeName,RIC,BusinessEntity,PI", 
        filter=f"(IssueISIN eq '{isin}' and ExchangeCode eq '{exchange_code}' and BusinessEntity eq '{business_entity}')",
        top=top
    ).get_data()

    response = response.data.df

    ListingStatus = [ek.get_data(ric, 'TR.InstrumentListingStatus')[0]["Instrument Listing Status"].values[0] for ric in response.RIC]
    
    response["ListingStatus"] = ListingStatus

    if include_listed_only:
        response = response[response.ListingStatus == "Listed"]
        response.reset_index(drop=True, inplace=True)

    return response

# test the function for an ISIN
isin = "DE0008022005"
exchange_code = "GER"
business_entity = "QUOTExEQUITY"
include_listed_only = False
top = 10
find_ric_to_isin(isin, exchange_code, business_entity, include_listed_only, top)


# Also implement a more general serach query function that might lead to better results
# not depending on the ISISN but rather on the Name from the file

def find_ric_to_name(name, exchange_code: str, business_entity: str, include_listed_only: bool, top: int = 10) -> pd.DataFrame:
    response = rd.discovery.search(name,
                                   view = rd.discovery.Views.SEARCH_ALL,
                                   select = "DTSubjectName,ExchangeName,RIC,BusinessEntity,PI,IssueISIN,ExchangeCode",
                                   filter=f"(ExchangeCode eq '{exchange_code}' and BusinessEntity eq '{business_entity}')",
                                   top=top)
    
    # Check for listing status
    ListingStatus = [ek.get_data(ric, 'TR.InstrumentListingStatus')[0]["Instrument Listing Status"].values[0] for ric in response.RIC]
    time.sleep(1)
    response["ListingStatus"] = ListingStatus

    if include_listed_only:
        response = response[response.ListingStatus == "Listed"]
        response.reset_index(drop=True, inplace=True)

    return response

# Test the function
name = "MUENCHENER RUECKVERSICHERUNGS GESELLSCHAFT IN"
exchange_code = "GER"
business_entity = "QUOTExEQUITY"
include_listed_only = False
top = 10
# Add a filtering for the activity status of the ticker to only include non delisted ones
find_ric_to_name(name, exchange_code, business_entity, include_listed_only, top)

# Now combine both methods to be sure, also search for the isin
def find_ric_to_name_isin(name: str, exchange_code: str, business_entity: str, isin: str, include_listed_only: bool, top: int) -> pd.DataFrame:
    response = rd.discovery.search(name,
                                   view = rd.discovery.Views.SEARCH_ALL,
                                   select = "DTSubjectName,ExchangeName,RIC,BusinessEntity,PI,IssueISIN,ExchangeCode",
                                   filter=f"(ExchangeCode eq '{exchange_code}' and BusinessEntity eq '{business_entity}' and IssueISIN eq '{isin}')",
                                   top=top)

    # Check for listing status
    ListingStatus = [ek.get_data(ric, 'TR.InstrumentListingStatus')[0]["Instrument Listing Status"].values[0] for ric in response.RIC]
    time.sleep(1)
    response["ListingStatus"] = ListingStatus

    if include_listed_only:
        response = response[response.ListingStatus == "Listed"]
        response.reset_index(drop=True, inplace=True)

    return response

# Test the function
name = "MUENCHENER RUECKVERSICHERUNGS GESELLSCHAFT IN"
exchange_code = "GER"
business_entity = "QUOTExEQUITY"
isin = "DE0008430042"
include_listed_only = False
top = 10

find_ric_to_name_isin(name, exchange_code, business_entity, isin, include_listed_only, top)

# Test the last function on a bigger scale for the given Data
file_path = glob.os.path.join("/Users/Robert_Hennings/Dokumente/Uni/MusterBewerbung/MeineArbeitgeber/SHK Uni DUE FIN/Arbeitsordner/RIC_Screening")
file_name = "Germany Request Full.xlsx"

excel_file = pd.read_excel(file_path + "//" + file_name, sheet_name="EMPTY_RIC", engine="openpyxl")

# Extract the company name and isin and loop over with function
comp_names = excel_file.ecname.values
comp_isins = excel_file["isin"].values

# Always choose the first result
exchange_code = "GER"
business_entity = "QUOTExEQUITY"
include_listed_only = False
top = 10

ric_com_name = []
ric_err = []


# When we allow for Delisted ones, how should we filter? There are more options!
# For now just take the first one
for c_name, c_isin in zip(comp_names, comp_isins):
    try:
        ric_com_name.append(find_ric_to_name_isin(c_name, exchange_code, business_entity, c_isin, include_listed_only, top).RIC.values)
    except:
        print(f"Err at: {c_name}, trying other function for the ISIN")
        try:
            ric_com_name.append(find_ric_to_isin(c_isin, exchange_code, business_entity, include_listed_only, top).RIC.values)
            ric_err.append([c_name, c_isin])
        except:
            print(f"Nothing available for ISIN: {c_isin}")

# For the one that ended up with no results searching for the isin, use the default function: ek.get_symbology(["DE0005774509"], from_symbol_type='ISIN', to_symbol_type='RIC', best_match=False).RICs[0] and perform filters on 
ric_screened = pd.DataFrame([comp_names, comp_isins, ric_com_name]).T
ric_screened.columns = ["ecname", "isin", "ric"]

unpacked_ric = ric_screened['ric'].apply(pd.Series).add_prefix('ric_')
ric_screened = pd.concat([ric_screened.drop('ric', axis=1), unpacked_ric], axis=1)

with pd.ExcelWriter(file_path + "//" + file_name, mode="a") as writer:
    ric_screened.to_excel(writer, sheet_name="RIC_Screen", index=False)



default_func_rics = []
# for c_isin in ric_screened.iloc[354:,:]["isin"].values[:5]:
#     default_func_rics.append(ek.get_symbology([str(c_isin)], from_symbol_type='ISIN', to_symbol_type='RIC', best_match=False).RICs[0])
for c_isin in comp_isins.values:
    try:
        default_func_rics.append(ek.get_symbology([str(c_isin)], from_symbol_type='ISIN', to_symbol_type='RIC', best_match=False).RICs[0])
    except:
        print(f"Err at: {c_isin}")

with pd.ExcelWriter(file_path + "//" + file_name, mode="a") as writer:
    pd.concat([ric_screened, pd.Series(default_func_rics).apply(pd.Series).add_prefix('ric_')], axis=1).to_excel(writer, sheet_name="RIC_ScreenDEF_Func", index=False)
rd.close_session()