const express = require('express');
const axios = require('axios');
const ip = require('ip');
const app = express();

const PORT = 3001;
const ESP32_STREAM_URL = "http://10.19.130.119:81/stream";

// This keeps track of all connected browsers
let clients = [];

console.log("--- Hackathon Stream Relay ---");

// 1. Function to bridge the ESP32 stream to the server
async function startRelay() {
    try {
        const response = await axios({
            method: 'get',
            url: ESP32_STREAM_URL,
            responseType: 'stream',
            timeout: 10000
        });

        console.log("Successfully connected to ESP32-CAM!");

        // When data comes in from the ESP32, send it to every connected browser
        response.data.on('data', (chunk) => {
            clients.forEach(res => res.write(chunk));
        });

        response.data.on('end', () => {
            console.log("ESP32 stream ended. Reconnecting...");
            setTimeout(startRelay, 1000);
        });

    } catch (err) {
        console.error("Could not connect to ESP32: ", err.message);
        console.log("Retrying in 2 seconds...");
        setTimeout(startRelay, 2000);
    }
}

// 2. Endpoint for your React app / Browsers to connect to
app.get('/relay-stream', (req, res) => {
    // Set headers for MJPEG stream
    res.writeHead(200, {
        'Content-Type': 'multipart/x-mixed-replace; boundary=123456789000000000000987654321',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache'
    });

    // Add this browser to our broadcast list
    clients.push(res);
    console.log(`Client connected. Total clients: ${clients.length}`);

    // Remove client when they close the tab
    req.on('close', () => {
        clients = clients.filter(c => c !== res);
        console.log(`Client disconnected. Total clients: ${clients.length}`);
    });
});

app.listen(PORT, () => {
    const localIp = ip.address();
    console.log(`Relay Server running at: http://${localIp}:${PORT}`);
    console.log(`React App should now use: http://${localIp}:${PORT}/relay-stream`);
    
    // Start the connection to the ESP32
    startRelay();
});