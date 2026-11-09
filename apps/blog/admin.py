from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import WysiwygWidget

from .models import Category, Comment, Post, PostStatus, Tag


class PostCategoryInline(TabularInline):
    model = Post
    extra = 0
    fields = ("title", "author", "status", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    inlines = (PostCategoryInline,)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(posts_count=Count("post", distinct=True))
        )

    @admin.display(description="Posts", ordering="posts_count")
    def posts_count(self, obj):
        return obj.posts_count


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(posts_count=Count("post", distinct=True))
        )

    @admin.display(description="Posts", ordering="posts_count")
    def posts_count(self, obj):
        return obj.posts_count


class CommentInline(TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    show_change_link = True
    per_page = 10


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = (
        "title",
        "author",
        "status_badge",
        "category",
        "comments_count",
        "created_at",
    )

    list_filter = (
        "status",
        "category",
        "tags",
        ("created_at", admin.DateFieldListFilter),
    )

    search_fields = (
        "title",
        "body",
        "author__email",
        "category__name",
    )

    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("author", "category")
    inlines = (CommentInline,)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Content",
            {
                "fields": ("title", "slug", "body"),
            },
        ),
        (
            "Classification",
            {
                "fields": ("category", "tags", "status"),
            },
        ),
        (
            "Meta",
            {
                "fields": ("author", "created_at", "updated_at"),
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {"widget": WysiwygWidget},
    }

    actions = (
        "publish_posts",
        "move_to_drafts",
        "publish_all_drafts",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(comments_count=Count("comment", distinct=True))
        )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        if obj.status == PostStatus.PUBLISHED:
            return format_html(
                '<span style="color:#16a34a;font-weight:600;">{}</span>',
                "● Published",
            )

        return format_html(
            '<span style="color:#d97706;font-weight:600;">{}</span>',
            "● Draft",
        )

    @admin.display(description="Comments", ordering="comments_count")
    def comments_count(self, obj):
        return obj.comments_count

    @admin.action(description="Publish selected posts")
    def publish_posts(self, request, queryset):
        updated = queryset.update(status=PostStatus.PUBLISHED)

        self.message_user(
            request,
            f"{updated} posts published successfully.",
        )

    @admin.action(description="Move selected posts to drafts")
    def move_to_drafts(self, request, queryset):
        updated = queryset.update(status=PostStatus.DRAFT)

        self.message_user(
            request,
            f"{updated} posts moved to drafts.",
        )

    @admin.action(description="Publish all drafts")
    def publish_all_drafts(self, request, queryset):
        updated = Post.objects.filter(status=PostStatus.DRAFT).update(
            status=PostStatus.PUBLISHED
        )

        self.message_user(
            request,
            f"{updated} draft posts published successfully.",
        )


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = (
        "post",
        "author",
        "short_body",
        "created_at",
    )

    list_filter = (("created_at", admin.DateFieldListFilter),)

    search_fields = (
        "body",
        "author__email",
        "post__title",
    )

    autocomplete_fields = ("post", "author")
    list_select_related = ("post", "author")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    @admin.display(description="Comment")
    def short_body(self, obj):
        if len(obj.body) > 60:
            return f"{obj.body[:60]}..."

        return obj.body
