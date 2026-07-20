#!/bin/sh
# Backend container entrypoint: make the writable mounts usable, then drop to
# the unprivileged runtime user.
#
# Why this exists
# ---------------
# The image runs the server as `appuser` (UID 1000) so that a container escape
# is not a host-level compromise. But `docker-compose.yml` bind-mounts a host
# directory over `/app/storage`, and a bind mount arrives with the *host's*
# ownership, overriding whatever the image set up. On Docker Desktop for Windows
# that ownership is `root:root` with mode 755, so UID 1000 cannot create
# `/app/storage/uploads` and the server dies at startup with:
#
#     PermissionError: [Errno 13] Permission denied: '/app/storage/uploads'
#
# This was not a theoretical risk: it crash-looped the backend container on the
# project's own development machine while `deployment/README.md` claimed Windows
# mapped bind-mount permissions automatically. It does not.
#
# The fix is the standard one for images that must accept arbitrary bind mounts:
# start as root, correct the ownership of just the mount points, then re-exec
# the real command as the unprivileged user. The server process itself never
# runs as root -- `setpriv` replaces the process image, so there is no root
# parent left alive once the server starts.
#
# Running the container with `user:` set (or `--user`) skips the fix-up branch
# entirely, so an operator who has already arranged correct ownership -- or who
# deliberately runs as a different UID -- keeps full control.

set -eu

APP_USER="${APP_USER:-appuser}"
APP_UID="${APP_UID:-1000}"
APP_GID="${APP_GID:-1000}"

if [ "$(id -u)" = "0" ]; then
    # Only the mount points, and only one level deep. A recursive chown over
    # `/app/storage` would rewrite every stored image and video on each start,
    # which on a populated demo directory costs seconds and, worse, rewrites
    # timestamps that the history records refer to.
    for dir in /app/storage /app/data /home/"${APP_USER}"; do
        [ -d "${dir}" ] || mkdir -p "${dir}"
        # A read-only mount (models/, mounted `:ro`) makes chown fail; that is
        # expected and must not stop the container. Anything else writable that
        # cannot be chowned is reported but also not fatal, because the server's
        # own startup check gives a far clearer error than this script could.
        chown "${APP_UID}:${APP_GID}" "${dir}" 2>/dev/null \
            || echo "entrypoint: could not chown ${dir}; continuing" >&2
    done

    exec setpriv --reuid "${APP_UID}" --regid "${APP_GID}" --init-groups -- "$@"
fi

# Already unprivileged: nothing to fix up, nothing to drop.
exec "$@"
