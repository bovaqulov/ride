# analytics/forms.py
from django import forms

class MassMessageForm(forms.Form):
    MESSAGE_TYPES = (
        ("all", "Barcha foydalanuvchilar"),
        ("users", "Yo'lovchilar"),
        ("drivers", "Haydovchilar"),
        ("banned", "Bloklanganlar"),
        ("custom", "Maxsus ro'yxat"),
    )

    PARSE_MODES = (
        ("HTML", "HTML"),
        ("Markdown", "Markdown"),
        ("MarkdownV2", "MarkdownV2"),
        ("", "Oddiy matn"),
    )

    MEDIA_TYPES = (
        ("none", "Faqat matn"),
        ("photo", "Rasm"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("document", "Fayl (document)"),
    )

    message_type = forms.ChoiceField(choices=MESSAGE_TYPES)
    parse_mode = forms.ChoiceField(choices=PARSE_MODES, required=False)
    custom_ids = forms.CharField(required=False, help_text="Vergul bilan ajrating: 123,456,789")

    message = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text="Matn (caption) 1024 belgigacha tavsiya qilinadi; oddiy xabar 4096."
    )

    media_type = forms.ChoiceField(choices=MEDIA_TYPES, required=True, initial="none")
    media_file = forms.FileField(required=False)

    def clean(self):
        cleaned = super().clean()
        media_type = cleaned.get("media_type")
        media_file = cleaned.get("media_file")

        if media_type != "none" and not media_file:
            raise forms.ValidationError("Media tanlangan bo'lsa, fayl ham yuklanishi shart.")
        return cleaned
