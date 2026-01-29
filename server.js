const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors()); // Yeh browser ki CORS error khatam kar dega

app.post('/login', async (req, res) => {
    const { clientCode, password, totp, apiKey } = req.body;

    try {
        const response = await axios.post('https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword', {
            clientcode: clientCode,
            password: password,
            totp: totp
        }, {
            headers: {
                'Content-Type': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-PrivateKey': apiKey
            }
        });
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ status: false, message: error.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
