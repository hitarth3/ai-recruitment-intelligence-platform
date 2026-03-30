const { check, validationResult,} = require('express-validator');



function validate() {
  return [
    (req, res, next) => {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(422).json({
          errors: errors.array().map(error => ({
            message: error.msg,
          })),
        });
      }
     next(); 
    },
  ];
}

const createuservalidate = () =>{
  return[
    check('name').notEmpty().withMessage('name is required'),
    check('email').notEmpty().withMessage('email is required'),
    check('password').notEmpty().withMessage('password is required')
  ]
}

const createproductvalidate = () =>{
  return[
    check('product_id').notEmpty().withMessage('product_id is required'),
    check('product_name').notEmpty().withMessage('product_name is required'),
    check('product_price').notEmpty().withMessage('product_price is required')
  ]
}



module.exports = {
  validate,
  createuservalidate,
  createproductvalidate
};
