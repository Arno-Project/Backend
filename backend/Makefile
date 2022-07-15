include .env

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
superuser:
	docker-compose exec arno python manage.py createsuperuser
runserver:
	docker-compose exec arno python manage.py runserver
down-v:
	docker-compose down -v
volume:
	docker volume inspect arno_postgres_data
shell:
	docker-compose exec arno python manage.py shell
tests:
	docker-compose exec arno python manage.py test -v 2

drop-table:
	docker-compose down && docker volume rm backend_postgres_data