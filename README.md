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

## Development

1. Check out the code (you've done this!)
2. Run `just bootstrap`; this will set up the local environment and seed the DB, including fake users and a fake election
3. just serve should work once you've done this.

Because Seattle's setup does not use password logins, you can log in by generating yourself test links:

``` shellsession
$ bin/login-link --base-url http://localhost:12000 \
  42 worldcon@example.com Chris Rose
http://localhost:12000/controll-redirect/?r=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Mzc4NDc3NzkuNTMzMjAxLCJlbWFpbCI6IndvcmxkY29uQGV4YW1wbGUuY29tIiwicGVyaWQiOiI0MiIsIm5ld3BlcmlkIjpudWxsLCJsZWdhbE5hbWUiOm51bGwsImZpcnN0X25hbWUiOiJDaHJpcyIsImxhc3RfbmFtZSI6IlJvc2UiLCJmdWxsTmFtZSI6IkNocmlzIFJvc2UiLCJyZXNUeXBlIjoiZnVsbFJpZ2h0cyIsInJpZ2h0cyI6Imh1Z29fbm9taW5hdGUsaHVnb192b3RlIn0.goSHw6rHLAitb38JJpnVL3oCKHsXY8aAfeTpW5N1sW45m2nf-Mg-8svo_KhvtEo5_mbMzxZkv6gKrjpPzZrQcQ
```

This will create a link that will auto-log-in member with ID 42, the name Chris Rose, and the email `worldcon@example.com`

### Logging in as the admin user

The admin interface is only accessible from the `/admin/` path: `http://localhost:12000/admin/` in the default case; you can't otherwise log in with admin permissions.

Use the username `admin` and password `admin` at that endpoint.
