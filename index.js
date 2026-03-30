const express = require("express");
const app = express();
const port = 3000;
const programmingLanguagesRouter = require("./router/programmingLanguages");
const userRouter = require("./router/user");
const categoryRouter = require("./router/category");
const productRouter = require("./router/product");
const jwt = require('jsonwebtoken');
const config = require('./config');
const multer = require('multer');
const db = require('./services/db');
const helper = require('./helper');
const {validate, createuservalidate, createproductvalidate} = require("./validation");


app.use(express.json());
app.use(express.urlencoded({
  extended: true
}));
app.get("/", (req, res) => {
  res.json({ message: "ok" });
});
app.use("/programming-languages", programmingLanguagesRouter);
app.use("/createuser", createuservalidate(), validate(), userRouter);
app.use("/product", productRouter);
app.use("/category", categoryRouter);

const userService = require('./services/user');
const bcrypt = require('bcryptjs');

app.post('/login', async (req,res,next)=>{
  try {
    const {name,password} = req.body;
    const user = await userService.findUserByName(name);
    if (!user) {
      return res.status(401).json({ message: "Invalid credentials" });
    }
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: "Invalid credentials" });
    }
    jwt.sign({ user: { id: user.id, name: user.name, email: user.email } }, config.secret, { expiresIn: '1h' }, (err, token) => {
      if (err) return next(err);
      res.json({ token });
    });
  } catch (error) {
    next(error);
  }
})
const upload = multer({
  storage:multer.diskStorage({
    destination: function (req,file,cb){
      cb(null,"public")
    },
    filename: function (req,file,cb)
    {
      cb(null,file.fieldname+"-"+Date.now()+".jpg")
    }
  })
}).single("user_file")
app.post('/upload', upload, async (req, res, next) => {
  try {
    const filename = req.file.filename;
    // Parameterized pg query
    const sql = 'INSERT INTO image (filename) VALUES ($1)';
    await db.query(sql, [filename]);
    res.send('File uploaded successfully');
  } catch (error) {
    next(error);
  }
});

app.post("/profile",verifytoken,(req,res)=>{
  jwt.verify(req.token,config.secret,(err,authdata)=>{
    if(err){
      res.send({
        result:"invalid token"
      })
    }else{
      res.json({
        message:"profile accessed",
        name:authdata.user.name,
        email:authdata.user.email,

      })
    }
  })
})
function verifytoken(req,res,next){
  const bearerHeader = req.headers['authorization'];
  if(typeof bearerHeader !== 'undefined'){
    const bearer = bearerHeader.split(" ");
    const token = bearer[1];
    req.token= token;
    next();
  }else{
    res.send({
      result:'Token is not valid'
    })
  }
}

// Global error handler
app.use((err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  console.error(err.message, err.stack);
  res.status(statusCode).json({ message: err.message });
});


app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`);
});

