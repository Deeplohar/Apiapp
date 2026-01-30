const express = require("express");
const axios = require("axios");
const cors = require("cors");
const { authenticator } = require("otplib");

const app = express();
app.use(cors());
app.use(express.json());

authenticator.options = { window: 1 }; // ⏱ TOTP tolerance

app.get("/", (req, res) => {
  res.send("Trading Proxy Server is Running!");
});

app.post("/login", async (req, res) => {
  try {
    const { clientCode, password, totpSecret, apiKey } = req.body;

    if (!clientCode || !password || !totpSecret || !apiKey) {
      return res.json({ status: false, message: "Missing fields" });
    }

    const totp = authenticator.generate(totpSecret);
    console.log("Generated TOTP:", totp);

    const response = await axios.post(
      "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword",
      {
        clientcode: clientCode,
        password: password,
        totp: totp
      },
      {
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "X-UserType": "USER",
          "X-SourceID": "WEB",
          "X-ClientLocalIP": "127.0.0.1",
          "X-ClientPublicIP": "127.0.0.1",
          "X-MACAddress": "00:00:00:00:00:00",
          "X-PrivateKey": apiKey
        }
      }
    );

    if (response.data.status === true) {
      return res.json({
        status: true,
        message: "Login successful",
        data: response.data.data
      });
    } else {
      return res.json({
        status: false,
        message: response.data.message || "Login failed"
      });
    }

  } catch (err) {
    console.error("LOGIN ERROR:", err.response?.data || err.message);
    res.json({
      status: false,
      message: err.response?.data?.message || "Server error"
    });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
  console.log("Server running on port", PORT);
});
