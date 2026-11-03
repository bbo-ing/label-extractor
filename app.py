import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(
    page_title="Label Tracking Extractor",
    layout="wide"
)

st.title("Label Tracking Extractor")

uploaded_files = st.file_uploader(
    "PDF 또는 ZPL 업로드",
    accept_multiple_files=True
)

tracking_numbers = set()


def extract_from_zpl(text):

    matches = set()

    patterns = [

        r">;?(96\d{32})",

        r"31Z(96\d{32})",

        r"\b(96\d{32})\b"
    ]

    for pattern in patterns:

        found = re.findall(
            pattern,
            text
        )

        matches.update(found)

    return matches


if uploaded_files:

    progress = st.progress(0)

    for idx, file in enumerate(uploaded_files):

        try:

            text = ""
            numbers_found = set()

            is_pdf = file.name.lower().endswith(
                ".pdf"
            )

            # =====================
            # PDF
            # =====================

            if is_pdf:

                with pdfplumber.open(
                    file
                ) as pdf:

                    for page in pdf.pages:

                        page_text = page.extract_text()

                        if page_text:

                            text += page_text
                            text += "\n"

            # =====================
            # ZPL
            # =====================

            else:

                text = file.read().decode(
                    "utf-8",
                    errors="ignore"
                )

                numbers_found.update(
                    extract_from_zpl(text)
                )

            tracking_numbers.update(
                numbers_found
            )

            with st.expander(
                f"Debug - {file.name}"
            ):

                st.write(
                    f"추출 건수: {len(numbers_found)}"
                )

                if numbers_found:

                    st.code(
                        "\n".join(
                            sorted(
                                numbers_found
                            )
                        )
                    )

                else:

                    st.write(
                        "FedEx Tracking Number 미발견"
                    )

                st.markdown("---")

                st.write(
                    "PDF/ZPL 원본 추출 텍스트"
                )

                st.code(
                    text[:3000]
                )

        except Exception as e:

            st.error(
                f"{file.name}: {e}"
            )

        progress.progress(
            (idx + 1)
            / len(uploaded_files)
        )

    result = sorted(
        tracking_numbers
    )

    if result:

        df = pd.DataFrame({
            "Tracking Number": result
        })

        st.success(
            f"{len(result)}개 Tracking Number 추출 완료"
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        csv = df.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

        st.download_button(
            "CSV 다운로드",
            csv,
            file_name="tracking_numbers.csv",
            mime="text/csv"
        )

    else:

        st.warning(
            "추출된 Tracking Number가 없습니다."
        )
