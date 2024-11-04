import pandas as pd
from datetime import datetime
from .loadclr import tally
from .helpers import convert_to_tally_date
from .create_masters import DEFAULT_LEDGER

from System import Decimal  # type: ignore # noqa: E402
from System.Collections.Generic import List as CSList  # type: ignore # noqa: E402
from TallyConnector.Core.Converters.XMLConverterHelpers import (  # type: ignore # noqa: E402
    TallyAmount,
    TallyQuantity,
    TallyRate,
)
from TallyConnector.Core.Models import (  # type: ignore # noqa: E402
    Voucher,
    BaseVoucherLedger,
    AllInventoryAllocations,
    VoucherLedger,
)


def create_vouchers(common_df: pd.DataFrame, items_df: pd.DataFrame):
    multiplier = 1 if common_df["Voucher Type"].iloc[0] == "Sales" else -1
    voucher_type = common_df["Voucher Type"].iloc[0]

    voucher = Voucher()
    voucher.VoucherType = voucher_type
    voucher.Date = convert_to_tally_date(datetime.now())
    voucher.Reference = common_df["Document Number"].iloc[0]
    voucher.ReferenceDate = convert_to_tally_date(common_df["Document Date"].iloc[0])
    voucher.Narration = common_df["Narration"].iloc[0]

    voucher.InventoryAllocations = CSList[AllInventoryAllocations]()

    for idx, item in items_df.iterrows():
        ledger_contra = BaseVoucherLedger()
        ledger_contra.LedgerName = DEFAULT_LEDGER[voucher_type]["Name"]
        ledger_contra.Amount = TallyAmount(Decimal(item["Taxable Amount"] * multiplier))

        inventory_allocation = AllInventoryAllocations()
        inventory_allocation.IndexNumber = idx
        inventory_allocation.StockItemName = item["Product Name"]
        inventory_allocation.ActualQuantity = TallyQuantity(Decimal(item["Quantity"]))
        inventory_allocation.BilledQuantity = TallyQuantity(Decimal(item["Quantity"]))
        inventory_allocation.Rate = TallyRate(Decimal(item["Rate"]))
        inventory_allocation.Amount = ledger_contra.Amount
        inventory_allocation.Ledgers = CSList[BaseVoucherLedger]()
        inventory_allocation.Ledgers.Add(ledger_contra)

        voucher.InventoryAllocations.Add(inventory_allocation)

    net_total = items_df["Total Amount"].sum()
    net_tax = items_df["Tax Amount"].sum()

    ledger_party = VoucherLedger()
    ledger_party.LedgerName = common_df["[D] Party Account"].iloc[0]
    ledger_party.Amount = TallyAmount(Decimal(net_total * multiplier * -1))

    ledger_igst = VoucherLedger()
    ledger_igst.LedgerName = DEFAULT_LEDGER["Tax"]["Name"]
    ledger_igst.Amount = TallyAmount(Decimal(net_tax * multiplier))

    voucher.Ledgers = CSList[VoucherLedger]()
    voucher.Ledgers.Add(ledger_party)
    voucher.Ledgers.Add(ledger_igst)

    # ledger_cgst = BaseVoucherLedger()
    # ledger_cgst.LedgerName = "CGST"
    # ledger_cgst.Amount = common_df["CGST"].iloc[0] * multiplier

    # ledger_sgst = BaseVoucherLedger()
    # ledger_sgst.LedgerName = "SGST"
    # ledger_sgst.Amount = common_df["SGST"].iloc[0] * multiplier

    tally.PostVoucherAsync(voucher).Result
