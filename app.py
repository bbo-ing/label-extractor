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

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

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


def extract_tracking_from_pdf_filename(filename):

    match = re.search(
        r"_(\d{12})\.pdf$",
        filename,
        re.IGNORECASE
    )

    if not match:
        return None

    last12 = match.group(1)

    return (
        "962208043000093514410087"
        + last12
    )


# =====================================
# 상단 버튼
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

        # uploader 초기화
        st.session_state.uploader_key += 1

        st.rerun()

# =====================================
# 파일 수 표시
# =====================================

st.info(
    f"현재 업로드된 파일 수: {len(st.session_state.files)}개"
)

# =====================================
# 업로드
# =====================================

uploaded_files = st.file_uploader(
    "PDF 또는 ZPL 업로드",
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_files:

    added_count = 0
    duplicate_count = 0

    for file in uploaded_files:

        if file.name in st.session_state.files:

            duplicate_count += 1
            continue

        st.session_state.files[file.name] = (
            file.getvalue()
        )

        added_count += 1

    if added_count:

        st.success(
            f"✅ {added_count}개 파일 추가됨"
        )

    if duplicate_count:

        st.warning(
            f"⚠️ {duplicate_count}개 중복 파일 제외됨"
        )

# =====================================
# 파일 목록
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
# Tracking 추출
# =====================================

tracking_numbers = set()

for filename, file_bytes in st.session_state.files.items():

    numbers_found = set()

    try:

        # --------------------------------
        # PDF
        # --------------------------------

        if filename.lower().endswith(".pdf"):

            tracking = (
                extract_tracking_from_pdf_filename(
                    filename
                )
            )

            if tracking:

                numbers_found.add(
                    tracking
                )

        # --------------------------------
        # ZPL
        # --------------------------------

        else:

            text = file_bytes.decode(
                "utf-8",
                errors="ignore"
            )

            numbers_found.update(
                extract_tracking_from_zpl(
                    text
                )
            )

        tracking_numbers.update(
            numbers_found
        )

        # --------------------------------
        # Debug
        # --------------------------------

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
                            sorted(
                                numbers_found
                            )
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
# 결과 출력
# =====================================

if tracking_numbers:

    result = sorted(
        tracking_numbers
    )

    df = pd.DataFrame(
        {
            "Tracking Number": result
        }
    )

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
