import json

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    AIContentPurchase,
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
    AIToolRecommendation,
)
from .services import (
    AIAccessDenied,
    AIInstructionModerationService,
    AIServiceError,
    AIToolRecommendationModerationService,
)


class PrettyJSONWidget(forms.Textarea):
    """Показывает JSON с отступами в расширенном редакторе."""

    def format_value(self, value):
        if value in (None, ""):
            return ""
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                return value
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "part",
        "request_type",
        "tokens_used",
        "created_at",
    )
    list_filter = ("request_type", "created_at")
    search_fields = (
        "user__email",
        "prompt",
        "response",
        "part__name",
        "part__original_number",
    )
    autocomplete_fields = ("user", "part")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(AIContentPurchase)
class AIContentPurchaseAdmin(admin.ModelAdmin):
    """Аудит приобретённого пользователями AI-контента."""

    list_display = (
        "id",
        "user",
        "content_type",
        "part",
        "instruction",
        "source",
        "subscription",
        "purchased_at",
    )
    list_filter = ("content_type", "source", "purchased_at")
    search_fields = (
        "user__email",
        "content_key",
        "part__name",
        "part__original_number",
        "instruction__title",
    )
    autocomplete_fields = (
        "user",
        "subscription",
        "part",
        "instruction",
        "source_request",
    )
    readonly_fields = (
        "user",
        "subscription",
        "content_type",
        "content_key",
        "part",
        "instruction",
        "source_request",
        "source",
        "purchased_at",
        "last_accessed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return bool(getattr(request.user, "is_superuser", False))


class ModerationForm(forms.Form):
    moderation_note = forms.CharField(
        required=False,
        label="Комментарий модератора",
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": (
                    "Укажите результаты проверки. "
                    "Для отклонения причина обязательна."
                ),
            }
        ),
    )
    rejected_error = "Укажите причину отклонения."

    def __init__(self, *args, require_note=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.require_note = require_note

    def clean_moderation_note(self):
        note = self.cleaned_data["moderation_note"].strip()
        if self.require_note and not note:
            raise forms.ValidationError(self.rejected_error)
        return note


class InstructionModerationForm(ModerationForm):
    rejected_error = "Укажите причину отклонения инструкции."


class ToolModerationForm(ModerationForm):
    rejected_error = (
        "Укажите причину отклонения рекомендации инструментов."
    )


class ModerationAdminMixin:
    moderation_form_class = ModerationForm
    moderation_url_name = ""
    moderation_template = ""
    generated_content_field = "generated_content"

    @staticmethod
    def _is_moderator_only(request):
        user = request.user
        return bool(
            getattr(user, "is_authenticated", False)
            and getattr(user, "role", "") == "moderator"
            and not getattr(user, "can_administrate", False)
        )

    def has_module_permission(self, request):
        return bool(
            getattr(request.user, "can_moderate", False)
            or super().has_module_permission(request)
        )

    def has_view_permission(self, request, obj=None):
        return bool(
            getattr(request.user, "can_moderate", False)
            or super().has_view_permission(request, obj)
        )

    def has_change_permission(self, request, obj=None):
        return bool(
            getattr(request.user, "can_moderate", False)
            or super().has_change_permission(request, obj)
        )

    def has_add_permission(self, request):
        if self._is_moderator_only(request):
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        if self._is_moderator_only(request):
            return False
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if self._is_moderator_only(request):
            readonly.extend(
                field.name
                for field in self.model._meta.concrete_fields
            )
        return tuple(dict.fromkeys(readonly))

    def get_urls(self):
        return [
            path(
                "<path:object_id>/moderate/<str:decision>/",
                self.admin_site.admin_view(self.moderate_object),
                name=self.moderation_url_name,
            )
        ] + super().get_urls()

    @admin.display(description="Модерация")
    def moderation_actions(self, obj):
        pending_value = obj.ModerationStatus.PENDING
        if obj.moderation_status != pending_value:
            return obj.get_moderation_status_display()
        approve_url = reverse(
            f"admin:{self.moderation_url_name}",
            args=(obj.pk, "approve"),
        )
        reject_url = reverse(
            f"admin:{self.moderation_url_name}",
            args=(obj.pk, "reject"),
        )
        return format_html(
            '<a class="button" style="margin-right:6px;'
            'background:#198754;color:#fff" href="{}">Одобрить</a>'
            '<a class="button" style="background:#ba2121;color:#fff" '
            'href="{}">Отклонить</a>',
            approve_url,
            reject_url,
        )

    def moderate_object(self, request, object_id, decision):
        if not self.has_change_permission(request):
            raise PermissionDenied

        instance = self.get_object(request, object_id)
        if instance is None:
            return HttpResponseRedirect(
                reverse(
                    f"admin:{self.model._meta.app_label}_"
                    f"{self.model._meta.model_name}_changelist"
                )
            )
        if decision not in {"approve", "reject"}:
            self.message_user(
                request,
                "Неизвестное решение модерации.",
                level=messages.ERROR,
            )
            return self._change_redirect(instance)

        form = self.moderation_form_class(
            request.POST or None,
            require_note=decision == "reject",
        )
        if request.method == "POST" and form.is_valid():
            try:
                success_message = self.apply_decision(
                    request=request,
                    instance=instance,
                    decision=decision,
                    note=form.cleaned_data["moderation_note"],
                )
            except (AIAccessDenied, AIServiceError, ValueError) as error:
                form.add_error(None, str(error))
            else:
                self.message_user(
                    request,
                    success_message,
                    level=messages.SUCCESS,
                )
                return self._change_redirect(instance)

        return TemplateResponse(
            request,
            self.moderation_template,
            {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "original": instance,
                "object_id": object_id,
                "decision": decision,
                "form": form,
                "title": self.moderation_title(decision),
                "generated_content": getattr(
                    instance,
                    self.generated_content_field,
                ),
                "has_view_permission": self.has_view_permission(
                    request,
                    instance,
                ),
            },
        )

    def _change_redirect(self, instance):
        return HttpResponseRedirect(
            reverse(
                f"admin:{self.model._meta.app_label}_"
                f"{self.model._meta.model_name}_change",
                args=(instance.pk,),
            )
        )


@admin.register(AIGeneratedInstruction)
class AIGeneratedInstructionAdmin(
    ModerationAdminMixin,
    admin.ModelAdmin,
):
    moderation_form_class = InstructionModerationForm
    moderation_url_name = "AI_aigeneratedinstruction_moderate"
    moderation_template = (
        "admin/AI/aigeneratedinstruction/moderation_form.html"
    )
    change_form_template = (
        "admin/AI/aigeneratedinstruction/change_form.html"
    )
    list_display = (
        "id",
        "ai_request",
        "instruction",
        "version_number",
        "is_cached",
        "moderation_status",
        "reviewed_by",
        "created_at",
        "moderation_actions",
    )
    list_filter = ("moderation_status", "is_cached", "created_at")
    search_fields = (
        "ai_request__user__email",
        "ai_request__prompt",
        "instruction__title",
    )
    autocomplete_fields = ("ai_request", "instruction")
    readonly_fields = (
        "version_number",
        "is_cached",
        "moderation_status",
        "moderation_note",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )

    def apply_decision(self, *, request, instance, decision, note):
        service = AIInstructionModerationService()
        if decision == "approve":
            service.approve(
                moderator=request.user,
                generated_instruction=instance,
                moderation_note=note,
            )
            return "AI-инструкция одобрена и опубликована."
        service.reject(
            moderator=request.user,
            generated_instruction=instance,
            moderation_note=note,
        )
        return "AI-инструкция отклонена."

    @staticmethod
    def moderation_title(decision):
        return (
            "Одобрить и опубликовать AI-инструкцию"
            if decision == "approve"
            else "Отклонить AI-инструкцию"
        )


@admin.register(AIToolRecommendation)
class AIToolRecommendationAdmin(
    ModerationAdminMixin,
    admin.ModelAdmin,
):
    moderation_form_class = ToolModerationForm
    moderation_url_name = "AI_aitoolrecommendation_moderate"
    moderation_template = (
        "admin/AI/aitoolrecommendation/moderation_form.html"
    )
    change_form_template = (
        "admin/AI/aitoolrecommendation/change_form.html"
    )
    list_display = (
        "id",
        "ai_request",
        "part",
        "moderation_status",
        "reviewed_by",
        "created_at",
        "moderation_actions",
    )
    list_filter = ("moderation_status", "created_at")
    search_fields = (
        "ai_request__user__email",
        "ai_request__part__name",
        "ai_request__part__original_number",
        "generated_content",
    )
    autocomplete_fields = ("ai_request",)
    readonly_fields = (
        "moderation_status",
        "moderation_note",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )

    @admin.display(description="Деталь")
    def part(self, obj):
        return obj.ai_request.part or "—"

    def apply_decision(self, *, request, instance, decision, note):
        service = AIToolRecommendationModerationService()
        if decision == "approve":
            service.approve(
                moderator=request.user,
                recommendation=instance,
                moderation_note=note,
            )
            return "Рекомендация инструментов одобрена."
        service.reject(
            moderator=request.user,
            recommendation=instance,
            moderation_note=note,
        )
        return "Рекомендация инструментов отклонена."

    @staticmethod
    def moderation_title(decision):
        return (
            "Одобрить рекомендацию инструментов"
            if decision == "approve"
            else "Отклонить рекомендацию инструментов"
        )


class AIImageAnalysisAdminForm(forms.ModelForm):
    class Meta:
        model = AIImageAnalysis
        fields = "__all__"
        widgets = {
            "analysis_result": PrettyJSONWidget(
                attrs={
                    "rows": 34,
                    "cols": 120,
                    "spellcheck": "false",
                    "style": (
                        "width:100%;min-height:640px;"
                        "font-family:ui-monospace,SFMono-Regular,Consolas,"
                        "monospace;line-height:1.5;tab-size:2;"
                    ),
                }
            )
        }


@admin.register(AIImageAnalysis)
class AIImageAnalysisAdmin(admin.ModelAdmin):
    form = AIImageAnalysisAdminForm
    list_display = (
        "id",
        "user",
        "detected_part",
        "confidence_score",
        "moderation_status",
        "created_at",
    )
    list_filter = ("moderation_status", "created_at")
    search_fields = (
        "user__email",
        "detected_part__name",
        "detected_part__original_number",
    )
    autocomplete_fields = ("user", "detected_part")
    readonly_fields = (
        "moderation_status",
        "moderation_categories",
        "moderation_model",
        "moderation_checked_at",
        "created_at",
    )
    formfield_overrides = {
        models.JSONField: {
            "widget": PrettyJSONWidget(
                attrs={
                    "rows": 34,
                    "style": (
                        "width:100%;min-height:640px;"
                        "font-family:ui-monospace,Consolas,monospace;"
                        "line-height:1.5;"
                    ),
                }
            )
        }
    }
