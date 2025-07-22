from enum import Enum

from django.utils.translation import gettext_lazy as _


class SessionType(str, Enum):
    """
    Enumeration of course session types for laboratory management.
    Stored in Indonesian for DB consistency.

    Core laboratory session types focus on practical activities
    commonly found in academic laboratory settings.
    """

    # Core laboratory session types
    EXPERIMENT = "Percobaan"
    RESPONSI = "Responsi"
    FINAL_PROJECT = "Tugas Akhir"

    # Additional laboratory session types
    LAB_INTRODUCTION = "Pengenalan Lab"
    PRACTICAL_EXAM = "Ujian Praktikum"
    TUTORIAL = "Tutorial"

    # General academic session types
    LECTURE = "Kuliah"
    QUIZ = "Kuis"
    PRESENTATION = "Presentasi"
    DISCUSSION = "Diskusi"
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    EXAM = "Ujian"
    REVIEW = "Review"

    @classmethod
    def choices(cls):
        """
        Return list of (value, label) tuples for Django model field choices.
        """
        return [(item.value, item.label()) for item in cls]

    def label(self):
        """
        Return translated label for display purposes.
        """
        labels = {
            self.EXPERIMENT: _("Experiment"),
            self.RESPONSI: _("Responsi"),
            self.FINAL_PROJECT: _("Final Project"),
            self.LAB_INTRODUCTION: _("Lab Introduction"),
            self.PRACTICAL_EXAM: _("Practical Exam"),
            self.TUTORIAL: _("Tutorial"),
            self.LECTURE: _("Lecture"),
            self.QUIZ: _("Quiz"),
            self.PRESENTATION: _("Presentation"),
            self.DISCUSSION: _("Discussion"),
            self.WORKSHOP: _("Workshop"),
            self.SEMINAR: _("Seminar"),
            self.EXAM: _("Exam"),
            self.REVIEW: _("Review"),
        }
        return labels.get(self, self.value)
