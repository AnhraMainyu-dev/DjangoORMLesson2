FROM node:16-slim

WORKDIR /starburger

COPY package.json package-lock.json ./
RUN npm ci

COPY bundles-src ./bundles-src
RUN ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./" --no-source-maps

CMD ["cp", "-r", "bundles/.", "/bundles/"]
