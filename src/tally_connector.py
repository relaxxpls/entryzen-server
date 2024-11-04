from .tally import loadclr as _
import pandas as pd
from .find_match import find_closest_matches, batch_match_column

from TallyConnector.Services import TallyService  # type: ignore # noqa: E402
from TallyConnector.Core.Models.Masters import Ledger  # type: ignore # noqa: E402
from TallyConnector.Core.Models.Masters.Inventory import StockItem, Unit  # type: ignore # noqa: E402

tally = TallyService()


def get_tally_company() -> str:
    # ? this will throw an exception if Tally is not running
    tally.CheckAsync().Result
    active_company = tally.GetActiveCompanyAsync().Result.Name

    return active_company


def match_masters(common_df: pd.DataFrame, items_df: pd.DataFrame):
    # ? Match supplier name to ledger name
    ledgers = tally.GetLedgersAsync[Ledger]().Result
    ledger_names = [ledger.Name for ledger in ledgers]
    supplier_name = common_df["Supplier Name"].iloc[0]
    customer_name = common_df["Customer Name"].iloc[0]
    voucher_type = common_df["Voucher Type"].iloc[0]
    party_account = supplier_name if voucher_type == "Purchase" else customer_name
    common_df["Party Account"] = party_account
    common_df["[D] Party Account"] = find_closest_matches(
        common_df["Party Account"], ledger_names
    )

    stock_items = tally.GetStockItemsAsync[StockItem]().Result
    stock_item_names = [item.Name for item in stock_items]
    items_df["[D] Stock Item"] = batch_match_column(
        items_df["Product Name"], stock_item_names
    )

    units = tally.GetUnitsAsync[Unit]().Result
    unit_names = [unit.Name for unit in units]
    items_df["[D] Units"] = batch_match_column(items_df["Quantity Unit"], unit_names)

    return common_df, items_df
