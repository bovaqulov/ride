from django import forms
from django.core.exceptions import ValidationError


class MassMessageForm(forms.Form):
    MESSAGE_TYPES = [
        ('all', 'Barcha foydalanuvchilar'),
        ('users', 'Faqat yo\'lovchilar'),
        ('drivers', 'Faqat haydovchilar'),
        ('banned', 'Bloklangan foydalanuvchilar'),
        ('custom', 'Maxsus ro\'yxat'),
    ]

    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPES,
        label="Xabar yuborish turi"
    )

    custom_ids = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Telegram ID larni vergul bilan ajrating: 123456, 789012, ...'
        }),
        label="Maxsus Telegram ID lar",
        help_text="Vergul bilan ajratilgan Telegram ID lar"
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
            'placeholder': 'Xabar matnini kiriting...\nHTML formatlash imkoniyatlari:\n<b>qalin matn</b>\n<i>kursiv</i>\n<a href="link">havola</a>'
        }),
        label="Xabar matni",
        help_text="HTML formatlash qo'llab-quvvatlanadi"
    )

    parse_mode = forms.ChoiceField(
        choices=[
            ('HTML', 'HTML'),
            ('Markdown', 'Markdown'),
        ],
        initial='HTML',
        label="Formatlash turi"
    )

    def clean_custom_ids(self):
        custom_ids = self.cleaned_data.get('custom_ids', '')
        if custom_ids:
            try:
                ids = [int(pk.strip()) for pk in custom_ids.split(',') if pk.strip()]
                return ids
            except ValueError:
                raise ValidationError("Iltimos, faqat raqamlarni kiriting")
        return []