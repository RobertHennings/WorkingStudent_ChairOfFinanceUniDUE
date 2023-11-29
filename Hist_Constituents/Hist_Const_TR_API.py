# Import necessary libraries
import glob
import eikon as ek
import numpy as np
import pandas as pd
import yaml

# Set api key and opening the workspace simulatenously
glob.os.chdir(glob.os.path.join('/Users/Robert_Hennings/Dokumente/Uni/MusterBewerbung/MeineArbeitgeber/SHK Uni DUE FIN/Arbeitsordner/RIC_Screening'))
# Load secrets
credentials = yaml.load(open('./secrets.yml'), Loader=yaml.FullLoader)
app_key = credentials['Reuters_Terminal']['Reuters_API_Key']
ek.set_app_key(app_key)

glob.os.chdir(glob.os.path.join('/Users/Robert_Hennings/Dokumente/Uni/MusterBewerbung/MeineArbeitgeber/SHK Uni DUE FIN/Arbeitsordner/Hist_Constituents'))
# Retrieve historical Index Constituents for the following German Indices
# DAX, TecDax, MDAX, SDAX, CDAX, starting 1980, must be in: 2010

# There are multiple ways to retrieve the desired data
# First method
df = ek.get_data('0#.GDAXI(20150331)', ['TR.RIC', "TR.DSCD"])
df = ek.get_data('0#.CDAX(20000131)', ['TR.RIC'])
df = ek.get_data('.GDAXI', ['TR.IndexConstituentRIC'])
# Second method
df, err = ek.get_data(
    instruments=['0#.SPX'],
    fields=['TR.IndexConstituentRIC',
            'TR.IndexConstituentName'],
    parameters={
        'SDate': '1996-01-02'
    }
)
# Third method
start_date = "01-01-2000"
end_date = "06-10-2023"
freq="M"
Instrument = "CDAX"

def get_historic_index_constituents(Instrument: str, start_date: str,
                                    end_date: str, freq: str) -> pd.DataFrame:
    """Retrieves historical Index Constituents for an Index given as Instrument
       The availability and quality of the data can vary with given Index

    Args:
        Instrument (str): RIC Ticker provided by Reuters for the Index
        start_date (str): Start of the History
        end_date (str): End of the History
        freq (str): Either get daily or monthly constituent data

    Returns:
        pd.DataFrame: 2 pd.DataFrames, first one holding the Instrument, the second one holding the RIC
    """
    historic_constit_Instrument = pd.DataFrame()
    historic_constit_RIC = pd.DataFrame()

    d_range = pd.date_range(start_date, end_date, freq=freq)
    for date in d_range:
        print(f"Loading Data for Date: {date} for Instrument: {Instrument}")
        print(f"Progress: {np.round((d_range.to_list().index(date) / len(d_range)), 2) * 100} %")
        try:
            date_constit_df = ek.get_data(f'0#.{Instrument}({date.strftime("%Y%m%d")})', ['TR.RIC'])
            date_constit_df = pd.DataFrame(date_constit_df[0])
            date_constit_df.columns = [date for col in date_constit_df.columns]
        except:
            print("Error during data loading")
        try:
            historic_constit_Instrument = pd.concat([historic_constit_Instrument, date_constit_df.iloc[:, 0]], axis=1)

            historic_constit_RIC = pd.concat([historic_constit_RIC, date_constit_df.iloc[:, 1]], axis=1)
        except:
            print("error while Data Transforming")
    return historic_constit_Instrument.transpose(), historic_constit_RIC.transpose()


hist_Inst, hist_RIC = get_historic_index_constituents(Instrument=Instrument,
                                                      start_date=start_date,
                                                      end_date=end_date,
                                                      freq=freq)


with pd.ExcelWriter("Historical_Constituents.xlsx", mode="a", engine="openpyxl") as writer:
    hist_RIC.to_excel(writer, sheet_name="CDAX")
