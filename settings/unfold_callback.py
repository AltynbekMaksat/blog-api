from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count

from apps.blog.models import Category, Comment, Post, PostStatus


def environment_callback(request):
    environment = getattr(settings, "BLOG_ENV_ID", "Development")

    if str(environment).lower() == "production":
        return ["Production", "danger"]

    return ["Development", "success"]


def dashboard_callback(request, context):
    User = get_user_model()

    total_users = User.objects.count()
    total_posts = Post.objects.count()
    total_comments = Comment.objects.count()
    total_categories = Category.objects.count()

    published_posts = Post.objects.filter(status=PostStatus.PUBLISHED).count()

    draft_posts = Post.objects.filter(status=PostStatus.DRAFT).count()

    published_percent = round(published_posts / total_posts * 100) if total_posts else 0

    draft_percent = round(draft_posts / total_posts * 100) if total_posts else 0

    stats = [
        ("Total Users", total_users),
        ("Total Posts", total_posts),
        ("Total Comments", total_comments),
        ("Total Categories", total_categories),
    ]

    context.update(
        {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_categories": total_categories,
            "published_posts": published_posts,
            "draft_posts": draft_posts,
            "published_percent": published_percent,
            "draft_percent": draft_percent,
            "stats": stats,
            "posts_by_category": (
                Category.objects.annotate(
                    posts_count=Count("post", distinct=True)
                ).order_by("-posts_count")
            ),
            "top_authors": (
                User.objects.annotate(posts_count=Count("post", distinct=True))
                .filter(posts_count__gt=0)
                .order_by("-posts_count")[:5]
            ),
        }
    )

    return context


def sidebar_badge(request):
    return Post.objects.filter(status=PostStatus.DRAFT).count()


def superuser_permission(request):
    return request.user.is_superuser
