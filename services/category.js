// services/category.js
const db = require('./db');

async function getcategory(page = 1) {
  const offset = (page - 1) * 10; // Assuming 10 items per page
  const rows = await db.query(
    'SELECT * FROM category ORDER BY id LIMIT $1 OFFSET $2',
    [10, offset]
  );
  return rows;
}

async function createcategory(category) {
  const result = await db.query(
    'INSERT INTO category(name, description) VALUES ($1, $2) RETURNING *',
    [category.name, category.description]
  );
  return result;
}

async function updatecategory(id, category) {
  const result = await db.query(
    'UPDATE category SET name = $1, description = $2 WHERE id = $3 RETURNING *',
    [category.name, category.description, id]
  );
  return result;
}

async function removecategory(id) {
  const result = await db.query(
    'DELETE FROM category WHERE id = $1 RETURNING *',
    [id]
  );
  return result;
}

module.exports = {
  getcategory,
  createcategory,
  updatecategory,
  removecategory
};