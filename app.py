import streamlit as st
import pandas as pd
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

        st.title(f"Thống kê khảo sát: {survey_details['elements'][0]['title']}")

        st.subheader("Thông tin chung")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cơ sở đào tạo", survey_details['facility_name'])
        with col2:
            st.metric("Số phiếu phát ra", survey_details['total_answers'])
        with col3:
            st.metric("Số phiếu thu vào", survey_details['valid_answers'])

        # Hiển thị thống kê câu hỏi lựa chọn (single-choice và multiple-choice)
        for question_type, group_data in stats.items():
            for i, (options, group_stats) in enumerate(group_data.items(), 1):
                st.subheader(f"Bảng thống kê nhóm câu hỏi {question_type.replace('-', ' ').title()} {i} ({', '.join(options)})")

                columns = ['TT', 'Câu hỏi']
                for opt in options:
                    columns.extend([f"{opt} (Số lượng)", f"{opt} (%)"])
                if question_type == 'single-choice' and set(options) == set(['Rất không hài lòng', 'Không hài lòng', 'Bình thường', 'Hài lòng', 'Rất hài lòng']):
                    columns.extend([
                        "Số phiếu KHL", "Không hài lòng (%) (Tổng)",
                        "Số phiếu HL", "Hài lòng (%) (Tổng)"
                    ])

                table_data = []
                for j, stat in enumerate(group_stats, 1):
                    row = [j, stat['question']]
                    for opt in options:
                        row.extend([
                            stat['option_counts'][opt],
                            f"{stat['percentages'][opt]:.2f}%"
                        ])
                    if stat.get('satisfaction_stats'):
                        row.extend([
                            stat['satisfaction_stats']['Không hài lòng']['count'],
                            f"{stat['satisfaction_stats']['Không hài lòng']['percent']:.2f}%",
                            stat['satisfaction_stats']['Hài lòng']['count'],
                            f"{stat['satisfaction_stats']['Hài lòng']['percent']:.2f}%"
                        ])
                    table_data.append(row)

                df = pd.DataFrame(table_data, columns=columns)
                st.dataframe(df, use_container_width=True)

        # Hiển thị câu trả lời tự luận
        if text_answers:
            st.subheader("Câu trả lời tự luận")
            for question_id, question_data in text_answers.items():
                st.write(f"**Câu hỏi: {question_data['question']}**")
                df_text = pd.DataFrame(
                    [[i + 1, answer] for i, answer in enumerate(question_data['answers'])],
                    columns=['STT', 'Câu trả lời']
                )
                st.dataframe(df_text, use_container_width=True)

        if st.button("Quay lại chọn khảo sát"):
            del st.session_state.survey_id
            st.rerun()

if __name__ == "__main__":
    main()