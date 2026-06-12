from rest_framework import serializers


class TargetSelectorSerializer(serializers.Serializer):
    menu = serializers.CharField(max_length=120, required=False)
    form = serializers.CharField(max_length=100, required=False)

    def validate(self, attrs):
        menu_name = attrs.get("menu")
        form_name = attrs.get("form")
        if bool(menu_name) == bool(form_name):
            raise serializers.ValidationError("Exactly one of 'menu' or 'form' must be provided.")
        return attrs


class InsertSerializer(TargetSelectorSerializer):
    data = serializers.DictField()


class UpdateSerializer(TargetSelectorSerializer):
    data = serializers.DictField()


class DeleteSerializer(TargetSelectorSerializer):
    data = serializers.DictField()


class DetailSerializer(TargetSelectorSerializer):
    id = serializers.IntegerField(min_value=1)


class ListSerializer(TargetSelectorSerializer):
    limit = serializers.IntegerField(min_value=1, max_value=1000, default=50)
    offset = serializers.IntegerField(min_value=0, default=0)
    sort_by = serializers.CharField(max_length=100, default="id")
    sort_direction = serializers.ChoiceField(choices=["asc", "desc"], default="asc")
    filters = serializers.DictField(required=False)


class ErrorDetailSerializer(serializers.Serializer):
    field = serializers.CharField(required=False)
    message = serializers.CharField()


class ErrorEnvelopeSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    error = ErrorDetailSerializer()


class GenericSuccessEnvelopeSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = serializers.DictField()


class GenericListDataSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    items = serializers.ListField(child=serializers.DictField())


class GenericListSuccessEnvelopeSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    data = GenericListDataSerializer()


class FormSchemaFieldSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    required = serializers.BooleanField()
    unique = serializers.BooleanField()
    lookup_id = serializers.IntegerField(required=False, allow_null=True)
    foreign_key_table = serializers.CharField(required=False, allow_blank=True)
    foreign_key_field = serializers.CharField(required=False, allow_blank=True)


class FormSchemaResponseSerializer(serializers.Serializer):
    form = serializers.CharField()
    table = serializers.CharField()
    fields = FormSchemaFieldSerializer(many=True)


class DataOptionsSerializer(serializers.Serializer):
    table = serializers.CharField(max_length=100, required=False)
    form = serializers.CharField(max_length=100, required=False)
    query = serializers.CharField(max_length=255, required=False, allow_blank=True)
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False)
    limit = serializers.IntegerField(min_value=1, max_value=200, default=50)

    def validate(self, attrs):
        has_table = bool(attrs.get("table"))
        has_form = bool(attrs.get("form"))
        if has_table == has_form:
            raise serializers.ValidationError("Exactly one of 'table' or 'form' must be provided.")
        return attrs


