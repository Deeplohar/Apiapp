const express = require('express');
const axios = require('axios');
const cors = require('cors');
const { authenticator } = require('otplib'); // Auto OTP generate karne ke liye

const app = express();
app.use(express.json());
app.use(cors());

// Default route check karne ke liye ki server live hai ya nahi
app.get('/', (req, res) => {
    res.send("Trading Proxy Server is Running!");
});

app.post('/login', async (req, res) => {
    const { clientCode, password, totpSecret, apiKey } = req.body;

    try {
        // 1. Secret Key se 6-digit TOTP generate karein
        // Iske liye aapka phone ka time aur server ka time match hona chahiye
        const generatedTotp = authenticator.generate(totpSecret);
        console.log(`Generated TOTP for ${clientCode}: ${generatedTotp}`);

        // 2. Angel One API ko login request bhejein
        const response = await axios.post('https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword', {
            clientcode: clientCode,
            password: password,
            totp: generatedTotp
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-PrivateKey': apiKey
            }
        });

        // 3. Success response wapas bhejein
        res.json(response.data);

    } catch (error) {
        // Detailed error message taaki 400 error ka pata chale
        const errorMessage = error.response ? error.response.data.message : error.message;
        console.error("Login Error:", errorMessage);
        res.status(400).json({ 
            status: false, 
            message: errorMessage 
        });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
    console.log(`Server is live on port ${PORT}`);
});
