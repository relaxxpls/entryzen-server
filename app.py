import streamlit as st
from src.verify_df import verify_amounts
from src.parse_pdf import parse_pdf, process_csv_string
from src.tally_connector import get_tally_company, match_masters
from src.tally.create_masters import create_masters
from src.tally.create_vouchers import create_vouchers

st.set_page_config(page_title="Tally Automation", page_icon=":ledger:", layout="wide")

# Initialize session state variables
if "is_exportable" not in st.session_state:
    st.session_state.is_exportable = False
if "common_df" not in st.session_state:
    st.session_state.common_df = None
if "items_df" not in st.session_state:
    st.session_state.items_df = None

col1, col2 = st.columns([4, 1], vertical_alignment="center")

DEBUG = True

# ? Display status of tally connection
status_placeholder = col1.empty()
company_name = None
with status_placeholder:
    try:
        with st.spinner("Processing... Please wait"):
            company_name = get_tally_company()
        st.success(f"Connected to Tally Company: '{company_name}'")

    except Exception:
        st.error(
            "Ensure Tally is running on your system and the correct company is selected. Then click the button below to connect."
        )

if col2.button("Reconnect", icon=":material/refresh:", use_container_width=True):
    status_placeholder.empty()
    st.rerun()

st.title("📤 Upload Invoice")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

supported_vouchers = ["Purchase", "Sales"]

msg_content = None
if DEBUG:
    msg_content = st.text_area("Enter Msg Content")

# ? If file is uploaded, parse the invoice
if company_name is not None and (uploaded_file is not None or msg_content is not None):
    if st.button("Parse Invoice"):
        with st.status("Loading...", expanded=True) as status:
            try:
                st.write("📖 Reading Invoice")
                if msg_content:
                    st.session_state.common_df, st.session_state.items_df = (
                        process_csv_string(msg_content)
                    )
                elif uploaded_file:
                    st.session_state.common_df, st.session_state.items_df = parse_pdf(
                        company_name, uploaded_file
                    )

                voucher_type = st.session_state.common_df["Voucher Type"].iloc[0]
                if voucher_type not in supported_vouchers:
                    raise Exception(
                        f"Detected Voucher Type: {voucher_type}. Supported Voucher Types: {supported_vouchers}"
                    )

                st.write("🔍 Matching Tally Masters")
                # ? Match units and other fields, updates in place
                match_masters(st.session_state.common_df, st.session_state.items_df)

                status.update(
                    label="✅ Invoice Parsed Successfully!",
                    state="complete",
                    expanded=False,
                )
                st.session_state.is_exportable = (
                    False  # Reset export flag when parsing new invoice
                )
            except Exception as e:
                print(e)
                status.update(
                    label="❌ Error parsing invoice", state="error", expanded=False
                )

    # Display the dataframes if they exist in session state
    if st.session_state.common_df is not None and st.session_state.items_df is not None:
        st.write("### Parsed Invoice Details")
        st.write("#### Invoice Summary:")
        st.session_state.common_df = st.data_editor(
            st.session_state.common_df, hide_index=True, key="common_df_editor"
        )

        st.write("#### Invoice Items:")
        st.session_state.items_df = st.data_editor(
            st.session_state.items_df,
            num_rows="dynamic",
            disabled=("Quantity Unit", "Product Name"),
            key="items_df_editor",
        )

        col1, col2 = st.columns([2, 1], gap="large")

        col1.write("#### Verify Amounts")
        errors = verify_amounts(st.session_state.items_df)

        if errors:
            col1.error("\n\n".join(errors))
            st.session_state.is_exportable = False
        else:
            col1.success("Amounts verified successfully!")
            st.session_state.is_exportable = True

        # display net total and net tax
        col2.write("#### Net Amounts")
        net_total = st.session_state.items_df["Total Amount"].sum().round(2)
        net_tax = st.session_state.items_df["Tax Amount"].sum().round(2)
        col2.write(f"##### Net Tax: {net_tax}")
        col2.write(f"##### Net Total: {net_total}")

    if st.session_state.is_exportable:
        if st.button(
            "Export", icon=":material/cloud_upload:", use_container_width=True
        ):
            with st.status("Loading...", expanded=True) as status:
                try:
                    st.write("📤 Creating Masters")
                    create_masters(
                        st.session_state.common_df, st.session_state.items_df
                    )

                    st.write("📤 Creating Voucher")
                    create_vouchers(
                        st.session_state.common_df, st.session_state.items_df
                    )
                    status.update(label="✅ Export Successful!", state="complete")
                except Exception as e:
                    print(e)
                    status.update(label="❌ Error exporting invoice", state="error")
