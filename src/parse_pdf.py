import pandas as pd
import pymupdf
from langchain_openai import ChatOpenAI
import dotenv
import io

dotenv.load_dotenv()


def is_journal_voucher(common_df: pd.DataFrame):
    return common_df["Voucher Type"].iloc[0] == "Journal"


def create_prompt(company_name: str, invoice_page: str):
    return f"""
You are an expert accounting system assistant specializing in Tally data entry automation for "{company_name}" company.
Your task is to analyze invoice text and prepare it for Tally import from the perspective of an accountant of "{company_name}".

First identify the Voucher Type using the guidelines below:
- If the invoice does not involve a sale or purchase of stock items or you are unsure, use "Journal" as the Voucher Type.
- Else create a Sales or Purchase entry from the perspective of "{company_name}". If the company name seems like the customer name, use "Purchase", else use "Sales".

Next, Output the invoice data in CSV format based on the Voucher Type:
If the invoice has a Voucher Type of "Sales" or "Purchase", output the following:
    Line 1: Column headers for the invoice data in this order:
        "Voucher Type","Customer Name","Customer Address","Customer State","Customer GSTIN","Supplier Name","Supplier Address","Supplier State","Supplier GSTIN","Document Number","Document Date","Narration"
    Line 2: Actual data for the journal entry, in the same order as the headers in Line 1.
    Line 3: Column headers for the invoice line items, in this order:
        "HSN Code","Product Name","Quantity","Quantity Unit","Rate","Currency","Discount","Taxable Amount","Tax Rate","Tax Amount","Total Amount"
    Line 4 and onwards: Actual data for each line item, in the same order as the headers in Line 3.

If the invoice has any other Voucher Type (e.g., Journal, Contra), output the following:
    Line 1: Contains column headers for the journal entry data, in the order:
        "Voucher Type","Voucher Date","Narration"
    Line 2: Actual data for the journal entry, in the same order as the headers in Line 1.
    Line 3: Contains column headers for the journal entry account details, in this order:
        "Account Name","Account Address","Account State","Account GSTIN","Account Group","Transaction Type","Debit Amount","Credit Amount"
    Line 4 and onwards: Actual data for each account, in the same order as the headers in Line 3.

Important Rules:

- Output no other information except for the csv data
- Tax Handling: For invoices with CGST/SGST, add them together to find the total tax rate (IGST).
- In the invoice text, each page data is separated by 3 new lines
- Data Formatting and Defaults:
    - The Voucher Type must be one of: "Sales", "Purchase", "Journal".
    - Wrap all comma-separated values in double quotes and escape existing double quotes within values with another double quote.
    - Ignore duplicate pages.
    - Remove commas from numeric values.
    - Use exact product names from the invoice.
    - Use defaults where data is missing: Quantity=1, Discount=0, Tax Rate=0, Tax Amount=0, Quantity Unit="Nos", Debit Amount=0, Credit Amount=0.
    - For missing fields, use an empty string, and format dates as %d/%m/%Y.
    - The Narration should be concise and include relevant details.
    - For decimal numbers, use a maximum of 2 decimal places.
- Journal Entry Rules:
    - Create separate account entries for each type of tax present.
    - Correctly identify Debt and Credit amounts based on the invoice data.
    - Ensure sum of Debit Amount equals sum of Credit Amount. If not, adjust the amounts accordingly. This is very important.
    - Assign Account Groups correctly and use concise, relevant Account Names based on the invoice.
    - Account Group must be one of the following: "Current Assets", "Current Liabilities", "Fixed Assets", "Indirect Expenses", "Investments", "Loans (Liability)", "Bank Accounts", "Cash-in-Hand", "Duties & Taxes", "Provisions", "Reserves & Surplus", "Secured Loans", "Stock-in-Hand", "Sundry Creditors", "Sundry Debtors", "Unsecured Loans".
    - For any Account Names not directly mentioned in the invoice, generate names based on using concise and relevant information.

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

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2, top_p=0.2)
    prompt = create_prompt(company_name, text)
    msg = llm.invoke(prompt)
    msg.pretty_print()
    print("ChatGPT Response Metadata:", msg.response_metadata)

    common_df, items_df = process_csv_string(msg.content)
    common_df["filename"] = pdf_file if is_file_path else pdf_file.name

    return common_df, items_df
