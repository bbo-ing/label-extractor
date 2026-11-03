import streamlit as st
import pandas as pd
import re
import pdfplumber

st.title("Label Tracking Extractor")

numbers = []

files = st.file_uploader(
    "PDF 또는 ZPL 업로드",
    accept_multiple_files=True
)

if files:

    for file in files:

        text = ""

        try:

            if file.name.lower().endswith(".pdf"):

                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""

                # PDF에서 실제 추출된 텍스트 확인
                with st.expander(f"PDF Debug: {file.name}"):
                    st.text(text[:5000])

            else:

                text = file.read().decode(
                    "utf-8",
                    errors="ignore"
                )

            patterns = [
                r"96\d{32}",      # FedEx 34자리
                r"\b\d{12}\b",    # 12자리 추적번호
                r"1Z[0-9A-Z]+"    # UPS
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text)
                numbers.extend(matches)

        except Exception as e:
            st.error(f"{file.name}: {e}")

    numbers = sorted(set(numbers))

    if numbers:

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

    else:

        st.warning(
            "추출된 Tracking Number가 없습니다."
        )
