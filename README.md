# Seattle Worldcon 2025 NomNom

## Deployment Notes

### First Deployment

- clone this repo on to your deployment host.
- construct the .env for your stage (deploy/staging/.env.template and deploy/production/.env.template are the sources, just remove .template for them)
- make sure the version in .env is set the way you want
- docker compose -f deploy/staging/compose.yml pull to make sure you have the image
- docker compose -f deploy/staging/compose.yml up boot to make sure it starts
- docker compose -f deploy/staging/compose.yml up --wait to start it

Make sure to load the relevant permissions in; to do that, these are the compose-based commands to set it up:

``` shellsession
# first set up a super user; this should be a very complex password, and unique to this con. Only one of these is needed.
$ docker compose -f deploy/staging/compose.yml run web -- ./manage.py createsuperuser

# second, load the group data we need for other members and admins
# note, this needs to be done from the root of the checkout, as it relies on seed data in the code.
$ docker compose -f deploy/staging/compose.yml run -v $(pwd)/seed:/app/seed:ro --rm web -- ./manage.py loaddata -v3 "all/0001-permissions.json"
```

## Admin Notes

- members cannot be automatically demoted from nominator/voter once they have signed on; you have to do it yourself.
