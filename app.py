import streamlit as st
import pandas as pd
import re
import pdfplumber

numbers = []

st.title("Label Tracking Extractor")

files = st.file_uploader(
    "PDF 또는 ZPL 업로드",
    accept_multiple_files=True
)

if files:

    for file in files:

        text = ""

        if file.name.lower().endswith(".pdf"):

            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

        else:
            text = file.read().decode(
                "utf-8",
                errors="ignore"
            )

        matches = re.findall(r"96\d{32}", text)

        numbers.extend(matches)

    numbers = sorted(set(numbers))

    df = pd.DataFrame(
        {"Tracking Number": numbers}
    )

    st.dataframe(df)

    csv = df.to_csv(index=False)

    st.download_button(
        "CSV 다운로드",
        csv,
        file_name="tracking_numbers.csv"
    )
