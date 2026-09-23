FROM node:24-alpine AS build

WORKDIR /app

COPY package.json .npmrc /app/
COPY apps /app/apps
COPY packages /app/packages

RUN npm ci
RUN npm run build -w @nyameko/blog

FROM nginxinc/nginx-unprivileged:1.29-alpine

COPY apps/blog/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/blog/dist /usr/share/nginx/html

EXPOSE 8080
