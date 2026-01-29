const express = require('express');
const axios = require('axios');
const cors = require('cors');
const { authenticator } = require('otplib'); // TOTP generate karne ke liye

const app = express();
app.use(express.json());
app.use(cors());

app.post('/login', async (req, res) => {
    const { clientCode, password, totpSecret, apiKey } = req.body;

    try {
        // 1. Secret Key se automatic 6-digit OTP generate karna
        const generatedTotp = authenticator.generate(totpSecret);

        // 2. Angel One API ko request bhejna
        const response = await axios.post('https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword', {
            clientcode: clientCode,
            password: password,
            totp: generatedTotp // Yahan auto-generated OTP ja raha hai
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
        const msg = error.response ? error.response.data.message : error.message;
        res.status(400).json({ status: false, message: msg });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`Server running with Auto-TOTP`));
