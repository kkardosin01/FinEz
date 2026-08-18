FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY src ./src

RUN mkdir -p /data

EXPOSE 3333

CMD ["node", "src/index.js"]
