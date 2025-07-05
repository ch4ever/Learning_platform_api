from datetime import datetime

import uuid
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
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



@extend_schema(summary="test session start",
               parameters=[OpenApiParameter(name="pk", description="Test session start", location=OpenApiParameter.PATH, required=True)],
               responses={200: OpenApiResponse(description="Test session started successfully + uuid"),
                          400: OpenApiResponse(description="Maximum tries exceeded"),
                          406: OpenApiResponse(description="session already exists"),}
               )
class TestSessionCreateView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,StudentOrAbove)

    def post(self, request, pk=None):
        test = get_object_or_404(TestBlock, pk=pk)
        existed_sessions = TestSession.objects.filter(test_block=test, user=request.user)

        if existed_sessions.count() >= test.possible_retries:
            return Response({'detail':"You exceeded the maximum number of retries."}, status=status.HTTP_400_BAD_REQUEST)
        active_session = existed_sessions.filter(is_finished=False).first()
        if active_session:
            return Response({"detail":"You already have test session: ","uuid":str(active_session.uuid)},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        session= TestSession.objects.create(test_block=test, user=request.user, is_finished=False)

        test_duration = test.time_for_test
        finish_test.apply_async(args=[str(session.uuid)], countdown=test_duration.total_seconds())
        return Response({"detail":"Test session started", "uuid": session.uuid},status=status.HTTP_201_CREATED)


class TestSessionViewSet(viewsets.ViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, StudentOrAbove)

    @extend_schema(summary="Test questions list/1 by order",
                   parameters=[OpenApiParameter(name='pk',description='test uuid', required=True, location=OpenApiParameter.PATH, type=OpenApiTypes.STR),
                               OpenApiParameter(name='question', required=False, location=OpenApiParameter.QUERY, type=OpenApiTypes.INT)],
                   responses={200: OpenApiResponse(response={'oneOf': [TestWithSelectedAnswersSerializer, SessionTestSerializer]})}
                   )
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

    @extend_schema(summary="Answer questions all/1 by order",
                   parameters=[OpenApiParameter(name='uuid', required=True, location=OpenApiParameter.PATH, type=OpenApiTypes.STR),
                               OpenApiParameter(name='question', required=False, location=OpenApiParameter.QUERY, type=OpenApiTypes.INT)],
                   responses={200: OpenApiResponse(response={'oneOf': [TestWithSelectedAnswersSerializer, SessionTestSerializer]}),
                              404: OpenApiResponse('Question/test not found')}
                   )
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


@extend_schema(summary="Test Submit",
               parameters=[OpenApiParameter(name="pk", description="test uuid.",
                                            required=True,location=OpenApiParameter.PATH, type=OpenApiTypes.STR),],
               responses={200: OpenApiResponse( response=OpenApiTypes.OBJECT,description="Test result with total score",),
                          404: OpenApiResponse(description="Not found.")},
               )
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

        return Response({"score":score}, status=status.HTTP_200_OK)
