from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from course.models import Course


@receiver(m2m_changed, sender=Course.students.through)
@receiver(m2m_changed, sender=Course.teaching_assistants.through)
def update_course_participants(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        total_students = instance.students.count()
        total_assistants = instance.teaching_assistants.count()
        instance.total_students = total_students
        instance.total_teaching_assistants = total_assistants
        instance.total_participants = total_students + total_assistants
        instance.save(
            update_fields=[
                "total_students",
                "total_teaching_assistants",
                "total_participants",
            ]
        )
