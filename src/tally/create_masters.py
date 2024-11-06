import pandas as pd
from datetime import datetime
from .helpers import convert_to_tally_date
from .loadclr import tally

from System.Collections.Generic import List as CSList  # type: ignore # noqa: E402
from TallyConnector.Core.Models import (  # type: ignore # noqa: E402
    LedgerGSTRegistrationDetails,
    LedgerMailingDetails,
    GSTRegistrationType,
    GSTDetail,
    StateWiseDetail,
    GSTTaxabilityType,
    GSTRateDetail,
    TaxType,
)
from TallyConnector.Core.Models.Masters import Ledger  # type: ignore # noqa: E402
from TallyConnector.Core.Models.Masters.Inventory import StockItem, Unit, HSNDetail  # type: ignore # noqa: E402


# ? Start of the financial year
applicable_from = convert_to_tally_date(f"01/04/{datetime.now().year}")

DEFAULT_LEDGER = {
    "Purchase": {
        "Name": "TallAi - Purchase Account",
        "Group": "Purchase Accounts",
    },
    "Sales": {
        "Name": "TallAi - Sales Account",
        "Group": "Sales Accounts",
    },
    "Tax": {
        "Name": "IGST",
        "Group": "Duties & Taxes",
    },
}


TALLY_NA = "\u0004 Not Applicable"


def create_party_account(common_df: pd.DataFrame, ledger_names: list[str]):
    is_sales = common_df["Voucher Type"].iloc[0] == "Sales"
    perspective = "Customer" if is_sales else "Supplier"

    party_account = common_df["[D] Party Account"].iloc[0]
    if pd.isna(party_account):
        party_account = common_df["Party Account"].iloc[0]

    if party_account in ledger_names:
        return

    ledger = Ledger()
    ledger.OldName = party_account
    ledger.Name = party_account
    ledger.Group = "Sundry Debtors" if is_sales else "Sundry Creditors - Purchases"

    # Create a LedgerGSTRegistrationDetails object
    gstin = common_df[f"{perspective} GSTIN"].iloc[0]
    if not pd.isna(gstin):
        gst_registration_details = LedgerGSTRegistrationDetails()
        gst_registration_details.GSTIN = common_df[f"{perspective} GSTIN"].iloc[0]
        gst_registration_details.State = (
            common_df[f"{perspective} State"].iloc[0] or TALLY_NA
        )
        gst_registration_details.GSTRegistrationType = GSTRegistrationType.Regular
        gst_registration_details.ApplicableFrom = applicable_from
        ledger.LedgerGSTRegistrationDetails = CSList[LedgerGSTRegistrationDetails]()
        ledger.LedgerGSTRegistrationDetails.Add(gst_registration_details)

    # Create a LedgerMailingDetails object
    mailing_details = LedgerMailingDetails()
    mailing_details.Address = common_df[f"{perspective} Address"].iloc[0] or ""
    mailing_details.MailingName = party_account
    mailing_details.State = common_df[f"{perspective} State"].iloc[0] or TALLY_NA
    mailing_details.Country = "India"
    # mailing_details.PinCode = common_df[f"{perspective} Pincode"].iloc[0]
    mailing_details.ApplicableFrom = applicable_from
    ledger.LedgerMailingDetails = CSList[LedgerMailingDetails]()
    ledger.LedgerMailingDetails.Add(mailing_details)

    tally.PostLedgerAsync(ledger).Result
    print(f"Created {perspective} Ledger with {ledger.Name}")

    # ? Update ledger names
    ledger_names.append(party_account)
    common_df.loc[0, "[D] Party Account"] = party_account


def create_units(items_df: pd.DataFrame):
    units = tally.GetUnitsAsync[Unit]().Result
    unit_names = [unit.Name for unit in units]
    for idx, unit_name in enumerate(items_df["[D] Units"]):
        if pd.isna(unit_name):
            unit_name = items_df["Quantity Unit"].iloc[idx]
            items_df.loc[idx, "[D] Units"] = unit_name

        if unit_name in unit_names:
            continue

        unit = Unit()
        unit.Name = unit_name
        tally.PostUnitAsync[Unit](unit).Result
        unit_names.append(unit_name)
        print(f"Created Unit: {unit_name}")

        items_df.loc[idx, "[D] Units"] = unit_name


def create_stock_items(items_df: pd.DataFrame):
    stock_items = tally.GetStockItemsAsync[StockItem]().Result
    stock_item_names = [item.Name for item in stock_items]
    for idx, stock_item_name in enumerate(items_df["[D] Stock Item"]):
        if pd.isna(stock_item_name):
            stock_item_name = items_df["Product Name"].iloc[idx]

        if stock_item_name in stock_item_names:
            continue

        stock_item = StockItem()
        stock_item.OldName = stock_item_name
        stock_item.Name = stock_item_name
        stock_item.BaseUnit = items_df["[D] Units"].iloc[idx]

        hsn_code = items_df["HSN code"].iloc[idx]
        if not pd.isna(hsn_code):
            hsn_code = str(hsn_code)
            hsn_details = HSNDetail()
            hsn_details.HSNCode = hsn_code
            hsn_details.ApplicableFrom = applicable_from
            hsn_details.SourceOfHSNDetails = "Specify Details Here"
            # hsn_details.HSNDescription = "Description"
            stock_item.HSNDetails = CSList[HSNDetail]()
            stock_item.HSNDetails.Add(hsn_details)

        tax_rate = items_df["Tax Rate"].iloc[idx]
        if pd.api.types.is_numeric_dtype(tax_rate):
            tax_rate = tax_rate.item()

            gst_rate_details = GSTRateDetail()
            gst_rate_details.DutyHead = "IGST"
            gst_rate_details.ValuationType = "Based on Value"
            gst_rate_details.GSTRate = tax_rate

            state_wise_details = StateWiseDetail()
            state_wise_details.StateName = "\u0004 Any"
            state_wise_details.GSTRateDetails = CSList[GSTRateDetail]()
            state_wise_details.GSTRateDetails.Add(gst_rate_details)

            gst_details = GSTDetail()
            gst_details.ApplicableFrom = applicable_from
            gst_details.SourceOfGSTDetails = "Specify Details Here"
            gst_details.Taxability = GSTTaxabilityType.Taxable
            gst_details.StateWiseDetails = CSList[StateWiseDetail]()
            gst_details.StateWiseDetails.Add(state_wise_details)

            stock_item.GSTDetails = CSList[GSTDetail]()
            stock_item.GSTDetails.Add(gst_details)

        # Add gst rate and hsn code
        tally.PostStockItemAsync[StockItem](stock_item).Result
        stock_item_names.append(stock_item_name)
        print(f"Created Stock Item: {stock_item_name}")

        items_df.loc[idx, "[D] Stock Item"] = stock_item_name


def create_masters_sales_purchase(common_df: pd.DataFrame, items_df: pd.DataFrame):
    ledgers = tally.GetLedgersAsync[Ledger]().Result
    ledger_names = [ledger.Name for ledger in ledgers]

    # ? Create ledgers
    create_party_account(common_df, ledger_names)

    voucher_type = common_df["Voucher Type"].iloc[0]
    other_ledger = DEFAULT_LEDGER[voucher_type]
    # ? Create default ledgers
    if other_ledger["Name"] not in ledger_names:
        ledger = Ledger()
        ledger.Name = other_ledger["Name"]
        ledger.Group = other_ledger["Group"]
        tally.PostLedgerAsync[Ledger](ledger).Result

        # ? Update ledger names
        ledger_names.append(ledger.Name)
        print(f"Created {voucher_type} Ledger with {ledger.Name}")

    # ? Create IGST ledger
    if "IGST" not in ledger_names:
        ledger = Ledger()
        ledger.Name = DEFAULT_LEDGER["Tax"]["Name"]
        ledger.Group = DEFAULT_LEDGER["Tax"]["Group"]
        ledger.TaxType = TaxType.GST
        ledger.GSTTaxType = "IGST"
        tally.PostLedgerAsync[Ledger](ledger).Result

        # ? Update ledger names
        ledger_names.append(ledger.Name)
        print("Created IGST Ledger")

    # ? Create units
    create_units(items_df)

    # ? Create stock items
    create_stock_items(items_df)


def create_masters_journal(ledgers_df: pd.DataFrame):
    ledgers = tally.GetLedgersAsync[Ledger]().Result
    ledger_names = [ledger.Name for ledger in ledgers]

    for _, item in ledgers_df.iterrows():
        ledger_name = item["[D] Account Name"]
        if pd.isna(ledger_name):
            ledger_name = item["Account Name"]
            item["[D] Account Name"] = ledger_name

        if ledger_name in ledger_names:
            return

        ledger = Ledger()
        ledger.Name = ledger_name
        ledger.Group = item["Account Group"]

        # Create a LedgerGSTRegistrationDetails object
        gst_registration_details = LedgerGSTRegistrationDetails()
        gst_registration_details.GSTIN = item["Account GSTIN"]
        gst_registration_details.State = item["Account State"]
        gst_registration_details.GSTRegistrationType = GSTRegistrationType.Regular
        gst_registration_details.ApplicableFrom = applicable_from
        ledger.LedgerGSTRegistrationDetails = CSList[LedgerGSTRegistrationDetails]()
        ledger.LedgerGSTRegistrationDetails.Add(gst_registration_details)

        # Create a LedgerMailingDetails object
        mailing_details = LedgerMailingDetails()
        mailing_details.Address = item["Account Address"]
        mailing_details.MailingName = ledger_name
        mailing_details.State = item["Account State"]
        mailing_details.Country = "India"
        # mailing_details.PinCode = common_df[f"{perspective} Pincode"].iloc[0]
        mailing_details.ApplicableFrom = applicable_from
        ledger.LedgerMailingDetails = CSList[LedgerMailingDetails]()
        ledger.LedgerMailingDetails.Add(mailing_details)

        tally.PostLedgerAsync[Ledger](ledger).Result

        # ? Update ledger names
        ledger_names.append(ledger_name)
        print(f"Created Ledger: {ledger_name}")


def create_masters(common_df: pd.DataFrame, items_df: pd.DataFrame):
    voucher_type = common_df["Voucher Type"].iloc[0]
    if voucher_type in ["Sales", "Purchase"]:
        create_masters_sales_purchase(common_df, items_df)
    else:
        create_masters_journal(items_df)
