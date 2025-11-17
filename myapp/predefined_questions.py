# predefined_questions.py
# Domain -> list of (question, ideal_answer) pairs
PREDEFINED_QUESTIONS = {
    "general": [
        ("Introduce yourself.", "A concise summary of background, education, core skills, and relevant experience."),
    ],

    "web_development": [
        ("What is Django used for?", "Django is a high-level Python web framework for rapid development and clean design."),
        ("Explain the concept of ORM in Django.", "Django ORM is an abstraction layer that allows you to interact with the database using Python models instead of raw SQL."),
        ("What is the difference between Django and Flask?", "Django is a batteries-included full-stack framework with built-in admin and ORM; Flask is a lightweight microframework offering more choice."),
        ("Explain what REST APIs are and how you build them in Django.", "REST APIs expose resources over HTTP; in Django you build them by serializing models and using viewsets or generic views (or Django REST Framework).")
    ],

    "mobile_development": [
        ("What is React Native and how is it different from Flutter?", "React Native uses JavaScript and bridges to native components; Flutter uses Dart and renders with its own engine."),
        ("Explain the app lifecycle on Android.", "Android apps have lifecycle callbacks like onCreate, onStart, onResume, onPause, onStop, onDestroy for activities."),
        ("What is a widget in Flutter?", "Widgets are the basic building blocks of Flutter UI; everything is a widget."),
        ("How do you debug a crash in a mobile app?", "Check logs, reproduce the crash, use breakpoints and stack traces, and examine recent code changes.")
    ],

    "data_science": [
        ("What is overfitting and how to prevent it?", "Overfitting happens when a model fits noise; prevent with cross-validation, regularization, and more data."),
        ("Explain the difference between supervised and unsupervised learning.", "Supervised learning uses labeled data to predict; unsupervised finds structure without labels."),
        ("When would you use Pandas vs NumPy?", "Use NumPy for numeric arrays and performance; use Pandas for tabular data and data manipulation."),
        ("What is a train/test split?", "Divide data into training and testing sets to measure generalization.")
    ],

    "devops": [
        ("What is Docker and why use it?", "Docker packages apps into containers for reproducibility and isolation."),
        ("What is Kubernetes and what problem does it solve?", "Kubernetes orchestrates containers across nodes for scaling and management."),
        ("Explain CI/CD briefly.", "Continuous Integration/Continuous Deployment automates building, testing and deploying code."),
        ("When would you use infrastructure as code?", "To version control infra, make reproducible environments, and automate provisioning.")
    ],

    "database": [
        ("When would you use SQL vs NoSQL?", "SQL for structured relational data and complex joins; NoSQL when schema is flexible or for scale and speed."),
        ("Explain indexing and when to use it.", "Indexing speeds queries on keys/columns but uses more storage and slows writes; use on frequently queried fields."),
        ("What is normalization?", "Normalization organizes DB to reduce redundancy and improve integrity across tables."),
        ("What is ACID?", "Set of DB properties: Atomicity, Consistency, Isolation, Durability.")
    ]
}
