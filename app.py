# app.py
import streamlit as st
import pandas as pd
from parse_functions import parse_pdf

st.title("Invoice Upload and Selection")

# Initialize session state for the invoices list (X)
if "X" not in st.session_state:
    st.session_state.X = []

# PDF Upload
uploaded_file = st.file_uploader("Upload PDF Invoice", type="pdf")

if uploaded_file:
    # Parse PDF and add common data to X
    common_df, items_df = parse_pdf(uploaded_file)
    st.session_state.X.append((common_df, items_df))
    st.success("Invoice uploaded and parsed successfully.")

# Display list of uploaded invoices
st.header("List of Uploaded Invoices")
selected_invoice = st.selectbox(
    "Select an Invoice to View/Edit", options=range(len(st.session_state.X))
)

# Save the selected invoice index to session state and go to ViewInvoice page
if st.button("View/Edit Selected Invoice"):
    st.session_state.selected_invoice = selected_invoice
    st.write(
        "Go to the 'View Invoice' page in the sidebar to view/edit the selected invoice."
    )
