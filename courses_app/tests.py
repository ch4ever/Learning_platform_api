# Create your tests here.
from conftest import *
from courses_app.models import Course, CourseJoinRequests, CourseRoles


#client
#student
#teacher approved/unapproved

@pytest.mark.django_db
def test_course_create_by_approved_teacher(teacher_with_auth):
    data = {
        'title':'test title',
        'short_description':'test short description',
    }
    response = teacher_with_auth.post('/courses/create/',data=data)
    assert response.status_code == 201
    assert Course.objects.filter(title=data['title'],short_description=data['short_description']).exists()

@pytest.mark.django_db
def test_course_create_by_not_approved_teacher(unverif_teacher_with_auth,user_teacher_unapproved):
    data = {
        'title':'test title',
        'short_description':'test short description',
    }
    response = unverif_teacher_with_auth.post('/courses/create/', data=data)
    assert response.status_code == 403
    assert not Course.objects.filter(title=data['title'], short_description=data['short_description']).exists()


@pytest.mark.django_db
def test_get_course_info(student_with_auth,course):
    response = student_with_auth.get(f'/courses/{course['id']}/info/')
    assert response.status_code == 200
    assert response.json()['title'] == course['title']
    assert response.json()['short_description'] == course['short_description']
    assert response.json()['owner'] == course['owner']






@pytest.mark.django_db
def test_course_request_no_staff(student_with_auth, private_course, user_student):
    response = student_with_auth.post(f'/courses/{private_course.id}/request/')

    assert response.status_code == 201
    assert not CourseRoles.objects.filter(course_id=private_course.id, user=user_student).exists()
    assert response.json()['approved'] == False
    print('CourseJoinRequests:', [(r.id, r.course.id, r.user.id) for r in CourseJoinRequests.objects.all()])
    print('Test course:', private_course.id)
    print('Test user:', user_student.id)

    assert CourseJoinRequests.objects.filter(course=private_course,user=user_student).exists()



@pytest.mark.django_db
def test_course_request_staff(private_course,staff_with_auth,user_staff):

    response = staff_with_auth.post(f'/courses/{private_course.id}/request/')
    assert response.status_code == 200
    assert response.json()['approved'] == True
    assert CourseRoles.objects.filter(course=private_course, user=user_staff).exists()
    print('CourseJoinRequests:', [(r.id, r.course.id, r.user.id) for r in CourseJoinRequests.objects.all()])
    print('Test course:', private_course.id)
    print('Test user:', user_staff.id)
    assert CourseJoinRequests.objects.filter(course=private_course,user=user_staff,status='approved').exists()