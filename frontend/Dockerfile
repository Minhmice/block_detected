FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
ARG NEXT_PUBLIC_API_BASE_URL=http://backend:8000
ARG NEXT_PUBLIC_WS_URL=ws://backend:8000/ws/detection
ARG NEXT_PUBLIC_STREAM_URL=http://backend:8000/video/stream
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_STREAM_URL=$NEXT_PUBLIC_STREAM_URL
RUN npm run build

FROM node:20-alpine AS frontend
WORKDIR /app
COPY --from=frontend-build /app/frontend/.next ./.next
COPY --from=frontend-build /app/frontend/public ./public
COPY --from=frontend-build /app/frontend/package*.json ./
COPY --from=frontend-build /app/frontend/node_modules ./node_modules

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/ || exit 1

CMD ["npm", "run", "start"]
