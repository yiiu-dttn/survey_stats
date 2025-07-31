import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
from api.database import get_surveys, get_survey_details, get_survey_answers
from services.survey_processor import process_survey_data

def main():
    st.set_page_config(page_title="Thống kê khảo sát", layout="wide")

    # ==== Giao diện tùy chỉnh ====
    st.markdown("""
        <style>
            html, body, [class*="css"] {
                font-family: 'Segoe UI', sans-serif;
                background-color: #f8f9fa;
                color: #1f2937;
            }
            .stTitle h1 {
                color: #2c3e50;
                font-weight: 800;
            }
            h3, .stMarkdown h3 {
                color: #2980b9;
                font-weight: bold;
            }
            div.stButton > button {
                background-color: #3498db;
                color: white;
                border-radius: 8px;
                font-size: 16px;
            }
            div.stButton > button:hover {
                background-color: #2980b9;
                color: white;
            }
            div[data-testid="metric-container"] {
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 10px;
                border: 1px solid #bdc3c7;
                box-shadow: 1px 1px 5px rgba(0,0,0,0.05);
            }
            .ag-theme-material {
                border: 1px solid #ced4da;
                border-radius: 5px;
            }
        </style>
    """, unsafe_allow_html=True)

    if 'survey_id' not in st.session_state:
        st.title("📋 Chọn khảo sát")
        surveys = get_surveys()
        survey_options = {s[1]: s[0] for s in surveys}

        selected_survey = st.selectbox("Chọn tên khảo sát", list(survey_options.keys()))
        if st.button("Xem thống kê"):
            st.session_state.survey_id = survey_options[selected_survey]
            st.rerun()

    else:
        survey_id = st.session_state.survey_id
        survey_details, stats, text_answers = process_survey_data(survey_id, get_survey_details, get_survey_answers)

        st.title(f"📊 Thống kê khảo sát: {survey_details['title']}")

        st.markdown("### 🧾 Thông tin chung")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏫 Cơ sở đào tạo", survey_details['facility_name'])
        with col2:
            st.metric("📤 Số phiếu phát ra", survey_details['total_answers'])
        with col3:
            st.metric("📥 Số phiếu thu vào", survey_details['valid_answers'])

        st.markdown("### 🗂️ Thống kê khảo sát")
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
                total_width = 600 + len(options) * 180 + 100
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
            st.markdown("### 📝 Đánh giá, ý kiến")
            for question_id, question_data in text_answers.items():
                st.write(f"**Câu hỏi:** {question_data['question']}")
                df_text = pd.DataFrame(
                    [[i + 1, answer] for i, answer in enumerate(question_data['answers'])],
                    columns=['STT', 'Câu trả lời']
                ).reset_index(drop=True)

                AgGrid(
                    df_text,
                    gridOptions={
                        "columnDefs": [
                            {"headerName": "STT", "field": "STT", "width": 30, "pinned": "center"},
                            {"headerName": "Câu trả lời", "field": "Câu trả lời", "wrapText": True, "autoHeight": True, "minWidth": 600}
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

        # Biểu đồ tròn thể hiện tỷ lệ lựa chọn
        st.markdown("### 📈 Biểu đồ thể hiện tỷ lệ hài lòng")

        chart_count = 0
        chart_columns = []

        for question_type, group_data in stats.items():
            for options, group_stats in group_data.items():
                for stat in group_stats:
                    # Tạo hàng mới sau mỗi 3 biểu đồ
                    if chart_count % 3 == 0:
                        chart_columns = st.columns(3)

                    col = chart_columns[chart_count % 3]
                    with col:
                        st.markdown(f"**{stat['question']}**")

                        # Lọc bỏ những giá trị 0 nhưng vẫn giữ label trong legend
                        chart_df = pd.DataFrame({
                            'Lựa chọn': list(stat['percentages'].keys()),
                            'Tỷ lệ (%)': list(stat['percentages'].values())
                        })

                        visible_labels = chart_df[chart_df['Tỷ lệ (%)'] > 0]

                        st.plotly_chart(
                            {
                                "data": [ {
                                    "type": "pie",
                                    "labels": chart_df['Lựa chọn'],
                                    "values": chart_df['Tỷ lệ (%)'],
                                    "hole": 0.3,
                                    "textinfo": "percent",
                                    "textposition": "inside",
                                    "insidetextorientation": "radial",
                                    "hoverinfo": "percent",
                                    "marker": {
                                        "colors": ["#3498db", "#e67e22", "#9b59b6", "#f1c40f", "#e84393"]
                                    }
                                }],
                                "layout": {
                                    "uniformtext": {"mode": "hide", "minsize": 10},
                                    "margin": {"t": 20, "b": 20, "l": 20, "r": 20},
                                    "height": 300,
                                    "showlegend": True,
                                    "legend": {
                                        "orientation": "h",
                                        "x": 0.5,
                                        "xanchor": "center"
                                    },
                                    "font": {"size": 14, "color": "#2c3e50"},
                                    "paper_bgcolor": "#f8f9fa"
                                }
                            },
                            use_container_width=True
                        )

                    chart_count += 1

        if st.button("🔙 Quay lại chọn khảo sát"):
            del st.session_state.survey_id
            st.rerun()

if __name__ == "__main__":
    main()
