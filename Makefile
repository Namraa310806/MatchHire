up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec web sh

migrate:
	docker compose run --rm web python manage.py migrate
