const db = require('./db');
const helper = require('../helper');
const config = require('../config');

async function getproduct(page = 1){
  const offset = helper.getOffset(page, config.listPerPage);
  const rows = await db.query(
    `SELECT product.pid, product.pname, product.pprice, product.cid, category.cname
FROM product 
JOIN category ON product.cid = category.cid `

  );
  const data = helper.emptyOrRows(rows);
  const meta = {page};

  
  return {
    data,
    meta
  }
}

async function createproduct(product) {
    const rows = await db.query(
      `INSERT INTO product (pname, pprice, cid) VALUES ($1, $2, $3) RETURNING *`,
      [product.pname, product.pprice, product.cid]
    );
    
    let message = 'Error in creating product';
  
    if (rows && rows.length > 0) {
      message = 'added successfully';
    }
  
    return { message, data: rows[0] };
  }

  async function updateproduct(pid, product){
    const rows = await db.query(
        `UPDATE product SET pname=$1, pprice=$2, cid=$3 WHERE pid=$4 RETURNING *`,
        [product.pname, product.pprice, product.cid, pid]
    );
  
    let message = 'Error in updating product';
  
    if (rows && rows.length > 0) {
      message = 'product updated successfully';
    }
  
    return {message};
  }
  async function removeproduct(pid){
    await db.query(`DELETE FROM product WHERE pid=$1`, [pid]);
    return {message: 'product deleted successfully'};
  }

 
  module.exports = {getproduct,createproduct,updateproduct,removeproduct};