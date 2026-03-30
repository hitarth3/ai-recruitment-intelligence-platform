const { Pool } = require('pg');
const config = require('../config');

const pool = new Pool(config.db);

async function query(sql, params) {
  try {
    const result = await pool.query(sql, params);
    return result.rows;
  } catch (error) {
    throw error;
  }
}

module.exports = {
  query
};