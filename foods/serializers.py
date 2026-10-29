from rest_framework import serializers

from .models import Food

MACRO_FIELDS = ('cal', 'fat', 'car', 'pro')


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = ('id', 'name', 'cal', 'fat', 'car', 'pro', 'serving')

    def validate_name(self, value):
        # Submissions arrive unauthenticated, so reject blank/whitespace names
        # before they reach the approval queue. (max_length is enforced by the
        # model field.)
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Name must not be blank.")
        return name

    def validate(self, attrs):
        negative = [f for f in MACRO_FIELDS
                    if attrs.get(f) is not None and attrs[f] < 0]
        if negative:
            raise serializers.ValidationError(
                {f: "Must not be negative." for f in negative}
            )
        return attrs
