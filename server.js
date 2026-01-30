const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

app.post('/login', async (req, res) => {
    const { clientCode, password, totp, apiKey } = req.body;

    try {
        const response = await axios.post('https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword', {
            clientcode: clientCode,
            password: password,
            totp: totp // Manual 6-digit code from App
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-PrivateKey': apiKey
            }
        });

        res.json(response.data);
    } catch (error) {
        const errMsg = error.response ? error.response.data.message : error.message;
        res.status(400).json({ status: false, message: errMsg });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`Server live on ${PORT}`));
