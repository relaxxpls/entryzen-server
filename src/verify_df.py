import pandas as pd

from .parse_pdf import is_journal_voucher


ROUND_DIGITS = 0
ROUND_ERROR = 1.01 * 10**-ROUND_DIGITS


def verify_amounts_sales_purchase(items_df: pd.DataFrame):
    errors: list[str] = []
    for idx, row in items_df.iterrows():
        rate = row["Rate"]
        discount = row["Discount"]
        quantity = row["Quantity"]
        taxable_amount = round(row["Taxable Amount"], ROUND_DIGITS)
        taxable_amount_calc = round(rate * quantity - discount, ROUND_DIGITS)
        if abs(taxable_amount - taxable_amount_calc) > ROUND_ERROR:
            errors.append(
                f"[Row {idx}] Taxable Amount {taxable_amount}, Calculated Taxable Amount: {taxable_amount_calc}"
            )

        tax_amount = round(row["Tax Amount"], ROUND_DIGITS)
        tax_amount_calc = round(taxable_amount * row["Tax Rate"] / 100, ROUND_DIGITS)
        if abs(tax_amount - tax_amount_calc) > ROUND_ERROR:
            errors.append(
                f"[Row {idx}] Tax Amount {tax_amount}, Calculated Tax Amount: {tax_amount_calc}"
            )

        total_amount = round(row["Total Amount"], ROUND_DIGITS)
        total_amount_calc = round(taxable_amount + tax_amount, ROUND_DIGITS)
        if abs(total_amount - total_amount_calc) > ROUND_ERROR:
            errors.append(
                f"[Row {idx}] Total Amount {total_amount}, Calculated Total Amount: {total_amount_calc}"
            )

    return errors


def verify_amounts_journal(ledgers_df: pd.DataFrame):
    errors: list[str] = []
    net_debit = round(ledgers_df["Debit Amount"].sum(), ROUND_DIGITS)
    net_credit = round(ledgers_df["Credit Amount"].sum(), ROUND_DIGITS)
    if abs(net_debit - net_credit) > ROUND_ERROR:
        errors.append(f"Net Debit {net_debit}, Net Credit: {net_credit}")

    return errors


def verify_amounts(common_df: pd.DataFrame, items_df: pd.DataFrame):
    if is_journal_voucher(common_df):
        return verify_amounts_journal(items_df)
    else:
        return verify_amounts_sales_purchase(items_df)
