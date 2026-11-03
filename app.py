import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
import re

from pdf2image import convert_from_bytes

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

FED_EX_PATTERN = r"96\d{32}"


def extract_fedex_numbers(text):

    if not text:
        return []

    # OCR 결과 정리
    clean_text = re.sub(
        r"[^0-9A-Z]",
        "",
        text.upper()
    )

    return re.findall(
        FED_EX_PATTERN,
        clean_text
    )


if uploaded_files:

    progress = st.progress(0)

    for idx, file in enumerate(uploaded_files):

        try:

            numbers_found = set()

            # =====================
            # PDF 처리
            # =====================

            if file.name.lower().endswith(".pdf"):

                text = ""

                # 1차 : pdfplumber
                try:

                    file.seek(0)

                    with pdfplumber.open(file) as pdf:

                        for page in pdf.pages:

                            page_text = page.extract_text()

                            if page_text:
                                text += page_text + "\n"

                    matches = extract_fedex_numbers(text)

                    numbers_found.update(matches)

                except Exception as e:

                    st.warning(
                        f"{file.name} pdfplumber 실패: {e}"
                    )

                # 2차 : OCR
                if len(numbers_found) == 0:

                    try:

                        file.seek(0)

                        images = convert_from_bytes(
                            file.read(),
                            dpi=300
                        )

                        ocr_text = ""

                        for image in images:

                            page_text = pytesseract.image_to_string(
                                image,
                                config="--psm 6"
                            )

                            ocr_text += page_text

                        matches = extract_fedex_numbers(
                            ocr_text
                        )

                        numbers_found.update(matches)

                    except Exception as e:

                        st.warning(
                            f"{file.name} OCR 실패: {e}"
                        )

            # =====================
            # ZPL 처리
            # =====================

            else:

                file.seek(0)

                text = file.read().decode(
                    "utf-8",
                    errors="ignore"
                )

                matches = extract_fedex_numbers(
                    text
                )

                numbers_found.update(matches)

            # =====================
            # 결과 저장
            # =====================

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
                            sorted(numbers_found)
                        )
                    )
                else:
                    st.write(
                        "FedEx Tracking Number 미발견"
                    )

        except Exception as e:

            st.error(
                f"{file.name} 처리 실패: {str(e)}"
            )

        progress.progress(
            (idx + 1) / len(uploaded_files)
        )

    # =====================
    # 최종 결과
    # =====================

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
        ).encode("utf-8-sig")

        st.download_button(
            "CSV 다운로드",
            data=csv,
            file_name="tracking_numbers.csv",
            mime="text/csv"
        )

    else:

        st.warning(
            "추출된 Tracking Number가 없습니다."
        )
