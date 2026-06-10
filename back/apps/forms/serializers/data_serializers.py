from rest_framework import serializers


class InsertSerializer(serializers.Serializer):
    table = serializers.CharField(max_length=100)
    data = serializers.DictField()


class UpdateSerializer(serializers.Serializer):
    table = serializers.CharField(max_length=100)
    data = serializers.DictField()


class DeleteSerializer(serializers.Serializer):
    table = serializers.CharField(max_length=100)
    data = serializers.DictField()


class DetailSerializer(serializers.Serializer):
    table = serializers.CharField(max_length=100)
    id = serializers.IntegerField(min_value=1)


class ListSerializer(serializers.Serializer):
    table = serializers.CharField(max_length=100)
    limit = serializers.IntegerField(min_value=1, max_value=1000, default=50)
    offset = serializers.IntegerField(min_value=0, default=0)
    sort_by = serializers.CharField(max_length=100, default="id")
    sort_direction = serializers.ChoiceField(choices=["asc", "desc"], default="asc")
    filters = serializers.DictField(required=False)

