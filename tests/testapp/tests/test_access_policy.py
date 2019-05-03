from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_access_policy import AccessPolicy
from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet


class FakeRequest(object):
    def __init__(self, user: User):
        self.user = user


class AccessPolicyTests(TestCase):
    def setUp(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_get_invoked_action_from_function_based_view(self):
        @api_view(["GET"])
        def my_view(request):
            return ""

        policy = AccessPolicy()
        view_instance = my_view.cls()

        result = policy._get_invoked_action(view_instance)
        self.assertEqual(result, "my_view")

    def test_get_invoked_action_from_class_based_view(self):
        class UserViewSet(ModelViewSet):
            pass

        policy = AccessPolicy()
        view_instance = UserViewSet()
        view_instance.action = "create"

        result = policy._get_invoked_action(view_instance)
        self.assertEqual(result, "create")

    def test_get_user_groups(self):
        group1 = Group.objects.create(name="admin")
        group2 = Group.objects.create(name="ceo")
        user = User.objects.create(username="mr user")

        user.groups.add(group1, group2)

        policy = AccessPolicy()
        result = sorted(policy.get_user_groups(user))

        self.assertEqual(result, ["admin", "ceo"])

    def test_normalize_statements(self):
        policy = AccessPolicy()

        result = policy._normalize_statements(
            [
                {
                    "principal": "group:admin",
                    "action": "delete",
                    "condition": "is_nice_day",
                }
            ]
        )

        self.assertEqual(
            result,
            [
                {
                    "principal": ["group:admin"],
                    "action": ["delete"],
                    "condition": ["is_nice_day"],
                }
            ],
        )

    def test_get_statements_matching_principal(self):
        cooks = Group.objects.create(name="cooks")
        user = User.objects.create(id=5)
        user.groups.add(cooks)

        statements = [
            {"principal": ["id:5"], "action": ["create"]},
            {"principal": ["group:dev"], "action": ["delete"]},
            {"principal": ["group:cooks"], "action": ["do_something"]},
            {"principal": ["*"], "action": ["*"]},
            {"principal": ["id:79"], "action": ["vote"]},
        ]

        policy = AccessPolicy()

        result = policy._get_statements_matching_principal(
            FakeRequest(user), statements
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["action"], ["create"])
        self.assertEqual(result[1]["action"], ["do_something"])
        self.assertEqual(result[2]["action"], ["*"])

    def test_get_statements_matching_action(self):
        pass
