const express = require('express');
const router = express.Router();
const user = require('../services/user');

router.post('/',async function(req, res, next) {
    try {
        res.json(await user.createuser(req.body));
        
    }
     catch (err) {
      console.error(`Error while creating user`, err.message);
      next(err);
    }
});
module.exports = router;