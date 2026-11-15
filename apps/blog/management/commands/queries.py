from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.blog.models import Category, Post, Tag
from apps.blog.queries import QUERIES

DEFAULT_QUERIES = [number for number in QUERIES if number not in range(40, 45)]

QUERY_ARGUMENTS = {
    3: (),
    5: (),
    6: (),
    13: (30,),
    24: (),
    29: (),
    30: (),
    34: (1,),
    40: ("Python",),
    41: (365,),
    44: (),
    45: (),
    46: (),
    47: (),
    48: (),
    49: (),
    50: (),
}


class Command(BaseCommand):
    help = "Run blog ORM queries."

    def add_arguments(self, parser):

        parser.add_argument(
            "--number",
            type=int,
            help="Run one query by its number.",
        )

        parser.add_argument(
            "--sql",
            action="store_true",
            help="Display SQL queries.",
        )

    def handle(self, *args, **options):

        number = options["number"]

        if number is not None:
            if number not in QUERIES:
                raise CommandError(f"Query number {number} does not exist.")

            numbers = [number]

        else:
            numbers = DEFAULT_QUERIES

        for query_number in numbers:
            self.run_query(
                query_number,
                options["sql"],
            )

    def get_arguments(self, number):

        arguments = QUERY_ARGUMENTS.get(number, ())

        post = Post.objects.order_by("pk").first()

        category = Category.objects.order_by("pk").first()

        tag = Tag.objects.order_by("pk").first()

        if number == 4:
            return (post.slug,) if post else ("",)

        if number == 7:
            return (1,)

        if number == 8:
            return (post.title.split()[0],) if post else ("",)

        if number == 9:
            user = post.author if post else None

            domain = user.email.split("@")[-1] if user else "example.com"

            return (domain,)

        if number == 11:
            return ([category.slug],) if category else ([],)

        if number == 12:
            today = timezone.localdate()

            return (today.year, today.month)

        if number == 14:
            today = timezone.localdate()

            return (today - timedelta(days=365), today)

        if number == 15:
            return (post.author.email,) if post else ("",)

        if number == 16:
            return (tag.slug,) if tag else ("",)

        if number == 17:
            return (category.slug,) if category else ("",)

        if number == 21:
            tags = list(Tag.objects.values_list("slug", flat=True)[:2])

            first = tags[0] if tags else ""

            second = tags[1] if len(tags) > 1 else first

            return (first, second)

        if number == 22:
            word = post.title.split()[0] if post else ""

            return (word,)

        if number == 37:
            return (post.author.first_name,) if post else ("",)

        if number == 42:
            return (category.slug, tag.slug) if category and tag else ("", "")

        if number == 43:
            categories = list(Category.objects.values_list("slug", flat=True)[:2])

            if len(categories) < 2:
                raise CommandError("Query 43 requires at least two categories.")

            return (categories[0], categories[1])

        return arguments

    def run_query(self, number, show_sql):

        function = QUERIES[number]

        arguments = self.get_arguments(number)

        self.stdout.write(
            self.style.MIGRATE_HEADING(f"\nQuery {number}: {function.__name__}")
        )

        with CaptureQueriesContext(connection) as queries:
            result = function(*arguments)

            if hasattr(result, "query"):
                result = list(result)

        self.stdout.write(f"SQL queries: {len(queries)}")

        if show_sql:
            for query in queries:
                self.stdout.write(query["sql"])

        self.display_result(result)

    def display_result(self, result):

        if isinstance(result, list):
            for item in result[:5]:
                self.stdout.write(str(item))

            self.stdout.write(f"Total results: {len(result)}")

        elif isinstance(result, dict):
            self.stdout.write(str(result))

        else:
            self.stdout.write(str(result))
