from datetime import timedelta


def generate_duty_dates(schedule_obj):
    from schedule.models import DutyDate

    selected_days = [day.strip().lower() for day in schedule_obj.days.split(",")]
    DutyDate.objects.filter(schedule=schedule_obj).delete()
    current = schedule_obj.start_date
    while current <= schedule_obj.end_date:
        day_name = current.strftime("%A").lower()
        if day_name in selected_days:
            DutyDate.objects.create(schedule=schedule_obj, duty_date=current)
        current += timedelta(days=1)
