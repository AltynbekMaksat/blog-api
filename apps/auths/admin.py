from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = (
        "user_header",
        "active_status",
        "staff_status",
        "posts_count",
    )

    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined", "posts_count")

    fieldsets = (
        (
            "Personal information",
            {
                "fields": ("email", "first_name", "last_name"),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "fields": ("last_login", "date_joined"),
            },
        ),
    )

    add_fieldsets = (
        (
            "Create user",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    actions = ("activate_users", "deactivate_users")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(total_posts=Count("post", distinct=True))
        )

    @admin.display(description="User")
    def user_header(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip() or obj.email
        return format_html(
            "<strong>{}</strong><br><small>{}</small>",
            full_name,
            obj.email,
        )

    @admin.display(description="Active")
    def active_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #16a34a;">{}</span>',
                "● Active",
            )

        return format_html(
            '<span style="color: #dc2626;">{}</span>',
            "● Inactive",
        )

    @admin.display(description="Staff")
    def staff_status(self, obj):
        return "Yes" if obj.is_staff else "No"

    @admin.display(description="Posts", ordering="total_posts")
    def posts_count(self, obj):
        return obj.total_posts

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
