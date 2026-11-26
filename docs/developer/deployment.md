# Deploying on a virtual machine

!!! warning
This is a development deployment: everything runs on one virtual machine (VM). It is
good for trying FaraX out and for sharing a working copy with collaborators. It is
not the production setup. Production will use managed services configured in the
cloud provider, Azure in our case, such as a managed PostgreSQL database and a
managed web service, rather than containers on a VM (see
[Moving to production](#moving-to-production)).

The `deployment/` directory contains everything needed to run FaraX on a VM with
[Docker Compose]:

| File                 | Purpose                                                           |
| -------------------- | ----------------------------------------------------------------- |
| `docker-compose.yml` | Defines the three services below.                                 |
| `Caddyfile`          | Tells the proxy which domain to serve and where to send requests. |
| `.env.example`       | Template for the `.env` file with the deployment's settings.      |

Don't confuse it with the `docker-compose.yml` at the repository root, which is for
local development (see
[Running with Docker Compose](index.md#running-with-docker-compose)).

## What runs

| Service    | Image                                        | Role                                                                                                                                                       |
| ---------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `web`      | `ghcr.io/imperialcollegelondon/farax:latest` | FaraX, served by [Gunicorn] with two workers. On every start it applies database migrations and collects static files.                                     |
| `proxy`    | `caddy:2.11-alpine`                          | [Caddy] reverse proxy. It listens on ports 80 and 443, gets and renews an HTTPS certificate for your domain automatically, and forwards requests to `web`. |
| `postgres` | `postgres:18`                                | The database.                                                                                                                                              |

Unlike the development setup, the `web` service uses the published FaraX image rather than
building from the source tree, so the VM doesn't need the source code or uv. It uses the
[production settings](index.md#production-settings), which expect the HTTPS proxy that
Caddy provides.

Data is kept on three named Docker volumes: `postgres` (the database), `media` (the File
Store, see [ADR 0003](../adr/0003-raw-files-in-file-store.md)) and `static` (collected
static files).

## Before you start

You need:

- A Linux VM with [Docker Engine and the Docker Compose plugin][Install Docker] installed.
- A domain name, such as `farax.example.org`, with a DNS record pointing to the VM's
  public IP address. Caddy needs it to obtain the HTTPS certificate, so use a real name
  rather than the IP address.
- Ports 80 and 443 reachable from the internet. On an Azure VM, add inbound rules for
  them to the VM's network security group (and keep port 22 open for SSH). Port 80 is
  needed to get the certificate even though the site is only served over HTTPS.
- Access to the FaraX image. If the package is private, log in to the GitHub Container
  Registry with a personal access token that has the `read:packages` scope:

  ```bash
  docker login ghcr.io -u <github-username>
  ```

## Set up

Copy the contents of `deployment/` to the VM, for example by cloning the repository, and
work from that directory. Only these three files are needed; the rest of the repository
isn't used.

```bash
git clone https://github.com/ImperialCollegeLondon/FaraX.git
cd FaraX/deployment
cp .env.example .env
```

Edit `.env`. Docker Compose passes this file to all three services, so it is the one
place to configure the deployment. Keep it private and never commit it. The following
values need to be set:

| Variable                                            | Value                                                                                                                                                                   |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DOMAIN`                                            | The domain name from DNS, with no `https://`. Used by Caddy.                                                                                                            |
| `DJANGO_SETTINGS_MODULE`                            | `farax.settings.production`                                                                                                                                             |
| `DJANGO_SECRET_KEY`                                 | A long random string, see below.                                                                                                                                        |
| `DJANGO_ALLOWED_HOSTS`                              | The same domain name as `DOMAIN`.                                                                                                                                       |
| `DJANGO_MEDIA_ROOT`                                 | `/data/media`, where the `media` volume is mounted, so the File Store is kept on the volume.                                                                            |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | The database name and credentials. The `postgres` service creates the database with them the first time it starts, and FaraX connects with them. Use a strong password. |
| `POSTGRES_HOST`                                     | `postgres`, the name of the database service in Compose.                                                                                                                |
| `POSTGRES_PORT`                                     | `5432`                                                                                                                                                                  |

Generate a secret key with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

The `DJANGO_EMAIL_*` variables are optional and set up the SMTP server FaraX sends email
through. They are described in
[Production settings](index.md#production-settings).

!!! note
The PostgreSQL image only reads `POSTGRES_USER`, `POSTGRES_PASSWORD` and
`POSTGRES_DB` the first time it starts, when the `postgres` volume is empty.
Changing them afterwards doesn't change the existing database, and FaraX will fail
to connect. Either change the credentials inside PostgreSQL too, or delete the
volume (and its data) with `docker compose down -v` and start again.

## Start FaraX

From `deployment/`:

```bash
docker compose pull          # download the images
docker compose up -d         # start everything in the background
docker compose ps            # check that all three services are running
docker compose logs -f web   # follow the logs; press Ctrl+C to stop following
```

The first start takes a little longer: the database is created, `web` waits for it to be
healthy, then applies the migrations and collects the static files before Gunicorn
starts. Caddy requests the HTTPS certificate when it starts, so HTTPS may not work for
the first minute. If it still doesn't, see [Troubleshooting](#troubleshooting).

Create an account for the Django admin, then log in at `https://<your domain>/admin/`:

```bash
docker compose exec web python manage.py createsuperuser
```

## Day-to-day operation

Run these from `deployment/`.

| Task                                    | Command                                               |
| --------------------------------------- | ----------------------------------------------------- |
| View logs                               | `docker compose logs -f web` (or `proxy`, `postgres`) |
| Restart a service                       | `docker compose restart web`                          |
| Stop everything, keeping data           | `docker compose down`                                 |
| Stop everything and **delete all data** | `docker compose down -v`                              |
| Run a management command                | `docker compose exec web python manage.py <command>`  |

All services restart automatically after a crash or a reboot of the VM, unless you
stopped them yourself with `docker compose stop` or `docker compose down`.

### Update FaraX

New images are published to the GitHub Container Registry when a release is published,
tagged with the release version (for example `v0.0.3`) and also as `latest`, so the
default `latest` image is always the newest release. To stay on a specific version
instead, change the `web` image in `docker-compose.yml`, for example to
`ghcr.io/imperialcollegelondon/farax:v0.0.3`. Then update with:

```bash
docker compose pull web
docker compose up -d web     # recreates web, which applies any new migrations
```

### Back up

Back up the database and the File Store regularly; the VM's disk is the only copy.

```bash
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > farax-db.sql
```

The File Store is the `media` volume, which Docker names after the Compose project
(the `deployment` directory by default), so `deployment_media`. Back it up with, for
example:

```bash
docker run --rm -v deployment_media:/data:ro -v "$PWD":/backup alpine tar czf /backup/farax-media.tar.gz -C /data .
```

Copy the backups off the VM, for example to an Azure storage account. Azure's VM disk
snapshots are a coarser alternative.

## Troubleshooting

- **The browser can't connect, or shows a certificate error.** Check that the domain
  resolves to the VM, that ports 80 and 443 are open in Azure and any VM firewall, and
  read the certificate errors in `docker compose logs proxy`.
- **`Bad Request (400)`.** The host name isn't in `DJANGO_ALLOWED_HOSTS`. Fix `.env`,
  then run `docker compose up -d web` to recreate the service with the new values.
- **`web` keeps restarting.** Read `docker compose logs web`. Django refuses to start
  when a required variable is missing from `.env` (see
  [Production settings](index.md#production-settings)), and the database login fails
  if the credentials no longer match the `postgres` volume (see the note above).
- **After editing `.env`, nothing changes.** `docker compose restart` doesn't re-read
  it. Use `docker compose up -d`, which recreates the services whose settings changed.

## Moving to production

This deployment is deliberately simple, and has limits that production must not have:

- The database runs in a container on the same VM as the app. Production should use a
  managed PostgreSQL service with automated backups.
- Everything is on one VM, so there is no redundancy and updates cause downtime.
- Secrets live in a `.env` file on the VM, and every service can see all of them.
  Production should keep them in a secret store such as Azure Key Vault.
- Caddy has no volume for its data, so its certificates are lost when the `proxy`
  container is recreated and it must request new ones. Repeated requests can hit the
  certificate authority's rate limits.
- The File Store is a local volume. Production needs storage that survives the loss of
  the VM and can be shared between instances.
- Backups are manual.
- HSTS is set to one hour, so a mistake can be undone. Raise it once the deployment
  is final (see `farax/settings/production.py`).

The hosting decisions for production are tracked in the project's issues; the settings
and these instructions will change when they are made.

[Caddy]: https://caddyserver.com/docs/
[Docker Compose]: https://docs.docker.com/compose/
[Gunicorn]: https://gunicorn.org/
[Install Docker]: https://docs.docker.com/engine/install/
