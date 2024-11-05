import pandas as pd


def verify_amounts(items_df: pd.DataFrame):
    errors: list[str] = []
    for idx, row in items_df.iterrows():
        rate = row["Rate"]
        discount = row["Discount"]
        quantity = row["Quantity"]
        taxable_amount = row["Taxable Amount"]
        taxable_amount_calc = rate * quantity - discount
        if abs(taxable_amount - taxable_amount_calc) > 0.01:
            errors.append(
                f"[Row {idx}] Taxable Amount {taxable_amount}, Calculated Taxable Amount: {taxable_amount_calc}"
            )

        tax_amount = row["Tax Amount"]
        tax_amount_calc = taxable_amount * row["Tax Rate"] / 100
        if abs(tax_amount - tax_amount_calc) > 0.01:
            errors.append(
                f"[Row {idx}] Tax Amount {tax_amount}, Calculated Tax Amount: {tax_amount_calc}"
            )

        total_amount = row["Total Amount"]
        total_amount_calc = taxable_amount + tax_amount
        if abs(total_amount - total_amount_calc) > 0.01:
            errors.append(
                f"[Row {idx}] Total Amount {total_amount}, Calculated Total Amount: {total_amount_calc}"
            )

    return errors
