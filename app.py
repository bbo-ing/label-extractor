import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="FedEx Tracking Extractor",
    layout="wide"
)

st.title("FedEx Tracking Extractor")

# =====================================
# Session State 초기화
# =====================================

if "files" not in st.session_state:
    st.session_state.files = {}

if "tracking_numbers" not in st.session_state:
    st.session_state.tracking_numbers = set()

# =====================================
# 함수
# =====================================

def extract_tracking_from_zpl(text):

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


# =====================================
# 상단 메뉴
# =====================================

col1, col2 = st.columns([1, 1])

with col1:

    show_debug = st.checkbox(
        "Debug 보기",
        value=False
    )

with col2:

    if st.button("전체 초기화"):

        st.session_state.files = {}
        st.session_state.tracking_numbers = set()

        st.rerun()

# =====================================
# 현재 파일 수
# =====================================

st.info(
    f"현재 업로드된 파일 수: {len(st.session_state.files)}개"
)

# =====================================
# 파일 업로드
# =====================================

uploaded_files = st.file_uploader(
    "PDF 또는 ZPL 업로드",
    accept_multiple_files=True
)

if uploaded_files:

    added_count = 0
    duplicate_count = 0

    for file in uploaded_files:

        if file.name in st.session_state.files:

            duplicate_count += 1
            continue

        file_bytes = file.getvalue()

        st.session_state.files[file.name] = {
            "name": file.name,
            "bytes": file_bytes
        }

        added_count += 1

    if added_count > 0:

        st.success(
            f"{added_count}개 파일 추가됨"
        )

    if duplicate_count > 0:

        st.warning(
            f"{duplicate_count}개 중복 파일 제외됨"
        )

# =====================================
# 현재 파일 목록
# =====================================

if st.session_state.files:

    with st.expander(
        f"업로드된 파일 목록 ({len(st.session_state.files)}개)"
    ):

        for filename in sorted(
            st.session_state.files.keys()
        ):

            st.write(filename)

# =====================================
# 파일 처리
# =====================================

tracking_numbers = set()

for filename, file_data in st.session_state.files.items():

    numbers_found = set()

    try:

        # ------------------------------
        # PDF
        # ------------------------------

        if filename.lower().endswith(".pdf"):

            # PDF 파일명 마지막 12자리 추출
            match = re.search(
                r"_(\d{12})\.pdf$",
                filename,
                re.IGNORECASE
            )

            if match:

                last12 = match.group(1)

                tracking_number = (
                    "962208043000093514410087"
                    + last12
                )

                numbers_found.add(
                    tracking_number
                )

        # ------------------------------
        # ZPL
        # ------------------------------

        else:

            try:

                text = file_data["bytes"].decode(
                    "utf-8",
                    errors="ignore"
                )

                numbers_found.update(
                    extract_tracking_from_zpl(text)
                )

            except Exception:
                pass

        tracking_numbers.update(
            numbers_found
        )

        # ------------------------------
        # Debug
        # ------------------------------

        if show_debug:

            with st.expander(
                f"Debug - {filename}"
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
                        "Tracking Number 미발견"
                    )

    except Exception as e:

        st.error(
            f"{filename}: {e}"
        )

# =====================================
# 결과
# =====================================

if tracking_numbers:

    result = sorted(
        tracking_numbers
    )

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
        label="CSV 다운로드",
        data=csv,
        file_name="tracking_numbers.csv",
        mime="text/csv"
    )
