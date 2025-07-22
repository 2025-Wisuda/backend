"""
Django management command to test the i18n (internationalization) system.

Usage:
    python manage.py test_i18n
    python manage.py test_i18n --language=en
    python manage.py test_i18n --language=id
"""

from django.core.management.base import BaseCommand
from django.utils.translation import activate
from django.utils.translation import gettext as _

from shared.utils.i18n_utils import get_common_messages, test_translations


class Command(BaseCommand):
    help = 'Test the i18n system with English and Indonesian translations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            choices=['en', 'id'],
            help='Test specific language (en/id). If not specified, tests both.',
        )

    def handle(self, *args, **options):
        language = options.get('language')
        
        self.stdout.write(
            self.style.SUCCESS('🌍 Testing Laboratory Management System i18n')
        )
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if language:
            self.test_single_language(language)
        else:
            self.test_all_languages()
            
        self.stdout.write(
            self.style.SUCCESS('\n✅ i18n testing completed successfully!')
        )

    def test_single_language(self, language_code):
        """Test translations for a single language."""
        activate(language_code)
        language_name = 'English' if language_code == 'en' else 'Indonesian'
        
        self.stdout.write(
            self.style.WARNING(f'\n📍 Testing {language_name} ({language_code}):')
        )
        
        messages = get_common_messages()
        
        # Display common status messages
        self.stdout.write(self.style.HTTP_INFO('\n  Status Messages:'))
        status_keys = ['pending', 'approved', 'rejected', 'cancelled', 'completed', 'expired']
        for key in status_keys:
            if key in messages:
                self.stdout.write(f'    • {key}: {messages[key]}')
        
        # Display attendance messages
        self.stdout.write(self.style.HTTP_INFO('\n  Attendance Messages:'))
        attendance_keys = ['present', 'absent', 'late']
        for key in attendance_keys:
            if key in messages:
                self.stdout.write(f'    • {key}: {messages[key]}')
        
        # Display day names
        self.stdout.write(self.style.HTTP_INFO('\n  Day Names:'))
        day_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for key in day_keys:
            if key in messages:
                self.stdout.write(f'    • {key}: {messages[key]}')
        
        # Display month names (first 6)
        self.stdout.write(self.style.HTTP_INFO('\n  Month Names (Sample):'))
        month_keys = ['january', 'february', 'march', 'april', 'may', 'june']
        for key in month_keys:
            if key in messages:
                self.stdout.write(f'    • {key}: {messages[key]}')
        
        # Display activity types
        self.stdout.write(self.style.HTTP_INFO('\n  Activity Types:'))
        activity_keys = ['practicum', 'seminar', 'experiment', 'tutorial', 'lecture', 'quiz', 'exam']
        for key in activity_keys:
            if key in messages:
                self.stdout.write(f'    • {key}: {messages[key]}')

    def test_all_languages(self):
        """Test translations for all supported languages."""
        results = test_translations()
        
        for lang_code, messages in results.items():
            language_name = 'English' if lang_code == 'en' else 'Indonesian'
            self.test_single_language(lang_code)
            
        # Compare translations
        self.stdout.write(self.style.WARNING('\n📊 Translation Comparison:'))
        self.stdout.write(self.style.HTTP_INFO('\nKey comparison (EN vs ID):'))
        
        # Get fresh results for comparison
        activate('en')
        en_messages = get_common_messages()
        activate('id')
        id_messages = get_common_messages()
        
        sample_keys = ['pending', 'approved', 'monday', 'january', 'practicum', 'student']
        for key in sample_keys:
            if key in en_messages and key in id_messages:
                en_text = str(en_messages[key])
                id_text = str(id_messages[key])
                self.stdout.write(f'  • {key}:')
                self.stdout.write(f'    EN: {en_text}')
                self.stdout.write(f'    ID: {id_text}')
                
        # Check for missing translations
        self.stdout.write(self.style.HTTP_INFO('\n🔍 Translation Coverage:'))
        en_keys = set(en_messages.keys())
        id_keys = set(id_messages.keys())
        
        if en_keys == id_keys:
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ All {len(en_keys)} keys have translations in both languages')
            )
        else:
            missing_in_id = en_keys - id_keys
            missing_in_en = id_keys - en_keys
            
            if missing_in_id:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Missing in Indonesian: {missing_in_id}')
                )
            if missing_in_en:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Missing in English: {missing_in_en}')
                )

    def test_runtime_translation(self):
        """Test runtime translation switching."""
        self.stdout.write(self.style.WARNING('\n🔄 Testing Runtime Translation Switching:'))
        
        # Test a simple message
        activate('en')
        en_pending = str(_('Pending'))
        
        activate('id')
        id_pending = str(_('Pending'))
        
        self.stdout.write(f'  Runtime switch test:')
        self.stdout.write(f'    English: {en_pending}')
        self.stdout.write(f'    Indonesian: {id_pending}')
        
        if en_pending != id_pending:
            self.stdout.write(self.style.SUCCESS('  ✅ Runtime switching works correctly'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ Runtime switching may not be working')) 