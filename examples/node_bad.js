const express = require('express')
const app = express()

app.get('/profile', (req, res) => {
  const user = req.user
  res.json({ name: user.name })
})

app.get('/settings', (req, res) => {
  res.json({ theme: 'dark' })
})

app.use(authMiddleware)
app.listen(3000)
