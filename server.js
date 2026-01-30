const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

app.post('/login', async (req, res) => {
    // In chaaron variables ka naam bilkul sahi hona chahiye
    const { clientCode, password, totp, apiKey } = req.body;

    try {
        const response = await axios.post('https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword', 
        {
            "clientcode": clientCode,
            "password": password,
            "totp": totp
        }, 
        {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-PrivateKey': apiKey  // Yeh sabse important header hai
            }
        });

        res.json(response.data);
    } catch (error) {
        // Agar error aaye toh poora message dikhao
        const errMsg = error.response ? error.response.data : error.message;
        console.log("Angel One Error:", errMsg);
        res.status(400).json({ status: false, message: errMsg.message || "Login Failed" });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`Server started on port ${PORT}`));
