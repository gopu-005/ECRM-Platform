FROM node:20-alpine

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install node dependencies
RUN npm install

# Copy source code
COPY . .

# Expose Vite development port
EXPOSE 3000

# Start Vite dev server on 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
