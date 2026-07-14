"""Seed courses and tests from frontend videos.js + tests.js"""
from django.core.management.base import BaseCommand

from apps.courses.models import Course, Lesson, Test, Question, Choice


COURSES = [
    {
        'slug': 'frontend',
        'title_uz': 'Frontend Development',
        'icon': '🌐',
        'type': 'IT',
        'lessons': [
            {'title_uz': 'HTML Asoslari va Tuzilishi',           'youtube_id': 'qz0aGYrrlhU', 'duration': '18:30'},
            {'title_uz': 'CSS Stillash va Flexbox',               'youtube_id': 'yfoY53QXEnI', 'duration': '22:15'},
            {'title_uz': "JavaScript — Kirish va O'zgaruvchilar", 'youtube_id': 'W6NZfCO5SIk', 'duration': '25:00'},
            {'title_uz': 'React Asoslari — Komponentlar',         'youtube_id': 'Ke90Tje7VS0', 'duration': '30:45'},
        ],
    },
    {
        'slug': 'backend',
        'title_uz': 'Backend Development',
        'icon': '⚙️',
        'type': 'IT',
        'lessons': [
            {'title_uz': 'Node.js — Kirish va NPM',             'youtube_id': 'TlB_eWDSMt4', 'duration': '20:00'},
            {'title_uz': 'Express.js bilan REST API',            'youtube_id': 'L72fhGm1tfE', 'duration': '28:30'},
            {'title_uz': "PostgreSQL — Ma'lumotlar bazasi",      'youtube_id': 'qw--VYLpxG4', 'duration': '24:00'},
            {'title_uz': 'JWT bilan Autentifikatsiya',           'youtube_id': 'mbsmsi7l3r4', 'duration': '22:15'},
        ],
    },
    {
        'slug': 'mobile',
        'title_uz': 'Mobile Development',
        'icon': '📱',
        'type': 'IT',
        'lessons': [
            {'title_uz': 'React Native — Kirish',               'youtube_id': '0-S5a0eXPoc', 'duration': '19:30'},
            {'title_uz': 'Expo bilan Ilova Yaratish',           'youtube_id': 'oBWBDaqpCVQ', 'duration': '26:00'},
            {'title_uz': 'Navigation va Ekranlar',              'youtube_id': '1bSRHdZvh4s', 'duration': '23:45'},
            {'title_uz': 'API bilan Ishlash',                   'youtube_id': 'nkEmPAte4fE', 'duration': '21:00'},
        ],
    },
    {
        'slug': 'computer-literacy',
        'title_uz': 'Kompyuter Savodxonligi',
        'icon': '🖥️',
        'type': 'IT',
        'lessons': [
            {'title_uz': 'Kompyuter asoslari va OS',             'youtube_id': 'Jfh5zV9b87k', 'duration': '15:00'},
            {'title_uz': 'Microsoft Word bilan ishlash',         'youtube_id': '5g5hEcL4fwA', 'duration': '18:00'},
            {'title_uz': 'Microsoft Excel — Jadvallar',          'youtube_id': 'rwbho0CwFAI', 'duration': '20:00'},
            {'title_uz': 'PowerPoint — Taqdimotlar',             'youtube_id': 'SiEBIRO0rvY', 'duration': '16:30'},
            {'title_uz': 'Internet va Email xavfsizligi',        'youtube_id': 'Yjjpr-Es7Vc', 'duration': '14:00'},
            {'title_uz': 'Google Drive va Cloud xizmatlar',      'youtube_id': 'eRqUE6IHTEA', 'duration': '13:30'},
        ],
    },
]


TESTS = [
    {
        'course_slug': 'frontend',
        'lesson_index': 0,  # HTML asoslari
        'title_uz': 'HTML & CSS Asoslari',
        'subject': 'Frontend',
        'type': 'IT',
        'questions': [
            {
                'text_uz': 'HTML qisqartmasi nima?',
                'choices': [
                    ('HyperText Markup Language', True),
                    ('HighText Machine Language', False),
                    ('HyperTool Markup Language', False),
                    ('Hyperlink Markup Language', False),
                ],
            },
            {
                'text_uz': 'CSS nima uchun ishlatiladi?',
                'choices': [
                    ('Sahifani uslublash uchun', True),
                    ('Sahifani yaratish uchun', False),
                    ("Serverga so'rov yuborish uchun", False),
                    ("Ma'lumot saqlash uchun", False),
                ],
            },
            {
                'text_uz': 'Qaysi teg sarlavha uchun ishlatiladi?',
                'choices': [
                    ('<head>', False),
                    ('<h1>', True),
                    ('<title>', False),
                    ('<header>', False),
                ],
            },
            {
                'text_uz': "CSS'da rang berish uchun qaysi xususiyat ishlatiladi?",
                'choices': [
                    ('font-color', False),
                    ('text-color', False),
                    ('color', True),
                    ('background', False),
                ],
            },
            {
                'text_uz': "HTML'da havola yaratish uchun qaysi teg ishlatiladi?",
                'choices': [
                    ('<link>', False),
                    ('<a>', True),
                    ('<p>', False),
                    ('<nav>', False),
                ],
            },
        ],
    },
    {
        'course_slug': 'frontend',
        'lesson_index': 2,  # JavaScript
        'title_uz': 'JavaScript Asoslari',
        'subject': 'Frontend',
        'type': 'IT',
        'questions': [
            {
                'text_uz': "JavaScript'da o'zgaruvchi e'lon qilish uchun qaysi kalit so'z ishlatiladi?",
                'choices': [
                    ('var', False),
                    ('let', False),
                    ('const', False),
                    ("Hammasi to'g'ri", True),
                ],
            },
            {
                'text_uz': 'Konsolga chiqarish uchun qaysi buyruq ishlatiladi?',
                'choices': [
                    ('print()', False),
                    ('console.log()', True),
                    ('echo()', False),
                    ('System.out.println()', False),
                ],
            },
            {
                'text_uz': "Array'da elementlar sonini qaytaruvchi xususiyat?",
                'choices': [
                    ('.size', False),
                    ('.count', False),
                    ('.length', True),
                    ('.total', False),
                ],
            },
            {
                'text_uz': "JavaScript'da shartli operatorning to'g'ri yozilishi?",
                'choices': [
                    ('if (x = 5)', False),
                    ('if x == 5:', False),
                    ('if (x === 5)', True),
                    ('if x === 5 {}', False),
                ],
            },
            {
                'text_uz': 'DOM nima?',
                'choices': [
                    ('Document Object Model', True),
                    ('Data Object Model', False),
                    ('Dynamic Origin Model', False),
                    ('Document Online Model', False),
                ],
            },
        ],
    },
    {
        'course_slug': 'backend',
        'lesson_index': 2,  # PostgreSQL dars
        'title_uz': 'Algebra - Tenglamalar',
        'subject': 'Matematika',
        'type': 'School',
        'questions': [
            {
                'text_uz': '2x + 6 = 14. x = ?',
                'choices': [('3', False), ('4', True), ('5', False), ('6', False)],
            },
            {
                'text_uz': 'x² - 9 = 0. x = ?',
                'choices': [('3', False), ('-3', False), ('±3', True), ('9', False)],
            },
            {
                'text_uz': '(x+2)(x-3) = 0 tenglamaning yechimlari?',
                'choices': [
                    ('x=2, x=-3', False),
                    ('x=-2, x=3', True),
                    ('x=2, x=3', False),
                    ('x=-2, x=-3', False),
                ],
            },
            {
                'text_uz': "Agar 3x = 21 bo'lsa, x nechaga teng?",
                'choices': [('6', False), ('7', True), ('8', False), ('9', False)],
            },
            {
                'text_uz': 'x/4 + 2 = 5. x = ?',
                'choices': [('8', False), ('10', False), ('12', True), ('16', False)],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Frontend videos.js + tests.js dan kurs va testlarni seed qiladi"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Kurslar seed qilinmoqda...")

        for order, cdata in enumerate(COURSES):
            course, created = Course.objects.update_or_create(
                slug=cdata['slug'],
                defaults={
                    'title_uz': cdata['title_uz'],
                    'icon': cdata['icon'],
                    'type': cdata['type'],
                    'order': order,
                    'is_active': True,
                },
            )
            self.stdout.write(f"  {'🆕' if created else '♻️'} {course.title_uz}")

            for lesson_order, ldata in enumerate(cdata['lessons']):
                Lesson.objects.update_or_create(
                    course=course,
                    order=lesson_order,
                    defaults={
                        'title_uz': ldata['title_uz'],
                        'youtube_id': ldata['youtube_id'],
                        'duration': ldata['duration'],
                    },
                )

        self.stdout.write("\n🔄 Testlar seed qilinmoqda...")
        for tdata in TESTS:
            try:
                course = Course.objects.get(slug=tdata['course_slug'])
                lesson = course.lessons.all()[tdata['lesson_index']]
            except (Course.DoesNotExist, IndexError):
                self.stdout.write(f"  ⚠️ Dars topilmadi: {tdata['course_slug']}")
                continue

            test, created = Test.objects.update_or_create(
                lesson=lesson,
                defaults={
                    'title_uz': tdata['title_uz'],
                    'subject': tdata['subject'],
                    'type': tdata['type'],
                },
            )

            # Eski savollarni tozalash
            test.questions.all().delete()

            for q_order, qdata in enumerate(tdata['questions']):
                question = Question.objects.create(
                    test=test,
                    text_uz=qdata['text_uz'],
                    order=q_order,
                )
                for c_order, (text, is_correct) in enumerate(qdata['choices']):
                    Choice.objects.create(
                        question=question,
                        text_uz=text,
                        is_correct=is_correct,
                        order=c_order,
                    )

            self.stdout.write(f"  {'🆕' if created else '♻️'} {test.title_uz} ({len(tdata['questions'])} savol)")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Tayyor! {Course.objects.count()} kurs, {Lesson.objects.count()} dars, {Test.objects.count()} test"))