import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Label Tracking Extractor")

st.title("Label Tracking Extractor")

numbers = set()

files = st.file_uploader(
    "PDF 또는 ZPL 업로드",
    accept_multiple_files=True,
)

if files:

    progress = st.progress(0)

    for idx, file in enumerate(files):

        try:

            text = ""

            # =========================
            # PDF 처리
            # =========================
            if file.name.lower().endswith(".pdf"):

                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

            # =========================
            # ZPL 처리
            # =========================
            else:

                text = file.read().decode(
                    "utf-8",
                    errors="ignore"
                )

            # -------------------------
            # 파일명에서도 추출
            # -------------------------
            filename_matches = re.findall(
                r"96\d{32}",
                file.name
            )

            numbers.update(filename_matches)

            # -------------------------
            # 원본 텍스트 보존
            # -------------------------
            original_text = text

            # -------------------------
            # 공백 제거 버전 생성
            # PDF에서 숫자가 띄어져 있는 경우 대응
            # -------------------------
            compact_text = re.sub(
                r"[\s\-\(\)]",
                "",
                text
            )

            # =========================
            # FedEx 34자리 추출
            # =========================

            fedex_matches = re.findall(
                r"96\d{32}",
                compact_text
            )

            numbers.update(fedex_matches)

            # =========================
            # ZPL 바코드 라인 전용
            # 예:
            # >;9622085030000935144100879358833404
            # =========================

            zpl_matches = re.findall(
                r">;?(96\d{32})",
                compact_text
            )

            numbers.update(zpl_matches)

            # =========================
            # 디버그
            # =========================

            with st.expander(
                f"Debug - {file.name}"
            ):
                st.write(
                    f"추출 건수: {len(fedex_matches) + len(zpl_matches)}"
                )

                if fedex_matches:
                    st.write("FedEx Matches:")
                    st.write(fedex_matches)

            progress.progress(
                (idx + 1) / len(files)
            )

        except Exception as e:

            st.error(
                f"{file.name}: {str(e)}"
            )

    # ====================================
    # 결과 출력
    # ====================================

    result = sorted(numbers)

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
            csv,
            file_name="tracking_numbers.csv",
            mime="text/csv"
        )

    else:

        st.warning(
            "추출된 Tracking Number가 없습니다."
        )
