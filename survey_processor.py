from collections import defaultdict

def process_survey_data(survey_id, get_survey_details, get_survey_answers):
    survey_details = get_survey_details(survey_id)
    answers = get_survey_answers(survey_id)

    question_groups = defaultdict(lambda: defaultdict(list))
    text_questions = {}
    elements = survey_details['elements']

    # Phân loại câu hỏi
    for element in elements:
        if element.get('controlType') in ['single-choice', 'multiple-choice'] and element.get('questionData'):
            q_data = element['questionData']
            options = tuple(q_data['OPTIONS']) if q_data['OPTIONS'] else ()
            question_type = element['controlType']
            question_groups[question_type][options].append({
                'id': element['id'],
                'content': q_data['CONTENT']
            })
        elif element.get('controlType') == 'text-answer' and element.get('questionData'):
            q_data = element['questionData']
            text_questions[element['id']] = {
                'content': q_data['CONTENT']
            }

    # Thống kê câu hỏi lựa chọn
    stats = {}
    for question_type, group_data in question_groups.items():
        stats[question_type] = {}
        for options, questions in group_data.items():
            if not options:
                continue

            group_stats = []
            for question in questions:
                option_counts = {opt: 0 for opt in options}
                total_responses = 0  # For single-choice: số phiếu, for multiple-choice: số phiếu có câu trả lời

                for answer in answers:
                    if question['id'] in answer:
                        response = answer[question['id']]
                        if question_type == 'single-choice':
                            if isinstance(response, str) and response.isdigit() and 0 <= int(response) < len(options):
                                option_counts[options[int(response)]] += 1
                                total_responses += 1
                        elif question_type == 'multiple-choice':
                            if isinstance(response, list):
                                total_responses += 1
                                for resp in response:
                                    if isinstance(resp, str) and resp.isdigit() and 0 <= int(resp) < len(options):
                                        option_counts[options[int(resp)]] += 1

                # Tính phần trăm
                if question_type == 'single-choice':
                    percentages = {
                        opt: (count / total_responses * 100) if total_responses > 0 else 0
                        for opt, count in option_counts.items()
                    }
                else:  # multiple-choice
                    total_selections = sum(option_counts.values())
                    percentages = {
                        opt: (count / total_selections * 100) if total_selections > 0 else 0
                        for opt, count in option_counts.items()
                    }

                # Tính toán satisfaction_stats cho single-choice với bộ tùy chọn cụ thể
                satisfaction_stats = {}
                if question_type == 'single-choice' and set(options) == set(['Rất không hài lòng', 'Không hài lòng', 'Bình thường', 'Hài lòng', 'Rất hài lòng']):
                    satisfaction_stats = {
                        'Không hài lòng': {
                            'count': option_counts['Rất không hài lòng'] + option_counts['Không hài lòng'],
                            'percent': percentages['Rất không hài lòng'] + percentages['Không hài lòng']
                        },
                        'Hài lòng': {
                            'count': option_counts['Bình thường'] + option_counts['Hài lòng'] + option_counts['Rất hài lòng'],
                            'percent': percentages['Bình thường'] + percentages['Hài lòng'] + percentages['Rất hài lòng']
                        }
                    }

                group_stats.append({
                    'question': question['content'],
                    'option_counts': option_counts,
                    'percentages': percentages,
                    'satisfaction_stats': satisfaction_stats
                })

            stats[question_type][options] = group_stats

    # Thống kê câu trả lời tự luận
    text_answers = {}
    for question_id, question_data in text_questions.items():
        answers_list = []
        for answer in answers:
            if question_id in answer and answer[question_id]:
                answers_list.append(answer[question_id])
        if answers_list:
            text_answers[question_id] = {
                'question': question_data['content'],
                'answers': answers_list
            }

    return survey_details, stats, text_answers
