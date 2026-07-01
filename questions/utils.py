import openpyxl
from .models import Question, Choice


def import_questions_from_excel(file, subject, user):
    wb = openpyxl.load_workbook(file)
    ws = wb.active
    count = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        content = str(row[0]).strip()
        if not content:
            continue

        q_type = str(row[1]).strip().lower() if row[1] else 'single'
        type_map = {
            'single': Question.TYPE_SINGLE,
            'multiple': Question.TYPE_MULTIPLE,
            'true_false': Question.TYPE_TRUE_FALSE,
            'essay': Question.TYPE_ESSAY,
            'trắc nghiệm 1 đáp án': Question.TYPE_SINGLE,
            'trắc nghiệm nhiều đáp án': Question.TYPE_MULTIPLE,
            'đúng/sai': Question.TYPE_TRUE_FALSE,
            'tự luận': Question.TYPE_ESSAY,
        }
        question_type = type_map.get(q_type, Question.TYPE_SINGLE)

        difficulty_raw = str(row[2]).strip().lower() if row[2] else 'medium'
        diff_map = {'dễ': 'easy', 'easy': 'easy', 'trung bình': 'medium', 'medium': 'medium', 'khó': 'hard', 'hard': 'hard'}
        difficulty = diff_map.get(difficulty_raw, 'medium')

        choices_data = []
        correct_labels = []
        if len(row) > 3:
            labels = ['A', 'B', 'C', 'D', 'E']
            for i, label in enumerate(labels):
                col_idx = 3 + i
                if col_idx < len(row) and row[col_idx]:
                    choices_data.append((label, str(row[col_idx]).strip()))

        if len(row) > 8 and row[8]:
            correct_labels = [c.strip().upper() for c in str(row[8]).split(',')]

        explanation = str(row[9]).strip() if len(row) > 9 and row[9] else ''

        question = Question.objects.create(
            subject=subject,
            question_type=question_type,
            difficulty=difficulty,
            content=content,
            explanation=explanation,
            created_by=user,
        )

        for i, (label, content_c) in enumerate(choices_data):
            Choice.objects.create(
                question=question,
                label=label,
                content=content_c,
                is_correct=(label in correct_labels),
                order=i + 1,
            )
        count += 1

    return count


def import_questions_from_docx(file, subject, user):
    from docx import Document
    import re

    doc = Document(file)
    count = 0
    current_question = None
    current_choices = []
    correct_labels = []

    def save_question():
        nonlocal current_question, current_choices, correct_labels, count
        if current_question:
            q = Question.objects.create(
                subject=subject,
                question_type=Question.TYPE_SINGLE,
                content=current_question,
                created_by=user,
            )
            for i, (label, text, is_correct) in enumerate(current_choices):
                Choice.objects.create(
                    question=q, label=label, content=text,
                    is_correct=is_correct, order=i + 1
                )
            count += 1
        current_question = None
        current_choices = []
        correct_labels = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Match question: starts with number like "1." or "Câu 1:"
        q_match = re.match(r'^(?:Câu\s+)?(\d+)[.:\)]\s+(.+)', text, re.IGNORECASE)
        if q_match:
            save_question()
            current_question = q_match.group(2).strip()
            continue

        # Match choice: A. B. C. D.
        c_match = re.match(r'^([A-Ea-e])[.)\s]\s*(.+)', text)
        if c_match and current_question:
            label = c_match.group(1).upper()
            content = c_match.group(2).strip()
            is_correct = content.startswith('*') or content.endswith('*')
            content = content.strip('*').strip()
            current_choices.append((label, content, is_correct))
            continue

        # Answer key line: "Đáp án: A" or "Answer: A,B"
        ans_match = re.match(r'^(?:Đáp án|Answer)[:\s]+([A-E,\s]+)', text, re.IGNORECASE)
        if ans_match and current_question:
            correct_labels = [c.strip().upper() for c in ans_match.group(1).split(',')]
            for i, (label, content, _) in enumerate(current_choices):
                current_choices[i] = (label, content, label in correct_labels)

    save_question()
    return count
