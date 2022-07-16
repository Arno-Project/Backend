# Arno

```bash
cd backend
```

## Start project

```bash
make build
make up
```

## Stop project

```bash
make down
```

## Translations

Make messages:

```bash
python manage.py makemessages --locale=fa --ignore=venv
```

Translate strings in 'locale/fa/LC_MESSAGES'.

Compile messages:

```bash
python manage.py compilemessages --locale=fa
```
