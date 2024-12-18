#!/bin/bash

# Make script exit on first error
set -e

echo "Starting frontend setup process..."

# Create directory structure
echo "Creating directory structure..."
mkdir -p frontend/src frontend/public

# Initialize npm project
echo "Initializing npm project..."
cd frontend
npm init -y

# Install React and core dependencies
echo "Installing React and core dependencies..."
npm install --legacy-peer-deps \
react@18.2.0 \
react-dom@18.2.0 \
@mui/material@5.14.20 \
@emotion/react@11.11.1 \
@emotion/styled@11.11.0 \
plotly.js-dist@2.27.1 \
react-plotly.js@2.6.0 \
axios@1.6.2

# Install development dependencies
echo "Installing development dependencies..."
npm install --save-dev --legacy-peer-deps \
@babel/core@7.23.5 \
@babel/preset-react@7.23.3 \
@babel/preset-env@7.23.5 \
webpack@5.89.0 \
webpack-cli@5.1.4 \
webpack-dev-server@4.15.1 \
babel-loader@9.1.3

# Create necessary configuration files
echo "Creating configuration files..."

# Create webpack config
cat > webpack.config.js << 'EOL'
const path = require('path');

module.exports = {
entry: './src/index.js',
output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
},
module: {
    rules: [
    {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader'],
    },
    ],
},
resolve: {
    extensions: ['*', '.js', '.jsx'],
},
devServer: {
    static: {
    directory: path.join(__dirname, 'public'),
    },
    port: 3000,
    hot: true,
},
};
EOL

# Create babel config
cat > babel.config.js << 'EOL'
module.exports = {
presets: ['@babel/preset-env', '@babel/preset-react'],
};
EOL

# Create base React files
echo "Creating React application files..."

# Create index.html
cat > public/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Analysis App</title>
</head>
<body>
    <div id="root"></div>
    <script src="/bundle.js"></script>
</body>
</html>
EOL

# Create index.js
cat > src/index.js << 'EOL'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
<React.StrictMode>
    <App />
</React.StrictMode>
);
EOL

# Create App.js
cat > src/App.js << 'EOL'
import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
palette: {
    mode: 'light',
},
});

function App() {
return (
    <ThemeProvider theme={theme}>
    <CssBaseline />
    <div>
        <h1>Network Analysis App</h1>
    </div>
    </ThemeProvider>
);
}

export default App;
EOL

# Update package.json scripts
npm pkg set scripts.start="webpack serve --mode development" \
            scripts.build="webpack --mode production" \
            scripts.dev="npm start"

# Create .gitignore
cat > .gitignore << 'EOL'
# Dependencies
node_modules/

# Production build
dist/
build/

# Environment variables
.env
.env.local
.env.*.local

# IDE files
.idea/
.vscode/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
EOL

echo "Setup complete! You can now run 'npm start' to start the development server."

# Return to original directory
cd ..

