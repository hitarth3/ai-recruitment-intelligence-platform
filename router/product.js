const express = require('express');
const router = express.Router();
const product = require('../services/product');

router.get('/', async function(req, res, next) {
    try {
      res.json(await product.getproduct(req.query.page));
    } catch (err) {
      console.error(`Error while getting products`, err.message);
      next(err);
    }
  });

router.post('/',async function(req, res, next) {
    try {
        res.json(await product.createproduct(req.body));
        
    }
     catch (err) {
      console.error(`Error while creating user`, err.message);
      next(err);
    }
});

router.put('/:id', async function(req, res, next) {
    try {
      res.json(await product.updateproduct(req.params.id, req.body));
    } catch (err) {
      console.error(`Error while updating product`, err.message);
      next(err);
    }
});

router.delete('/:id', async function(req, res, next) {
    try {
      res.json(await product.removeproduct(req.params.id));
    } catch (err) {
      console.error(`Error while deleting product`, err.message);
      next(err);
    }
  });
module.exports = router;