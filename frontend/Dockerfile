# Use Node to build the browser files. Vite supports this Node version.
FROM node:24-alpine AS build

# Put the frontend files in one folder inside this build stage.
WORKDIR /app

# Copy the package list and lock file first so Docker can reuse the install.
COPY package.json package-lock.json ./

# Install exactly the frontend packages recorded in the lock file.
RUN npm ci

# Copy the frontend source files into the build stage.
COPY . .

# Turn the React app into static files that a web server can serve.
RUN npm run build

# Start a small Nginx web server to serve the built site.
FROM nginx:1.30-alpine

# Replace the default Nginx settings with Clearance's routing rules.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built website from the first stage into the web server.
COPY --from=build /app/dist /usr/share/nginx/html

# Record that the website listens on port 80 inside this container.
EXPOSE 80

# Keep Nginx running in the foreground so Docker can manage it.
CMD ["nginx", "-g", "daemon off;"]
