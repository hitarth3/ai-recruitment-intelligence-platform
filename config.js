require('dotenv').config();

const config = {
    db: {
      host: process.env.DB_HOST || "localhost",
      user: process.env.DB_USER || "postgres",
      password: process.env.DB_PASSWORD || "2004",
      database: process.env.DB_NAME || "hitarthshah",
      setTimeout: 600000,
      port: process.env.DB_PORT || 5432, // PostgreSQL default port
    },
    secret: process.env.JWT_SECRET || 'my-api',
    listPerPage: 25,
  };
  module.exports = config;