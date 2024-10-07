import gradio as gr
import pandas as pd
from typing import Tuple, List
import pymupdf
from langchain_openai import ChatOpenAI
import dotenv


dotenv.load_dotenv()


def create_prompt(invoice_page: str):
    return f"""
You are a helpful assistant for automating data entry into an accounting system.
Given the text extracted from an invoice, you need to extract the following information:

for the invoice get the:
Customer name, Supplier name, document number, document date

for each good in the invoice, get the:
HSN code, Product Name / Recognized Product, Unit, Quantity, Price, Taxable Amount, Tax Rate, Tax, Total Amount

Keep the output format strictly as follows:
line 1 for invoice titles in csv format
line 2 for invoice data in csv format
line 3 for goods title in csv format
line 4 onwards for goods data in csv format
Output no other information.

Pages are seperated by 3 new lines.
If the invoice contains a duplicate page, ignore it.
If there are numbers which have a comma, remove the comma.

The invoice text is as follows:
{invoice_page}
"""


def process_csv_string(csv_string: str):
    # Remove the markdown code block syntax
    csv_string = csv_string.replace("```csv\n", "").replace("```", "")

    # Split the CSV string into lines
    lines = csv_string.strip().split("\n")

    # Process common data
    common_data = dict(zip(lines[0].split(","), lines[1].split(",")))
    common_df = pd.DataFrame([common_data])

    # Process item data
    item_header = lines[2].split(",")
    item_data = [line.split(",") for line in lines[3:]]
    item_df = pd.DataFrame(item_data, columns=item_header)

    return common_df, item_df


def process_invoice(pages: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    prompt = create_prompt("\n\n\n".join(pages))
    msg = llm.invoke(prompt)

    return process_csv_string(msg.content)


def process_pdf(pdf_file: str):
    if pdf_file is None:
        return pd.DataFrame(), pd.DataFrame()

    doc = pymupdf.open(pdf_file)
    pages = []
    for page in doc:
        text = page.get_text("text")
        pages.append(text)

    return process_invoice(pages)


iface = gr.Interface(
    fn=process_pdf,
    inputs=gr.File(label="Upload Invoice PDF"),
    outputs=[
        gr.Dataframe(label="Invoice Details"),
        gr.Dataframe(label="Invoice Items"),
    ],
    title="Invoice Processor",
    description="Upload a PDF invoice to extract common data and item details.",
)

# Launch the app
iface.launch(share=True)
