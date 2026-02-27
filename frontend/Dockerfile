# Stage 1: Build
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy the rest of the application
COPY . .

# Build the application
# Note: CI will pass the openapi.json if it exists, or it can be fetched
RUN yarn build

# Stage 2: Runtime
FROM nginx:mainline-alpine

LABEL authors="Felix Doering <development@felixdoering.com>"

COPY ./docker/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:80/index.html || exit 1

