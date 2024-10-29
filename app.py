import streamlit as st
import pandas as pd
import base64
from parse_tally_masters import parse_tally_masters
from parse_pdf import parse_pdf


def load_css():
    st.markdown(
        """
        <style>
        .stButton>button {
            width: 100%;
        }
        .edit-table td input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


def extract_invoice_items(pdf_file):
    """
    Placeholder function to extract items from PDF invoice
    Returns: DataFrame with invoice items
    """
    # Add your PDF extraction logic here
    # This is a sample return
    return pd.DataFrame(
        {
            "Item": ["Sample Item 1", "Sample Item 2"],
            "Quantity": [1, 2],
            "Rate": [100, 200],
            "Amount": [100, 400],
        }
    )


def export_to_tally(df):
    """
    Placeholder function to export data to Tally
    """
    # Add your Tally export logic here
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
    <ENVELOPE>
        <!-- Add your Tally XML structure here -->
    </ENVELOPE>
    """
    return xml_content


def main():
    st.set_page_config(page_title="Invoice to Tally", layout="wide")
    load_css()

    if "masters_data" not in st.session_state:
        st.session_state.masters_data = None
    if "current_pdf" not in st.session_state:
        st.session_state.current_pdf = None
    if "invoice_data" not in st.session_state:
        st.session_state.invoice_data = {}

    st.title("Invoice PDF to Tally Integration")

    tab1, tab2 = st.tabs(["Import Masters", "Process Invoices"])

    with tab1:
        st.header("Import Tally Masters")
        st.markdown(
            """
        ### How to export masters from Tally:
        1. Open Tally
        2. Go to Export > Data > Masters
        3. Select the following options:
           - Export format: XML
           - Select masters: Stock Items
        4. Save the XML file
        5. Upload the saved XML file below
        """
        )

        masters_file = st.file_uploader("Upload Tally Masters XML", type=["xml"])
        if masters_file and st.button("Load Masters"):
            st.session_state.masters_data = parse_tally_masters(masters_file)
            st.success("Masters loaded successfully!")
            st.dataframe(st.session_state.masters_data)

    with tab2:
        st.header("Process Invoice PDFs")

        # PDF upload section
        uploaded_files = st.file_uploader(
            "Upload Invoice PDFs", type=["pdf"], accept_multiple_files=True
        )

        if uploaded_files:
            for pdf in uploaded_files:
                if st.button(f"Process {pdf.name}"):
                    st.session_state.current_pdf = pdf.name
                    if pdf.name not in st.session_state.invoice_data:
                        st.session_state.invoice_data[pdf.name] = extract_invoice_items(
                            pdf, st.session_state.masters_data
                        )

        # Display and edit invoice data
        if st.session_state.current_pdf:
            st.subheader(f"Invoice: {st.session_state.current_pdf}")

            df = st.session_state.invoice_data[st.session_state.current_pdf]

            # Create an editable dataframe
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Item": st.column_config.TextColumn("Item"),
                    "Quantity": st.column_config.NumberColumn("Quantity"),
                    "Rate": st.column_config.NumberColumn("Rate"),
                    "Amount": st.column_config.NumberColumn("Amount"),
                },
            )

            # Update the stored data
            st.session_state.invoice_data[st.session_state.current_pdf] = edited_df

            if st.button("Export to Tally"):
                try:
                    xml_content = export_to_tally(edited_df)
                    # Create download button for XML
                    b64 = base64.b64encode(xml_content.encode()).decode()
                    href = f'<a href="data:application/xml;base64,{b64}" download="tally_export.xml">Download Tally XML</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("Export successful! Click the link above to download.")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")


if __name__ == "__main__":
    main()
