# Link to dataset https://www.kaggle.com/datasets/apoorvwatsky/bank-transaction-data

# Import necessary libraries
import streamlit as st  # Streamlit for creating a web-based dashboard
import pandas as pd  # Pandas for data manipulation
import sqlite3  # SQLite3 for database connectivity
import plotly.express as px  # Plotly for interactive visualizations

# Set Streamlit page configuration
st.set_page_config(page_title="Transactions Dashboard", layout="wide")

# Display the main title of the dashboard
st.title("💰 Transactions Dashboard")

# Display a brief description below the title
st.markdown("### 📊 Analyze financial transactions with adaptable insights.")

# Sidebar section for file upload
st.sidebar.header("📂 Upload Transactions File")

# Allow users to upload a CSV or Excel file
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xls", "xlsx"])

# Check if a file is uploaded; if yes, read the file into a DataFrame
if uploaded_file:
    file_extension = uploaded_file.name.split(".")[-1]  # Extract file extension
    if file_extension == "csv":
        df = pd.read_csv(uploaded_file)  # Read CSV file
    else:
        df = pd.read_excel(uploaded_file)  # Read Excel file

    st.sidebar.success("✅ File uploaded successfully!")  # Display success message
else:
    # If no file is uploaded, load data from the SQLite database
    conn = sqlite3.connect("bank_transactions.db")  # Connect to the database
    df = pd.read_sql("SELECT * FROM transactions", conn)  # Load transactions table into a DataFrame
    conn.close()  # Close the database connection

# Automatically detect column types
df.columns = [col.strip().upper() for col in df.columns]  # Normalize column names

# Identify date columns
date_columns = [col for col in df.columns if "DATE" in col or "TIME" in col]
numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

# Convert detected date columns to datetime format
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# Sidebar filters (dynamic)
st.sidebar.header("🔍 Filter Transactions")

# Select date column for filtering
if date_columns:
    selected_date_col = st.sidebar.selectbox("Select Date Column", date_columns)
    start_date = st.sidebar.date_input("Start Date", df[selected_date_col].min())
    end_date = st.sidebar.date_input("End Date", df[selected_date_col].max())
    df_filtered = df[(df[selected_date_col] >= pd.to_datetime(start_date)) & (df[selected_date_col] <= pd.to_datetime(end_date))]
else:
    df_filtered = df.copy()

# Search box for filtering transactions by keywords
search_query = st.sidebar.text_input("Search Transaction Details")

# If search query is entered, filter transactions that contain the keyword
if search_query:
    text_columns = df_filtered.select_dtypes(include=["object"]).columns.tolist()
    if text_columns:
        df_filtered = df_filtered[df_filtered[text_columns].apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False)).any(axis=1)]

# Display the filtered transactions in a table
st.subheader("📋 Filtered Transactions" if uploaded_file else "📋 All Transactions")
st.dataframe(df_filtered)  # Show the DataFrame in Streamlit

# Transaction Summary section
st.subheader("📊 Transaction Summary")

# Choose numeric columns for analysis
if numeric_columns:
    selected_deposit_col = st.selectbox("Select Deposit Column", numeric_columns, index=0)
    selected_withdrawal_col = st.selectbox("Select Withdrawal Column", numeric_columns, index=1)
    selected_balance_col = st.selectbox("Select Balance Column", numeric_columns, index=2 if len(numeric_columns) > 2 else 1)

    col1, col2, col3 = st.columns(3)

    with col1:
        total_deposits = df_filtered[selected_deposit_col].sum()  # Calculate total deposits
        st.metric(label="Total Deposits", value=f"₦{total_deposits:,.2f}")  # Display total deposits

    with col2:
        total_withdrawals = df_filtered[selected_withdrawal_col].sum()  # Calculate total withdrawals
        st.metric(label="Total Withdrawals", value=f"₦{total_withdrawals:,.2f}")  # Display total withdrawals

    with col3:
        # Get the last available balance amount (if data exists)
        total_balance = df_filtered[selected_balance_col].iloc[-1] if not df_filtered.empty else 0
        st.metric(label="Current Balance", value=f"₦{total_balance:,.2f}")  # Display current balance

    # Pie Chart for Deposit vs Withdrawal Distribution
    st.subheader("📊 Deposit vs Withdrawal Distribution")

    # Create a pie chart using Plotly
    fig_pie = px.pie(
        names=["Deposits", "Withdrawals"],  # Labels for the pie chart
        values=[total_deposits, total_withdrawals],  # Corresponding values
        title="Deposit vs Withdrawal Breakdown",  # Title of the pie chart
        color_discrete_sequence=["green", "red"]  # Assign colors to deposits and withdrawals
    )
    st.plotly_chart(fig_pie)  # Display the pie chart in Streamlit

    # Monthly Transactions Chart
    st.subheader("📈 Transactions Over Time")

    if date_columns:
        # Create a new column for Month-Year (e.g., "2024-03")
        df_filtered["Month-Year"] = df_filtered[selected_date_col].dt.to_period("M").astype(str)

        # Group transactions by Month-Year and calculate sum of deposits and withdrawals
        monthly_data = df_filtered.groupby("Month-Year")[[selected_deposit_col, selected_withdrawal_col]].sum().reset_index()

        # Create a line chart for transaction trends over time
        fig_line = px.line(
            monthly_data,
            x="Month-Year",  # X-axis: Month-Year
            y=[selected_deposit_col, selected_withdrawal_col],  # Y-axis: Deposit and Withdrawal Amounts
            markers=True,  # Add markers to data points
            title="Monthly Transaction Trends",  # Title of the chart
            labels={"value": "Amount (₦)", "Month-Year": "Month"},  # Label formatting
        )
        st.plotly_chart(fig_line)  # Display the line chart in Streamlit

    # Filter Transactions by Type (Deposit or Withdrawal)
    st.subheader("🔍 Filter by Transaction Type")

    # Determine Transaction Type dynamically
    df_filtered["Transaction Type"] = df_filtered.apply(
        lambda row: "Deposit" if row[selected_deposit_col] > 0 else "Withdrawal", axis=1
    )

    # Radio button selection for transaction type
    transaction_type = st.radio("Select Transaction Type:", ("All", "Deposit", "Withdrawal"))

    # Apply filtering based on transaction type selection
    if transaction_type != "All":
        df_filtered = df_filtered[df_filtered["Transaction Type"] == transaction_type]

    # Display the filtered transactions again after transaction type filtering
    st.dataframe(df_filtered)

else:
    st.warning("⚠️ No numeric columns detected for analysis. Please upload a valid dataset.")

# Footer message
st.markdown("🚀 Powered by Streamlit & SQLite")
