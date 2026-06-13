from __future__ import annotations

from rest_framework import serializers


class RunReportSerializer(serializers.Serializer):
    report_id = serializers.IntegerField(min_value=1)
    filters = serializers.DictField(required=False, default=dict)
    sort_by = serializers.CharField(required=False, allow_blank=True, default="")
    sort_direction = serializers.ChoiceField(choices=["asc", "desc"], required=False, default="asc")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)

