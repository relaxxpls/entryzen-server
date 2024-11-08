import pandas as pd

from .parse_pdf import is_journal_voucher


def verify_amounts_sales_purchase(items_df: pd.DataFrame):
    errors: list[str] = []
    for idx, row in items_df.iterrows():
        rate = row["Rate"]
        discount = row["Discount"]
        quantity = row["Quantity"]
        taxable_amount = row["Taxable Amount"].round(1)
        taxable_amount_calc = (rate * quantity - discount).round(1)
        if abs(taxable_amount - taxable_amount_calc) > 0.1:
            errors.append(
                f"[Row {idx}] Taxable Amount {taxable_amount}, Calculated Taxable Amount: {taxable_amount_calc}"
            )

        tax_amount = row["Tax Amount"].round(1)
        tax_amount_calc = (taxable_amount * row["Tax Rate"] / 100).round(1)
        if abs(tax_amount - tax_amount_calc) > 0.1:
            errors.append(
                f"[Row {idx}] Tax Amount {tax_amount}, Calculated Tax Amount: {tax_amount_calc}"
            )

        total_amount = row["Total Amount"].round(1)
        total_amount_calc = (taxable_amount + tax_amount).round(1)
        if abs(total_amount - total_amount_calc) > 0.1:
            errors.append(
                f"[Row {idx}] Total Amount {total_amount}, Calculated Total Amount: {total_amount_calc}"
            )

    return errors


def verify_amounts_journal(ledgers_df: pd.DataFrame):
    errors: list[str] = []
    net_debit = ledgers_df["Debit Amount"].sum().round(1)
    net_credit = ledgers_df["Credit Amount"].sum().round(1)
    if abs(net_debit - net_credit) > 0.1:
        errors.append(f"Net Debit {net_debit}, Net Credit: {net_credit}")

    return errors


def verify_amounts(common_df: pd.DataFrame, items_df: pd.DataFrame):
    if is_journal_voucher(common_df):
        return verify_amounts_journal(items_df)
    else:
        return verify_amounts_sales_purchase(items_df)
