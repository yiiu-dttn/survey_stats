import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
from api.database import get_surveys, get_survey_details, get_survey_answers
from services.survey_processor import process_survey_data

def main():
    st.set_page_config(page_title="Thống kê khảo sát", layout="wide")

    if 'survey_id' not in st.session_state:
        st.title("Chọn khảo sát")
        surveys = get_surveys()
        survey_options = {s[1]: s[0] for s in surveys}

        selected_survey = st.selectbox("Chọn tên khảo sát", list(survey_options.keys()))
        if st.button("Xem thống kê"):
            st.session_state.survey_id = survey_options[selected_survey]
            st.rerun()

    else:
        survey_id = st.session_state.survey_id
        survey_details, stats, text_answers = process_survey_data(survey_id, get_survey_details, get_survey_answers)

        st.title(f"Thống kê khảo sát: {survey_details['title']}")

        st.subheader("Thông tin chung")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cơ sở đào tạo", survey_details['facility_name'])
        with col2:
            st.metric("Số phiếu phát ra", survey_details['total_answers'])
        with col3:
            st.metric("Số phiếu thu vào", survey_details['valid_answers'])

        # Hiển thị thống kê câu hỏi lựa chọn
        st.subheader("Thống kê khảo sát")
        for question_type, group_data in stats.items():
            for i, (options, group_stats) in enumerate(group_data.items(), 1):
                column_defs = [
                    {"headerName": "STT", "field": "STT", "width": 60, "pinned": "center"},
                    {
                        "headerName": "Câu hỏi",
                        "field": "Câu hỏi",
                        "wrapText": True,
                        "autoHeight": True,
                        "minWidth": 400,
                        "flex": 1
                    }
                ]

                for opt in options:
                    column_defs.append({
                        "headerName": opt,
                        "children": [
                            {"headerName": "Số lượng", "field": f"{opt}_count", "width": 90},
                            {"headerName": "Tỷ lệ", "field": f"{opt}_percent", "width": 90}
                        ]
                    })

                table_data = []
                for j, stat in enumerate(group_stats, 1):
                    row = {"STT": j, "Câu hỏi": stat['question']}
                    for opt in options:
                        row[f"{opt}_count"] = stat['option_counts'][opt]
                        row[f"{opt}_percent"] = f"{stat['percentages'][opt]:.2f}%"
                    table_data.append(row)

                df = pd.DataFrame(table_data)

                # Tính tổng width để không bị tràn
                total_width = 600 + len(options) * 180 + 100  # 600 cho cột câu hỏi, 180 mỗi option group, + extra
                grid_height = min(400 + len(df) * 35, 800)

                AgGrid(
                    df,
                    gridOptions={
                        "columnDefs": column_defs,
                        "defaultColDef": {
                            "wrapText": True,
                            "autoHeight": True,
                            "resizable": True
                        },
                        "domLayout": "normal"
                    },
                    height=grid_height,
                    fit_columns_on_grid_load=False,
                    theme="material"
                )

        # Hiển thị câu trả lời tự luận
        if text_answers:
            for question_id, question_data in text_answers.items():
                st.write(f"**Câu hỏi: {question_data['question']}**")
                df_text = pd.DataFrame(
                    [[i + 1, answer] for i, answer in enumerate(question_data['answers'])],
                    columns=['STT', 'Câu trả lời']
                ).reset_index(drop=True)

                AgGrid(
                    df_text,
                    gridOptions={
                        "columnDefs": [
                            {"headerName": "STT", "field": "STT", "width": 50, "pinned": "center"},
                            {"headerName": "Câu trả lời", "field": "Câu trả lời", "wrapText": True, "autoHeight": True, "minWidth": 400}
                        ],
                        "defaultColDef": {
                            "wrapText": True,
                            "autoHeight": True,
                            "resizable": True
                        },
                        "domLayout": "normal"
                    },
                    height=min(400 + len(df_text) * 32, 800),
                    fit_columns_on_grid_load=True,
                    theme="material"
                )

        if st.button("Quay lại chọn khảo sát"):
            del st.session_state.survey_id
            st.rerun()

if __name__ == "__main__":
    main()
