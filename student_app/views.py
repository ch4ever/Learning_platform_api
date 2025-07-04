from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from Learning_platform.tasks import finish_test
from courses_app.models import TestBlock, TestQuestions, TestAnswers
from courses_app.utils import check_test_results
from main.permissions import StudentOrAbove
from student_app.models import TestSession, TestUserAnswers
from student_app.serializers import SessionTestSerializer, TestWithSelectedAnswersSerializer, \
    TestAnswersValidationSerializer


"Session start"
#TODO rebuild mb for  block id --> search test?
class TestSessionCreateView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,StudentOrAbove)

    def post(self, request, pk=None):
        test = get_object_or_404(TestBlock, pk=pk)
        session, created = TestSession.objects.get_or_create(test_block=test, user=request.user, is_finished=False)

        if not created:
            return Response({"detail":"You already have test session"},status=status.HTTP_204_NO_CONTENT)
        else:
            test_duration = test.time_for_test
            finish_test.apply_async(args=[str(session.uuid)], countdown=test_duration.total_seconds())
            return Response({"detail":"Test session started","uuid": session.uuid},status=status.HTTP_201_CREATED)

"""session questions list/1 by order"""
class TestSessionViewSet(viewsets.ViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, StudentOrAbove)

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        session = get_object_or_404(TestSession, pk=pk)
        order = request.query_params.get('question', None)
        if not session.is_finished:
            if order:
                question = get_object_or_404(TestQuestions, order=int(order) ,test_block=session.test_block)
                serializer = TestWithSelectedAnswersSerializer(question, read_only=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                serializer = SessionTestSerializer(session, read_only=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"detail":f"This test session has been finished, score:{session.summary_score}"},status=status.HTTP_200_OK)

    #TODO mb rebuild for order
    def post(self, request, pk=None):
        session = get_object_or_404(TestSession, pk=pk)
        question = request.query_params.get("question")
        if question:
            question = get_object_or_404(TestQuestions, order=question, test_block=session.test_block)
            serializer = TestAnswersValidationSerializer(data=request.data, context={"question":question })
            serializer.is_valid(raise_exception=True)
            selected_answers = serializer.validated_data["selected_answers"]
            TestUserAnswers.objects.filter(question=question, session=session).delete()
            if selected_answers:
                answers = TestAnswers.objects.filter(id__in=selected_answers, test=question)
                new = TestUserAnswers.objects.create(question=question, session=session)
                #TODO check
                new.selected_answers.set(answers)


            output_serializer = TestWithSelectedAnswersSerializer(question, context={"session":session})
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        else:
            answers = request.data.get("answers",[])

            for new_answer in answers:
                question_id = new_answer.get("question")
                answers_id = new_answer.get("selected_answer",[])

                question = get_object_or_404(TestQuestions, id=question_id,test_block=session.test_block)

                serializer = TestAnswersValidationSerializer(data={"selected_answers": answers_id}, context={"question":question})
                serializer.is_valid(raise_exception=True)

                TestUserAnswers.objects.filter(question=question, session=session).delete()

                if answers_id:
                    answers_ = TestAnswers.objects.filter(id__in=answers_id, test=question)
                    new = TestUserAnswers.objects.create(question=question, session=session)
                    new.selected_answers.set(answers_)
            output_serializer = SessionTestSerializer(session,read_only=True)
            return Response(output_serializer.data, status=status.HTTP_202_ACCEPTED)



class TestSubmitView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, StudentOrAbove)

    def post(self, request, pk=None):
        user = request.user
        session = get_object_or_404(TestSession, pk=pk)

        if session.user != user:
            raise PermissionDenied("You don't have permission to submit this session")
        if session.is_finished:
            raise ValidationError(f"Test already finished at {session.finished_at}")

        questions = session.test_block.questions.all()
        score = check_test_results(questions, session)
        with transaction.atomic():
            session.is_finished = True
            session.finished_at = timezone.now()
            session.summary_score = score
            session.save()
        #TODO serializer for this shit
        return Response({"score":score}, status=status.HTTP_200_OK)
