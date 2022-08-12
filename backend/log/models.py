import inspect

from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
from utils.Singleton import Singleton
from utils.helper_funcs import ListAdapter


class Log(models.Model):
    class LogLevel(models.TextChoices):
        DEBUG = 'D', _('Debug')
        INFO = 'I', _('Info')
        WARNING = 'W', _('Warning')
        ERROR = 'E', _('Error')
        CRITICAL = 'C', _('Critical')

    level = models.CharField(max_length=1, choices=LogLevel.choices, default=LogLevel.DEBUG)
    source = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Log')
        verbose_name_plural = _('Logs')

    def __str__(self):
        return f"[{self.level}] | {self.created_at} | {self.source} | {self.message}"

    def get_level(self):
        return self.level

    def get_source(self):
        return self.source

    def get_message(self):
        return self.message

    def get_created_at(self):
        return self.created_at


class Logger(metaclass=Singleton):
    def log(self, message, level=Log.LogLevel.INFO, source=None):
        stack = inspect.stack()
        if source is None:
            try:
                the_class = stack[1][0].f_locals["self"].__class__.__name__
                the_method = stack[1][0].f_code.co_name
                frm = inspect.stack()[1]
                mod = inspect.getmodule(frm[0])
                source = f"{mod.__name__}.{the_class}.{the_method}" if source is None else source
            except:
                print("Error getting source")
                source = ""
        log = Log.objects.create(message=message, level=level, source=source)
        log.save()

    def log_name(self, log_level=Log.LogLevel.DEBUG):
        def _print_name(fn):
            def wrapper(*args, **kwargs):
                print('{}.{}'.format(fn.__module__, fn.__qualname__))
                source = f'{fn.__module__}.{fn.__qualname__}'
                Logger().log("Method started successfully.", source=source, level=log_level)
                retval = fn(*args, **kwargs)
                Logger().log("Method ended successfully.", source=source, level=log_level)
                return retval

            return wrapper

        return _print_name


class LogCatalogue(metaclass=Singleton):
    logs = Log.objects.all()

    def search(self, query: dict):
        result = self.logs

        if query.get('id'):
            result = result.filter(pk__in=ListAdapter().python_ensure_list(query['id']))

        if query.get('level'):
            result = result.filter(level__iexact=query.get('level'))

        for field in ['source', 'message']:
            if query.get(field):
                result = result.filter(**{field + "__icontains": query.get(field)})

        for field in ['created_at_gte']:
            if query.get(field):
                result = result.filter(**{'_'.join(field.split('_')[:-1]) + "__gte": query.get(field)})

        for field in ['created_at_lte']:
            if query.get(field):
                result = result.filter(**{'_'.join(field.split('_')[:-1]) + "__lte": query.get(field)})

        result = result.order_by('-created_at')

        return result
