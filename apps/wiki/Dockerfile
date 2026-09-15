FROM node:22-alpine AS build

WORKDIR /app

COPY package.json .npmrc /app/
COPY apps /app/apps
COPY packages /app/packages

RUN npm install
RUN npm run build -w @nyameko/wiki

FROM nginxinc/nginx-unprivileged:1.29-alpine

COPY apps/wiki/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/wiki/dist /usr/share/nginx/html

EXPOSE 8080
