const db = require('./db');
const helper = require('../helper');
const config = require('../config');
const bcrypt = require('bcryptjs');

async function createuser(user) {
    const hashedPassword = await bcrypt.hash(user.password, 10);
    const rows = await db.query(
      `INSERT INTO "user" (name, email, password) VALUES ($1, $2, $3) RETURNING id, name, email`,
      [user.name, user.email, hashedPassword]
    );
    
    let message = 'Error in signing up';
  
    if (rows && rows.length > 0) {
      message = 'user added successfully';
    }
  
    return { message, data: rows ? rows[0] : null };
}

async function findUserByName(name) {
    const rows = await db.query(
        `SELECT * FROM "user" WHERE name=$1`,
        [name]
    );
    return rows && rows.length > 0 ? rows[0] : null;
}

module.exports = { createuser, findUserByName };