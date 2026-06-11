from django.urls import path

from apps.forms.api.views import FormSchemaAPIView

urlpatterns = [
    path("<str:form_name>/schema", FormSchemaAPIView.as_view(), name="form-runtime-schema"),
]

