const express = require('express');
const app = express();
const port = 3000;

// Set EJS as the view engine
app.set('view engine', 'ejs');

// Serve static files from the "public" directory
app.use(express.static('public'));

const welcomeMessage = "Welcome to Ryans super useful, totally awesome demo app!";

const portMessage = "Application Running on port";

const subHeaderMessage = "Refresh for a new Random Cat Image";

const getWelcomeMessage = () => {
    return welcomeMessage;
};

const getPortMessage = () => {
    return portMessage;
};

const getSubHeaderMessage = () => {
    return subHeaderMessage;
}

// Define a route for the home page
app.get('/', async (req, res) => {
    try {
        // Dynamically import the 'node-fetch' module
        const fetch = (await import('node-fetch')).default;

        // Fetch a random image from https://loremflickr.com
        const response = await fetch('https://loremflickr.com/640/480');

        const data = await response.json();
        const imageUrl = data.urls.regular;

        res.render('index', {
            welcomeMessage: getWelcomeMessage(),
            subHeaderMessage: getSubHeaderMessage(),
            portMessage: getPortMessage(),
            port: port,
            imageUrl: imageUrl
        });
    } catch (error) {
        console.error(error);
        res.status(500).send('Error fetching image from loremflicker.com');
    }
});


// Start the server
app.listen(port, () => {
    console.log(`${getPortMessage()} ${port}`);
});

