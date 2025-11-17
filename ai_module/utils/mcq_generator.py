# ai_module/utils/mcq_generator.py
import random

# A small, editable knowledgebase for prototypes
DEFAULT_KNOWLEDGE = {
    'web_development': [
        {
            'concept': 'Django ORM',
            'fact': 'Django ORM provides a high-level abstraction to interact with databases using Python models.',
            'qa': {
                'question': 'What does Django ORM allow you to do?',
                'answer': 'Interact with the database using Python objects (models).',
                'distractors': [
                    'Write SQL queries in the browser',
                    'Automatically deploy applications to server',
                    'Render dynamic HTML without templates'
                ]
            }
        },
        {
            'concept': 'CSRF protection',
            'fact': 'Django has built-in CSRF protection for POST forms',
            'qa': {
                'question': 'What is the main purpose of CSRF protection in Django?',
                'answer': 'Prevent Cross Site Request Forgery attacks.',
                'distractors': [
                    'Prevent SQL Injection attacks',
                    'Prevent Cross Site Scripting attacks',
                    'Encrypt HTTP responses'
                ]
            }
        },
        # add more entries...
    ],
    'data_science': [
        {
            'concept': 'Pandas DataFrame',
            'fact': 'DataFrame is a 2-dimensional labeled data structure in pandas.',
            'qa': {
                'question': 'What is a pandas DataFrame?',
                'answer': 'A 2-dimensional labeled data structure for handling tabular data.',
                'distractors': [
                    'A model training algorithm',
                    'An HTML templating engine',
                    'A cloud storage service'
                ]
            }
        }
    ],
    'general': [
        {
            'concept': 'HTTP',
            'fact': 'HTTP is an application protocol for distributed, collaborative, hypermedia information systems.',
            'qa': {
                'question': 'What does HTTP stand for?',
                'answer': 'HyperText Transfer Protocol',
                'distractors': [
                    'Hyper Transfer Text Protocol',
                    'HighText Transfer Protocol',
                    'Hyperlink Transfer Protocol'
                ]
            }
        }
    ]
}

class MCQGenerator:
    def __init__(self, knowledge_base=None):
        self.knowledge = knowledge_base if knowledge_base else DEFAULT_KNOWLEDGE

    def generate_questions(self, domain, num_questions=10):
        """
        Returns a list of dicts: {question, options: [A,B,C,D], correct_answer_index (0..3), difficulty}
        """
        bucket = self.knowledge.get(domain, []) or self.knowledge.get('general', [])
        questions = []
        # If not enough entries, repeat or sample from general
        choices = bucket.copy()
        if len(choices) < num_questions:
            # extend with general
            choices += self.knowledge.get('general', []) * ((num_questions // max(len(bucket),1)) + 1)
        random.shuffle(choices)
        selected = choices[:num_questions]
        for item in selected:
            qa = item.get('qa')
            if not qa:
                continue
            correct = qa['answer']
            distractors = qa.get('distractors', [])[:3]
            # ensure 3 distractors
            while len(distractors) < 3:
                distractors.append('None of the above')
            options = [correct] + distractors
            random.shuffle(options)
            correct_idx = options.index(correct)
            questions.append({
                'concept': item.get('concept'),
                'question': qa['question'],
                'options': options,
                'correct_index': correct_idx,
                'difficulty': 'medium'  # simple default; replace with DifficultyManager later
            })
        return questions
