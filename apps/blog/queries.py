from datetime import date, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import (
    Avg,
    Case,
    Count,
    Exists,
    ExpressionWrapper,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.blog.models import Category, Comment, Post, PostStatus, Tag

User = get_user_model()

POSTS_PER_PAGE = 10
NEWEST_POSTS_LIMIT = 5
TOP_AUTHORS_LIMIT = 5
FEED_LIMIT = 50
TAGGED_POSTS_LIMIT = 20

EDITED_POSTS_HOURS = 1
AVERAGE_DECIMAL_PLACES = 2

POPULARITY_HOT_LIMIT = 10
POPULARITY_NORMAL_LIMIT = 3

UNCATEGORIZED = "Uncategorized"
HOT = "hot"
NORMAL = "normal"
QUIET = "quiet"


# 1–10. Basic queries


def categories_by_name():
    """Return categories ordered by name."""
    return Category.objects.order_by("name")


def published_posts():
    """Return published posts, newest first."""
    return Post.objects.filter(status=PostStatus.PUBLISHED).order_by("-created_at")


def newest_published_posts():
    """Return the five newest published posts."""
    return published_posts()[:NEWEST_POSTS_LIMIT]


def post_by_slug(slug: str) -> Post | None:
    """Find a post by its slug."""
    return Post.objects.filter(slug=slug).first()


def active_users_count() -> int:
    """Count active non-staff users."""
    return User.objects.filter(
        is_active=True,
        is_staff=False,
    ).count()


def has_drafts() -> bool:
    """Check whether draft posts exist."""
    return Post.objects.filter(status=PostStatus.DRAFT).exists()


def published_posts_page(page: int):
    """Return one page of published posts."""
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE

    return published_posts()[start:end]


def posts_with_word_in_title(word: str):
    """Find posts containing a word in the title."""
    return Post.objects.filter(title__icontains=word)


def users_with_email_domain(domain: str):
    """Find users by email domain."""
    return User.objects.filter(email__iendswith=f"@{domain}")


def posts_without_category():
    """Return posts without a category."""
    return Post.objects.filter(category__isnull=True)


# 11–20. Filtering and relations


def categories_by_slugs(slugs: list[str]):
    """Find categories by their slugs."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int):
    """Find posts created in a specific month."""
    return Post.objects.filter(
        created_at__year=year,
        created_at__month=month,
    )


def posts_last_days(days: int):
    """Find posts created during the last number of days."""
    return Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=days))


def posts_between(start: date, end: date):
    """Find posts created between two dates."""
    return Post.objects.filter(created_at__date__range=(start, end))


def author_published_posts(email: str):
    """Find published posts by author email."""
    return Post.objects.filter(
        author__email__iexact=email,
        status=PostStatus.PUBLISHED,
    )


def posts_with_tag(tag_slug: str):
    """Find posts with a specific tag."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str):
    """Find comments on posts in a category."""
    return Comment.objects.filter(post__category__slug=category_slug)


def users_with_published_posts():
    """Find users who have published posts."""
    return User.objects.filter(post__status=PostStatus.PUBLISHED).distinct()


def posts_without_tags():
    """Find posts without tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments():
    """Find users who have never commented."""
    return User.objects.filter(comment__isnull=True)


# 21–30. Complex queries and aggregation


def posts_with_both_tags(
    first_slug: str,
    second_slug: str,
):
    """Find posts containing both specified tags."""
    return Post.objects.filter(tags__slug=first_slug).filter(tags__slug=second_slug)


def search_posts(text: str):
    """Search posts by title or body."""
    return Post.objects.filter(Q(title__icontains=text) | Q(body__icontains=text))


def published_posts_missing_info():
    """Find published posts without a category or tags."""
    return (
        Post.objects.filter(status=PostStatus.PUBLISHED)
        .filter(Q(category__isnull=True) | Q(tags__isnull=True))
        .distinct()
    )


def edited_posts():
    """Find posts edited more than one hour after creation."""
    return Post.objects.annotate(
        edit_limit=ExpressionWrapper(
            F("created_at") + timedelta(hours=EDITED_POSTS_HOURS),
            output_field=Post._meta.get_field("created_at"),
        )
    ).filter(updated_at__gt=F("edit_limit"))


def comments_by_post_author():
    """Find comments written by the post author."""
    return Comment.objects.filter(author_id=F("post__author_id"))


def comments_before_post():
    """Find comments created before their posts."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))


def published_authors_emails() -> list[str]:
    """Return unique emails of published post authors."""
    return list(
        User.objects.filter(post__status=PostStatus.PUBLISHED)
        .values_list(
            "email",
            flat=True,
        )
        .distinct()
        .order_by("email")
    )


def published_posts_overview() -> list[dict[str, Any]]:
    """Return a short overview of published posts."""
    return list(
        Post.objects.filter(status=PostStatus.PUBLISHED)
        .annotate(
            author_email=F("author__email"),
            category_name=Coalesce(
                "category__name",
                Value(UNCATEGORIZED),
            ),
        )
        .values(
            "title",
            "author_email",
            "category_name",
        )
    )


def posts_stats() -> dict[str, Any]:
    """Return general post statistics."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count(
            "id",
            filter=Q(status=PostStatus.PUBLISHED),
        ),
        drafts=Count(
            "id",
            filter=Q(status=PostStatus.DRAFT),
        ),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )


def average_comments_per_post() -> float:
    """Calculate average comments per published post."""
    result = (
        Post.objects.filter(status=PostStatus.PUBLISHED)
        .annotate(comment_count=Count("comment"))
        .aggregate(average=Avg("comment_count"))
    )

    return round(
        result["average"] or 0.0,
        AVERAGE_DECIMAL_PLACES,
    )


# 31–40. Advanced ORM queries


def categories_with_post_count():
    """Return categories with total post counts."""
    return Category.objects.annotate(post_count=Count("post")).order_by(
        "-post_count", "name"
    )


def categories_with_published_count():
    """Return categories with published post counts."""
    return Category.objects.annotate(
        published_count=Count(
            "post",
            filter=Q(post__status=PostStatus.PUBLISHED),
        )
    ).order_by("-published_count", "name")


def top_authors():
    """Return five authors with the most published posts."""
    return (
        User.objects.annotate(
            published_count=Count(
                "post",
                filter=Q(post__status=PostStatus.PUBLISHED),
            )
        )
        .filter(published_count__gt=0)
        .order_by(
            "-published_count",
            "email",
        )[:TOP_AUTHORS_LIMIT]
    )


def popular_tags(min_posts: int):
    """Return tags used in at least the specified number of posts."""
    return (
        Tag.objects.annotate(post_count=Count("post"))
        .filter(post_count__gte=min_posts)
        .order_by("-post_count", "name")
    )


def posts_per_status():
    """Return the number of posts for each status."""
    return list(
        Post.objects.values("status").annotate(count=Count("id")).order_by("status")
    )


def users_activity():
    """Return users with their post and comment counts."""
    return User.objects.annotate(
        post_count=Count("post", distinct=True),
        comment_count=Count("comment", distinct=True),
    )


def search_users_by_full_name(text: str):
    """Search users by their combined first and last name."""
    return User.objects.annotate(
        full_name=Concat(
            F("first_name"),
            Value(" "),
            F("last_name"),
        )
    ).filter(full_name__icontains=text)


def published_posts_per_month():
    """Return monthly published post counts."""
    return (
        Post.objects.filter(status=PostStatus.PUBLISHED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )


def posts_with_popularity():
    """Return posts with comment counts and popularity levels."""
    return Post.objects.annotate(comment_count=Count("comment")).annotate(
        popularity=Case(
            When(
                comment_count__gte=POPULARITY_HOT_LIMIT,
                then=Value(HOT),
            ),
            When(
                comment_count__gte=POPULARITY_NORMAL_LIMIT,
                then=Value(NORMAL),
            ),
            default=Value(QUIET),
        )
    )


def get_or_create_tag(name: str) -> Tag:
    """Get a tag by slug or create it."""
    slug = slugify(name)

    tag, _ = Tag.objects.get_or_create(
        slug=slug,
        defaults={"name": name},
    )

    return tag


# 41–44. Data-changing queries


def publish_old_drafts(days: int) -> int:
    """Publish drafts older than the specified number of days."""
    threshold = timezone.now() - timedelta(days=days)

    return Post.objects.filter(
        status=PostStatus.DRAFT,
        created_at__lt=threshold,
    ).update(
        status=PostStatus.PUBLISHED,
        updated_at=timezone.now(),
    )


def tag_category_posts(
    category_slug: str,
    tag_slug: str,
) -> int:
    """Add a tag to all posts in a category."""
    posts = list(Post.objects.filter(category__slug=category_slug))

    tag = Tag.objects.get(slug=tag_slug)
    tag.post_set.add(*posts)

    return len(posts)


def merge_categories(
    source_slug: str,
    target_slug: str,
) -> int:
    """Move posts from one category to another and delete the source."""
    source = Category.objects.get(slug=source_slug)
    target = Category.objects.get(slug=target_slug)

    moved_count = Post.objects.filter(category=source).update(category=target)

    source.delete()

    return moved_count


def delete_inactive_users_comments() -> int:
    """Delete comments written by inactive users."""
    deleted_count, _ = Comment.objects.filter(author__is_active=False).delete()

    return deleted_count


# 45–50. Query optimization


def published_feed() -> list[str]:
    """Return the latest published posts as formatted strings."""
    posts = (
        Post.objects.filter(status=PostStatus.PUBLISHED)
        .select_related(
            "author",
            "category",
        )
        .order_by("-created_at")[:FEED_LIMIT]
    )

    return [
        (
            f"{post.title} | "
            f"{post.author.email} | "
            f"{post.category.name if post.category else UNCATEGORIZED}"
        )
        for post in posts
    ]


def newest_posts_with_tags() -> list[str]:
    """Return the latest posts with their tag names."""
    posts = Post.objects.prefetch_related("tags").order_by("-created_at")[
        :TAGGED_POSTS_LIMIT
    ]

    return [
        f"{post.title}: {', '.join(sorted(tag.name for tag in post.tags.all()))}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    """Return categories with their published post titles."""
    posts = Post.objects.filter(status=PostStatus.PUBLISHED).order_by("-created_at")

    categories = Category.objects.prefetch_related(
        Prefetch(
            "post_set",
            queryset=posts,
            to_attr="published_posts",
        )
    )

    return {
        category.name: [post.title for post in category.published_posts]
        for category in categories
    }


def posts_with_last_comment():
    """Return published posts with their latest comment body."""
    last_comment = (
        Comment.objects.filter(post=OuterRef("pk"))
        .order_by("-created_at")
        .values("body")[:1]
    )

    return Post.objects.filter(status=PostStatus.PUBLISHED).annotate(
        last_comment=Subquery(last_comment)
    )


def posts_with_staff_comments():
    """Return posts having at least one staff comment."""
    staff_comments = Comment.objects.filter(
        post=OuterRef("pk"),
        author__is_staff=True,
    )

    return Post.objects.annotate(has_staff_comment=Exists(staff_comments)).filter(
        has_staff_comment=True
    )


def users_with_draft_as_latest_post():
    """Return users whose latest post is a draft."""
    latest_post = (
        Post.objects.filter(author=OuterRef("pk"))
        .order_by(
            "-created_at",
            "-pk",
        )
        .values("status")[:1]
    )

    return User.objects.annotate(latest_post_status=Subquery(latest_post)).filter(
        latest_post_status=PostStatus.DRAFT
    )


# Query registry

QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}
