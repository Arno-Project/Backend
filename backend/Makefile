include .env
.PHONY: build up down restart logs migrate makemigrations startapp superuser runserver down-v volume shell tests drop-table
build:
	docker-compose up --build -d
up:
	docker-compose up -d
down:
	docker-compose down
restart:
	docker-compose restart
logs:
	docker-compose logs
migrate:
	docker-compose exec arno python manage.py migrate
makemigrations:
	docker-compose exec arno python manage.py makemigrations
startapp:
	docker-compose exec arno python manage.py startapp $(name)
superuser:
	docker-compose exec arno python manage.py createsuperuser
runserver:
	docker-compose exec arno python manage.py runserver
down-v:
	docker-compose down -v
volume:
	docker volume inspect backend_postgres_data
shell:
	docker-compose exec arno python manage.py shell
tests:
	docker-compose exec arno python manage.py test -v 2
drop-table:
	docker-compose down && docker volume rm backend_postgres_data
