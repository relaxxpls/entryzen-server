import pandas as pd
import pymupdf
from langchain_openai import ChatOpenAI
import dotenv
import io

dotenv.load_dotenv()


def create_prompt(company_name: str, invoice_page: str):
    return f"""
You are an expert accounting system assistant specializing in Tally data entry automation for "{company_name}" company.
Your task is to analyze invoice text and prepare it for Tally import.

If the invoice has a Voucher Type of "Sales" or "Purchase":
    The output should have the following format:
        Line 1: Contains column headers for the invoice data, in the order:
            "Voucher Type","Customer Name","Customer Address","Customer State","Customer GSTIN","Supplier Name","Supplier Address","Supplier State","Supplier GSTIN","Document Number","Document Date","Narration"
        Line 2: Contains the actual data for the invoice, in the same order as the headers in Line 1.
        Line 3: Contains column headers for the invoice line items, in the order:
            "HSN Code","Product Name","Quantity","Quantity Unit","Rate","Currency","Discount","Taxable Amount","Tax Rate","Tax Amount","Total Amount"
        Line 4 and onwards: Contains the actual data for each line item, in the same order as the headers in Line 3.

If the invoice has any other Voucher Type (e.g., Journal, Contra):
    The output should have the following format:
        Line 1: Contains column headers for the journal entry data, in the order:
            "Voucher Type","Voucher Date","Narration"
        Line 2: Contains the actual data for the journal entry, in the same order as the headers in Line 1.
        Line 3: Contains column headers for the journal entry account details, in the order:
            "Account Name","Account Address","Account State","Account GSTIN","Account Group","Transaction Type","Debit Amount","Credit Amount"
        Line 4 and onwards: Contains the actual data for each account, in the same order as the headers in Line 3.

Important rules:

* Output no other information except for the csv data
* Prefer Journal entries for non-Sales/Purchase Invoices
* If voucher type is Journal, create seperate accounts for different types of taxes present
* Wrap all comma-separated values in double quotes and escape any existing double quotes within the values with another double quote.
* In invoice text, each page data is separated by 3 new lines
* Ignore any duplicate pages.
* Remove any commas from numeric values.
* Use the exact product name from the invoice.
* For decimal numbers, use a maximum of 2 decimal places.
* If the tax rate is given as IGST, use that directly. If given as CGST/SGST, sum them up.
* If the quantity is not given, use a default value of 1.
* If the discount is not given, use a default value of 0.
* If the tax rate is not given, use a default value of 0.
* If the tax amount is not given, use a default value of 0.
* If the quantity unit is not given, use a default value of "Nos".
* If any other field is not given, use a default value of an empty string.
* The Voucher Type must be one of: "Sales", "Purchase", "Receipt", "Payment", "Journal", "Contra".
* The Narration should be concise and include relevant details.
* Use the date format "%d/%m/%Y" for any dates.
* For the Transaction Type, use either "Debit" or "Credit".
* If the Debit Amount or Credit Amount is not given, use a default value of 0.
* The Account Group must be one of the following: "Current Assets", "Current Liabilities", "Fixed Assets", "Indirect Expenses", "Investments", "Loans (Liability)", "Bank Accounts", "Cash-in-Hand", "Duties & Taxes", "Provisions", "Reserves & Surplus", "Secured Loans", "Stock-in-Hand", "Sundry Creditors", "Sundry Debtors", "Unsecured Loans".
* For any Account Names not directly mentioned in the invoice, generate names based on using concise and relevant information.

The invoice text is as follows:
{invoice_page}
"""


def process_csv_string(csv_string: str):
    """Split the CSV string into lines"""
    lines = csv_string.strip().split("\n")
    if csv_string.startswith("```"):
        lines = lines[1:-1]

    common_df = pd.read_csv(io.StringIO("\n".join(lines[:2])))
    item_df = pd.read_csv(io.StringIO("\n".join(lines[2:])))

    return common_df, item_df


def parse_pdf(company_name: str, pdf_file: io.BytesIO | str):
    is_file_path = isinstance(pdf_file, str)
    if is_file_path:
        pages = pymupdf.get_text(pdf_file)
    else:
        with pymupdf.open(stream=pdf_file.read()) as doc:
            pages = [page.get_text() for page in doc]
    text = "\n\n\n".join(pages)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    prompt = create_prompt(company_name, text)
    msg = llm.invoke(prompt)
    msg.pretty_print()
    print("ChatGPT Response Metadata:", msg.response_metadata)

    common_df, items_df = process_csv_string(msg.content)
    common_df["filename"] = pdf_file if is_file_path else pdf_file.name

    return common_df, items_df
