"""Tests for courses app."""
from datetime import date
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import User
from .models import Course, Lesson, Test, Question, Choice, LessonProgress


def make_test_data():
    """Kurs, dars va test yaratish (test uchun yordamchi)."""
    course = Course.objects.create(slug='test', title_uz='Test Course', type='IT')
    lesson = Lesson.objects.create(
        course=course, title_uz='Test Lesson',
        youtube_id='abc123', duration='10:00', order=0,
    )
    test_obj = Test.objects.create(
        lesson=lesson, title_uz='Test', subject='Frontend', type='IT',
    )
    q1 = Question.objects.create(test=test_obj, text_uz='Q1', order=0)
    Choice.objects.create(question=q1, text_uz='A', is_correct=True, order=0)
    Choice.objects.create(question=q1, text_uz='B', is_correct=False, order=1)
    q2 = Question.objects.create(test=test_obj, text_uz='Q2', order=1)
    Choice.objects.create(question=q2, text_uz='C', is_correct=True, order=0)
    Choice.objects.create(question=q2, text_uz='D', is_correct=False, order=1)
    return course, lesson, test_obj, [q1, q2]


class CourseTests(TestCase):
    """Kurs va dars testlari."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student', password='test1234', role=User.ROLE_STUDENT,
        )
        self.course, self.lesson, self.test_obj, self.questions = make_test_data()

    def test_list_courses(self):
        """Kurslar ro'yxati."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Course')

    def test_list_courses_filter_by_type(self):
        """Kurslarni tur bo'yicha filtrlash."""
        Course.objects.create(slug='school', title_uz='School', type='School')
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('course-list'), {'type': 'School'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'School')

    def test_courses_require_auth(self):
        """Kurslarni ko'rish uchun login kerak."""
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, 401)


class DailyLimitTests(TestCase):
    """Kunlik limit testlari."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student', password='test1234', plan=User.PLAN_FREE,
        )
        self.course, self.lesson, _, _ = make_test_data()

    def test_daily_limit_initial(self):
        """Yangi user — 3 limit ko'rinadi."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('daily-limit'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['limit'], 3)
        self.assertEqual(response.data['remaining'], 3)
        self.assertEqual(response.data['watched_count'], 0)

    def test_daily_limit_after_watching(self):
        """1 ta dars ko'rilgach — 2 qoladi."""
        from django.utils import timezone
        LessonProgress.objects.create(
            user=self.user, lesson=self.lesson,
            status=LessonProgress.STATUS_WATCHED,
            watched_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('daily-limit'))
        self.assertEqual(response.data['watched_count'], 1)
        self.assertEqual(response.data['remaining'], 2)

    def test_premium_user_unlimited(self):
        """Premium user — cheksiz."""
        self.user.plan = User.PLAN_PREMIUM
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('daily-limit'))
        self.assertEqual(response.data['remaining'], 999)
        self.assertIsNone(response.data['limit'])


class WatchLessonTests(TestCase):
    """Dars ko'rish testlari."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student', password='test1234', plan=User.PLAN_FREE,
        )
        self.course, self.lesson, _, _ = make_test_data()

    def test_watch_lesson_success(self):
        """Dars muvaffaqiyatli ko'rish."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('watch-lesson', kwargs={'lesson_id': self.lesson.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(LessonProgress.objects.filter(
            user=self.user, lesson=self.lesson,
        ).exists())

    def test_watch_lesson_daily_limit(self):
        """3 ta darsdan keyin 4-chi ko'rilmaydi."""
        from django.utils import timezone
        # 3 ta dars yaratamiz
        l1 = Lesson.objects.create(course=self.course, title_uz='L1', youtube_id='a', order=1)
        l2 = Lesson.objects.create(course=self.course, title_uz='L2', youtube_id='b', order=2)
        l3 = Lesson.objects.create(course=self.course, title_uz='L3', youtube_id='c', order=3)
        l4 = Lesson.objects.create(course=self.course, title_uz='L4', youtube_id='d', order=4)

        # Birinchi 3 ta dars bugun ko'rilgan
        for lesson in [l1, l2, l3]:
            LessonProgress.objects.create(
                user=self.user, lesson=lesson,
                status=LessonProgress.STATUS_WATCHED,
                watched_at=timezone.now(),
            )

        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('watch-lesson', kwargs={'lesson_id': l4.id})
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'], 'daily_limit')

    def test_premium_can_watch_unlimited(self):
        """Premium user cheklovsiz ko'radi."""
        self.user.plan = User.PLAN_PREMIUM
        self.user.save()
        # 5 ta dars yaratamiz
        lessons = []
        for i in range(5):
            lessons.append(Lesson.objects.create(
                course=self.course, title_uz=f'L{i}', youtube_id=f'y{i}', order=i+1,
            ))

        self.client.force_authenticate(self.user)
        for lesson in lessons:
            response = self.client.post(
                reverse('watch-lesson', kwargs={'lesson_id': lesson.id})
            )
            self.assertEqual(response.status_code, 200)


class TestSubmissionTests(TestCase):
    """Test topshirish testlari."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student', password='test1234', plan=User.PLAN_FREE,
        )
        self.course, self.lesson, self.test_obj, self.questions = make_test_data()

    def test_get_test(self):
        """Test savollarini olish."""
        self.client.force_authenticate(self.user)
        response = self.client.get(
            reverse('lesson-test', kwargs={'lesson_id': self.lesson.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Test')
        self.assertEqual(len(response.data['questions']), 2)

    def test_submit_all_correct(self):
        """Barcha javob to'g'ri — 100% ball."""
        self.client.force_authenticate(self.user)
        correct_choice_q1 = self.questions[0].choices.get(is_correct=True)
        correct_choice_q2 = self.questions[1].choices.get(is_correct=True)

        response = self.client.post(
            reverse('submit-test', kwargs={'lesson_id': self.lesson.id}),
            {'answers': {
                str(self.questions[0].id): str(correct_choice_q1.id),
                str(self.questions[1].id): str(correct_choice_q2.id),
            }},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['score'], 100)
        self.assertEqual(response.data['correct'], 2)
        self.assertTrue(response.data['passed'])
        self.assertEqual(response.data['letter'], 'A')

    def test_submit_all_wrong(self):
        """Barcha javob noto'g'ri — 0% ball."""
        self.client.force_authenticate(self.user)
        wrong_choice_q1 = self.questions[0].choices.get(is_correct=False)

        response = self.client.post(
            reverse('submit-test', kwargs={'lesson_id': self.lesson.id}),
            {'answers': {
                str(self.questions[0].id): str(wrong_choice_q1.id),
                str(self.questions[1].id): str(wrong_choice_q1.id),
            }},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['score'], 0)
        self.assertFalse(response.data['passed'])
        self.assertEqual(response.data['letter'], 'F')

    def test_submit_updates_progress(self):
        """Test submit progress yangilaydi."""
        self.client.force_authenticate(self.user)
        correct_choice_q1 = self.questions[0].choices.get(is_correct=True)
        correct_choice_q2 = self.questions[1].choices.get(is_correct=True)

        self.client.post(
            reverse('submit-test', kwargs={'lesson_id': self.lesson.id}),
            {'answers': {
                str(self.questions[0].id): str(correct_choice_q1.id),
                str(self.questions[1].id): str(correct_choice_q2.id),
            }},
            format='json',
        )

        progress = LessonProgress.objects.get(user=self.user, lesson=self.lesson)
        self.assertEqual(progress.status, LessonProgress.STATUS_PASSED)
        self.assertEqual(progress.last_score, 100)


class AdminCourseViewTests(TestCase):
    """Admin — barcha kurslar va progress endpoint testlari."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student', password='student1234',
            role=User.ROLE_STUDENT,
        )
        self.course = Course.objects.create(
            slug='test', title_uz='Test', type=Course.TYPE_IT, is_active=False,
        )
        self.lesson = Lesson.objects.create(
            course=self.course, title_uz='L1', youtube_id='abc', order=1,
        )
        LessonProgress.objects.create(
            user=self.student, lesson=self.lesson, status=LessonProgress.STATUS_WATCHED,
        )

    def test_admin_sees_inactive_courses(self):
        """Admin noaktiv kurslarni ham ko'radi."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-course-list'))
        self.assertEqual(response.status_code, 200)
        slugs = [c['slug'] for c in response.data]
        self.assertIn('test', slugs)

    def test_admin_sees_all_progress(self):
        """Admin barcha LessonProgress'ni ko'radi."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-progress-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_admin_progress_filter_by_user(self):
        """Progress'ni user_id bo'yicha filtrlash."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse('admin-progress-list'),
            {'user_id': self.student.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_admin_progress_filter_by_status(self):
        """Progress'ni status bo'yicha filtrlash."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse('admin-progress-list'),
            {'status': 'passed'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_student_cannot_access_admin_course_list(self):
        """Student admin kurslar ro'yxatini ko'ra olmaydi — 403."""
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse('admin-course-list'))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_admin_progress(self):
        """Student admin progress'ni ko'ra olmaydi — 403."""
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse('admin-progress-list'))
        self.assertEqual(response.status_code, 403)