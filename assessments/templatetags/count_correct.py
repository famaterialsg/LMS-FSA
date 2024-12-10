from django import template

register = template.Library()

@register.filter
def correct_answer_count(question):
    return question.answer_options.filter(is_correct=True).count()