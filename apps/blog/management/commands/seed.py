import random

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Comment, Post, Tag

fake = Faker()

SEED_PASSWORD = "SeedPassword123!"

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

CATEGORY_NAMES = [
    "Technology",
    "Programming",
    "Python",
    "Django",
    "Web Development",
    "Databases",
    "Artificial Intelligence",
    "Science",
]

TAG_NAMES = [
    "Python",
    "Django",
    "JavaScript",
    "HTML",
    "CSS",
    "Backend",
    "Frontend",
    "API",
    "REST",
    "Database",
    "SQL",
    "Programming",
    "Technology",
    "Tutorial",
    "Development",
    "Web",
    "Software",
    "Testing",
    "Security",
    "Education",
]

PUBLISHED_PERCENTAGE = 70
STAFF_PERCENTAGE = 10
MAX_TAGS_PER_POST = 5
MAX_SENTENCES_PER_COMMENT = 3


class Command(BaseCommand):
    help = "Fill the database with test data"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=DEFAULT_USERS)
        parser.add_argument("--posts", type=int, default=DEFAULT_POSTS)
        parser.add_argument("--comments", type=int, default=DEFAULT_COMMENTS)
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args, **options):
        users_count = options["users"]
        posts_count = options["posts"]
        comments_count = options["comments"]

        if min(users_count, posts_count, comments_count) < 0:
            raise CommandError("Counts cannot be negative.")

        if users_count == 0 and (posts_count > 0 or comments_count > 0):
            raise CommandError("Users are required to create posts and comments.")

        if options["clear"]:
            self.clear_data()

        User = get_user_model()

        users = User.objects.all()

        if users_count > 0:
            users = self.create_users(User, users_count)

        if posts_count > 0:
            categories = self.create_categories()
            tags = self.create_tags()
            posts = self.create_posts(users, categories, posts_count)
            self.assign_tags(posts, tags)

        published_posts = list(Post.objects.filter(status="published"))

        if comments_count > 0 and not published_posts:
            raise CommandError(
                "Cannot create comments because there are no published posts."
            )

        if comments_count > 0:
            self.create_comments(users, published_posts, comments_count)

        self.stdout.write(
            self.style.SUCCESS(
                "Seed completed successfully!\n"
                f"Users: {User.objects.count()}\n"
                f"Categories: {Category.objects.count()}\n"
                f"Tags: {Tag.objects.count()}\n"
                f"Posts: {Post.objects.count()}\n"
                f"Comments: {Comment.objects.count()}"
            )
        )

    def clear_data(self):
        User = get_user_model()

        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()

        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.WARNING("Existing data cleared."))

    def create_users(self, User, count):
        password = make_password(SEED_PASSWORD)
        users = []
        used_emails = set(User.objects.values_list("email", flat=True))

        for _ in range(count):
            email = fake.unique.email()

            while email in used_emails:
                email = fake.unique.email()

            used_emails.add(email)

            users.append(
                User(
                    email=email,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    password=password,
                    is_active=False,
                    is_staff=random.random() < STAFF_PERCENTAGE / 100,
                )
            )

        User.objects.bulk_create(users)
        return list(User.objects.filter(email__in=used_emails))

    def create_categories(self):
        existing_names = set(Category.objects.values_list("name", flat=True))

        categories = [
            Category(name=name, slug=slugify(name))
            for name in CATEGORY_NAMES
            if name not in existing_names
        ]

        Category.objects.bulk_create(categories)
        return list(Category.objects.all())

    def create_tags(self):
        existing_names = set(Tag.objects.values_list("name", flat=True))

        tags = [
            Tag(name=name, slug=slugify(name))
            for name in TAG_NAMES
            if name not in existing_names
        ]

        Tag.objects.bulk_create(tags)
        return list(Tag.objects.all())

    def create_posts(self, users, categories, count):
        posts = []
        used_slugs = set(Post.objects.values_list("slug", flat=True))

        for _ in range(count):
            title = fake.sentence(nb_words=6).rstrip(".")
            slug = slugify(title)

            while slug in used_slugs:
                slug = f"{slug}-{random.randint(1, 999999)}"

            used_slugs.add(slug)

            status = (
                "published" if random.random() < PUBLISHED_PERCENTAGE / 100 else "draft"
            )

            category = (
                random.choice(categories)
                if categories and random.random() >= 0.1
                else None
            )

            posts.append(
                Post(
                    author=random.choice(users),
                    title=title,
                    slug=slug,
                    body=fake.text(max_nb_chars=1000),
                    category=category,
                    status=status,
                )
            )

        Post.objects.bulk_create(posts)
        return list(Post.objects.filter(slug__in=used_slugs))

    def assign_tags(self, posts, tags):
        for post in posts:
            selected_tags = random.sample(
                tags,
                k=random.randint(0, min(MAX_TAGS_PER_POST, len(tags))),
            )
            post.tags.set(selected_tags)

    def create_comments(self, users, posts, count):
        comments = [
            Comment(
                post=random.choice(posts),
                author=random.choice(users),
                body=fake.paragraph(
                    nb_sentences=random.randint(
                        1,
                        MAX_SENTENCES_PER_COMMENT,
                    )
                ),
            )
            for _ in range(count)
        ]

        Comment.objects.bulk_create(comments)
