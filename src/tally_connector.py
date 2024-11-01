import pandas as pd
from .find_match import find_closest_match
import sys
from pythonnet import load


load("coreclr")
sys.path.append("../TallyConnector")

import clr  # noqa: E402

clr.AddReference("TallyConnector")

from TallyConnector.Services import TallyService  # noqa: E402

tally = TallyService()


def get_tally_company() -> str:
    # ? this will throw an exception if Tally is not running
    tally.CheckAsync().Result
    active_company = tally.GetActiveCompanyAsync().Result.Name

    return active_company


# TODO: Match units and other fields
def match_masters(common_df: pd.DataFrame, items_df: pd.DataFrame):
    # ? Match supplier name to ledger name
    supplier_name = common_df["Supplier Name"].iloc[0]
    ledgers = tally.GetLedgersAsync().Result
    ledger_names = [ledger.Name for ledger in ledgers]
    supplier_ledger_name = find_closest_match(supplier_name, ledger_names)
    common_df["[D] Party Account"] = supplier_ledger_name

    stock_items = tally.GetStockItemsAsync().Result
    stock_item_names = [item.Name for item in stock_items]
    items_df["[D] Stock Item"] = items_df["Product Name"].apply(
        lambda x: find_closest_match(x, stock_item_names)
    )

    units = tally.GetUnitsAsync().Result
    unit_names = [unit.Name for unit in units]
    items_df["[D] Units"] = items_df["Quantity Unit"].apply(
        lambda x: find_closest_match(x, unit_names)
    )

    return common_df, items_df


def create_masters(common_df: pd.DataFrame, items_df: pd.DataFrame):
    pass


def create_voucher(common_df: pd.DataFrame, items_df: pd.DataFrame):
    pass
