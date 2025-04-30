from rest_framework import serializers

from courses_app.models import Course, CourseSections, SectionContent


class CourseSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields= ('id','owner','title','short_description','created_at','users',)

    def get_users(self, obj):
        return [{
            'id': u.user.id,
            'username': u.user.username,
            'role': u.course_role
        } for u in obj.course_roles.select_related('user') ]

class SectionContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = SectionContent
        fields = ('title','content')

class CourseSectionsSerializer(serializers.ModelSerializer):
    section_content = SectionContentSerializer(many=True, read_only=True)
    class Meta:
        model = CourseSections
        fields = ('order','section_name','section_content')


