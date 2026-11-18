# One image recipe for both React apps: docker build --build-arg APP=storefront|staff-dashboard
# Build context is the repo root (npm workspaces need the root package.json and lockfile).
FROM node:22-slim AS build
ARG APP=storefront
# Vite bakes VITE_* values into the bundle at build time, so they are build args, not runtime env.
ARG VITE_STRIPE_PUBLISHABLE_KEY=
ARG VITE_MAPBOX_TOKEN=
ENV VITE_STRIPE_PUBLISHABLE_KEY=$VITE_STRIPE_PUBLISHABLE_KEY \
    VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN
WORKDIR /repo
COPY package.json package-lock.json ./
COPY frontend ./frontend
# The committed package-lock.json only lists Linux x64 native binaries (Tailwind oxide, lightningcss,
# rolldown), so `npm ci` fails on arm64 hosts (Apple Silicon). Re-resolve inside the image so the right
# native packages are fetched for whatever platform Docker builds on. Local installs still use the lockfile.
RUN rm -f package-lock.json && npm install --no-audit --no-fund && npm run build -w ${APP}

FROM httpd:2.4
ARG APP=storefront
COPY --from=build /repo/frontend/${APP}/dist/ /usr/local/apache2/htdocs/
COPY docker/apache-app.conf /usr/local/apache2/conf/extra/app.conf
RUN sed -i \
      -e 's/^#\(LoadModule proxy_module\)/\1/' \
      -e 's/^#\(LoadModule proxy_http_module\)/\1/' \
      -e 's/^#\(LoadModule rewrite_module\)/\1/' \
      -e 's/^#\(LoadModule headers_module\)/\1/' \
      /usr/local/apache2/conf/httpd.conf \
 && echo 'Include conf/extra/app.conf' >> /usr/local/apache2/conf/httpd.conf
