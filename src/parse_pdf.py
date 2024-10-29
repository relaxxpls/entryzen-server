import pandas as pd
import pymupdf
from langchain_openai import ChatOpenAI
import dotenv
import io


dotenv.load_dotenv()


def create_prompt(invoice_page: str):
    return f"""
You are an expert accounting system assistant specializing in Tally data entry automation.
Your task is to analyze invoice text and prepare it for Tally import.
Extract the following information maintaining exact output format:

for the invoice get the:
Customer Name,Customer Address,Customer GSTIN,Supplier Name,Supplier Address,Supplier GSTIN,Document Number,Document Date

for each good in the invoice, get the:
HSN code, Product Name, Quantity, Quantity Unit, Rate, Discount, Taxable Amount, Tax Rate, Tax Amount, Total Amount

Important rules:
1. Keep the output format strictly as follows:
    line 1 for invoice titles in csv format
    line 2 for invoice data in csv format
    line 3 for goods title in csv format
    line 4 onwards for goods data in csv format
2. Output no other information.
3. Wrap comma separated values in double quotes and escape any double quotes in the values with another double quote.
4. Pages are seperated by 3 new lines.
5. Ignore duplicate pages
6. Remove any commas from numbers
7. Product Name should be the raw name from invoice
8. For decimal numbers, use maximum 2 decimal places
9. If tax rate is given as IGST, use that directly. If given as CGST/SGST, sum them up
10. For quantity use default value 1 if not given
11. For discount use default value 0 if not given
12. For tax rate use default value 0 if not given
13. For tax amount use default value 0 if not given
14. For quantity unit use default value "Nos" if not given
15. For other fields use default value empty string if not given

The invoice text is as follows:
{invoice_page}
"""


def process_csv_string(csv_string: str):
    """Split the CSV string into lines"""
    lines = csv_string.strip().split("\n")
    common_df = pd.read_csv(io.StringIO("\n".join(lines[:2])))
    item_df = pd.read_csv(io.StringIO("\n".join(lines[2:])))

    return common_df, item_df


def parse_pdf(pdf_file: str):
    pages = pymupdf.get_text(pdf_file)
    text = "\n\n\n".join(pages)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    prompt = create_prompt(text)
    msg = llm.invoke(prompt)

    return process_csv_string(msg.content)
