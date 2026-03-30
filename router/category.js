const express = require('express');
const router = express.Router();
const category = require('../services/category');

router.get('/', async function(req, res, next) {
    try {
      res.json(await category.getcategory(req.query.page));
    } catch (err) {
      console.error(`Error while getting categories`, err.message);
      next(err);
    }
  });
  

router.post('/',async function(req, res, next) {
    try {
        res.json(await category.createcategory(req.body));
        
    }
     catch (err) {
      console.error(`Error while creating category`, err.message);
      next(err);
    }
});

router.put('/:id', async function(req, res, next) {
    try {
      res.json(await category.updatecategory(req.params.id, req.body));
    } catch (err) {
      console.error(`Error while updating category`, err.message);
      next(err);
    }
});

router.delete('/:id', async function(req, res, next) {
    try {
      res.json(await category.removecategory(req.params.id));
    } catch (err) {
      console.error(`Error while deleting category`, err.message);
      next(err);
    }
  });

module.exports = router;