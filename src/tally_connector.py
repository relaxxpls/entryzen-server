from typing import List, Dict
import pandas as pd
from .find_match import find_closest_match

type MasterData = Dict[str, List[str]]


# TODO: Match units and other fields
def match_masters(common_df: pd.DataFrame, items_df: pd.DataFrame):
    supplier_name = common_df["Supplier Name"].iloc[0]
    supplier_ledger_name = find_closest_match(supplier_name, masters_data["LEDGER"])
    common_df["Supplier Ledger Name"] = supplier_ledger_name

    items_df["Stock Item"] = items_df["Product Name"].apply(
        lambda x: find_closest_match(x, masters_data["STOCKITEM"])
    )

    return common_df, items_df
