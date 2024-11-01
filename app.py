import streamlit as st
from src.parse_pdf import parse_pdf
from src.tally_connector import (
    get_tally_company,
    match_masters,
    create_masters,
    create_voucher,
)


# ? Display status of tally connection
status_placeholder = st.empty()
company_name = None
with status_placeholder:
    try:
        with st.spinner("Processing... Please wait"):
            company_name = get_tally_company()
        st.success(f"Connected to Tally Company: {company_name}")

    except Exception:
        st.error(
            "Ensure Tally is running on your system and the correct company is selected. Then click the button below to connect."
        )

if st.button("Reconnect"):
    status_placeholder.empty()
    st.rerun()

st.title("📤 Upload Invoice")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type="pdf",
    help="Upload a PDF invoice to parse and process",
)

supported_vouchers = ["Purchase", "Sales"]

# ? If file is uploaded, parse the invoice
if uploaded_file is not None and company_name is not None:
    is_exportable = False

    if st.button("Parse Invoice"):
        with st.status("Loading...", expanded=True) as status:
            try:
                st.write("📖 Reading Invoice")
                common_df, items_df = parse_pdf(company_name, uploaded_file)
                voucher_type = common_df["Voucher Type"].iloc[0]
                if voucher_type not in supported_vouchers:
                    st.error(
                        f"Detected Voucher Type: {voucher_type}. Supported Voucher Types: {supported_vouchers}"
                    )

                st.write("🔍 Matching Tally Masters")
                common_df, items_df = match_masters(common_df, items_df)

                status.update("✅ Invoice Parsed Successfully!", state="complete")

                st.write("### Parsed Invoice Details")
                st.write("#### Invoice Summary:")
                common_df_edited = st.data_editor(common_df, hide_index=True)

                st.write("#### Invoice Items:")
                items_df_edited = st.data_editor(items_df, num_rows="dynamic")

                is_exportable = True

            except Exception as e:
                print(e)
                status.update("❌ Error Parsing Invoice", state="error")

    if is_exportable:
        if st.button("Export"):
            with st.status("Loading...", expanded=True) as status:
                try:
                    st.write("📤 Creating Masters")
                    create_masters(common_df_edited, items_df_edited)

                    st.write("📤 Creating Voucher")
                    create_voucher(common_df_edited, items_df_edited)
                except Exception as e:
                    print(e)
                    status.update("❌ Error exporting invoice", state="error")
