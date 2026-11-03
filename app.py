import streamlit as st
import pandas as pd
import fitz
import re

from PIL import Image
from pyzbar.pyzbar import decode

st.set_page_config(
    page_title="FedEx Tracking Extractor"
)

st.title("FedEx Tracking Extractor")

files = st.file_uploader(
    "PDF 또는 ZPL 업로드",
    accept_multiple_files=True
)

results = set()


def extract_zpl(text):

    matches = set()

    patterns = [

        r">;?(96\d{32})",

        r"31Z(96\d{32})",

        r"\b(96\d{32})\b",
    ]

    for pattern in patterns:

        found = re.findall(
            pattern,
            text
        )

        matches.update(found)

    return matches


def extract_pdf_barcodes(pdf_bytes):

    found = set()

    doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    for page in doc:

        pix = page.get_pixmap(
            matrix=fitz.Matrix(
                4,
                4
            )
        )

        img = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        decoded = decode(img)

        for barcode in decoded:

            try:

                data = barcode.data.decode(
                    "utf-8"
                )

                fedex = re.findall(
                    r"96\d{32}",
                    data
                )

                found.update(fedex)

            except:
                pass

    return found


if files:

    progress = st.progress(0)

    for i, file in enumerate(files):

        found = set()

        try:

            if file.name.lower().endswith(
                ".pdf"
            ):

                pdf_bytes = file.read()

                found.update(
                    extract_pdf_barcodes(
                        pdf_bytes
                    )
                )

            else:

                text = file.read().decode(
                    "utf-8",
                    errors="ignore"
                )

                found.update(
                    extract_zpl(text)
                )

            results.update(found)

            with st.expander(
                f"Debug - {file.name}"
            ):

                st.write(
                    f"추출 건수: {len(found)}"
                )

                if found:

                    st.code(
                        "\n".join(
                            sorted(found)
                        )
                    )

                else:

                    st.write(
                        "Tracking Number 미발견"
                    )

        except Exception as e:

            st.error(
                f"{file.name}: {e}"
            )

        progress.progress(
            (i + 1) / len(files)
        )

    if results:

        df = pd.DataFrame({
            "Tracking Number":
            sorted(results)
        })

        st.success(
            f"{len(df)}개 추출 완료"
        )

        st.dataframe(df)

        st.download_button(
            "CSV 다운로드",
            df.to_csv(
                index=False
            ).encode("utf-8-sig"),
            "tracking_numbers.csv",
            "text/csv"
        )

    else:

        st.warning(
            "추출된 Tracking Number가 없습니다."
        )
