const db = require('./db');
const helper = require('../helper');
const config = require('../config');

async function getMultiple(page = 1){
  const offset = helper.getOffset(page, config.listPerPage);
  const rows = await db.query(
    `SELECT id, name, released_year, githut_rank, pypl_rank, tiobe_rank 
    FROM programming_languages LIMIT $1 OFFSET $2`,
    [config.listPerPage, offset]
  );
  const data = helper.emptyOrRows(rows);
  const meta = {page};

  
  return {
    data,
    meta
  }
}
async function create(programmingLanguage) {
  const rows = await db.query(
    `INSERT INTO programming_languages (name, released_year, githut_rank, pypl_rank, tiobe_rank) VALUES ($1, $2, $3, $4, $5) RETURNING *`,
    [programmingLanguage.name, programmingLanguage.released_year, programmingLanguage.githut_rank, programmingLanguage.pypl_rank, programmingLanguage.tiobe_rank]
  );

  let message = 'Error in creating programming language';

  if (rows && rows.length > 0) {
    message = 'Programming language created successfully';
  }

  return { message, data: rows[0] };
}
async function update(id, programmingLanguage) {
  const rows = await db.query(
    `UPDATE programming_languages SET name=$1, released_year=$2, githut_rank=$3, pypl_rank=$4, tiobe_rank=$5 WHERE id=$6 RETURNING *`,
    [programmingLanguage.name, programmingLanguage.released_year, programmingLanguage.githut_rank, programmingLanguage.pypl_rank, programmingLanguage.tiobe_rank, id]
  );

  let message = 'Error in updating programming language';

  if (rows && rows.length > 0) {
    message = 'Programming language updated successfully';
  }

  return {message};
}


async function remove(id) {
  await db.query(`DELETE FROM programming_languages WHERE id=$1`, [id]);
  return {message: 'Programming language deleted successfully'};
}



module.exports = {
  getMultiple,
  create,
  update,
  remove
}