# 1. Initialize npm
npm init -y

# 2. Core React dependencies
npm install --legacy-peer-deps react@18.2.0 react-dom@18.2.0

# 3. UI Framework
npm install --legacy-peer-deps @mui/material@5.14.20 @emotion/react@11.11.1 @emotion/styled@11.11.0

# 4. Visualization and API
npm install --legacy-peer-deps plotly.js-dist@2.27.1 react-plotly.js@2.6.0 axios@1.6.2

# 5. Development dependencies
npm install --save-dev --legacy-peer-deps @babel/core@7.23.5 @babel/preset-react@7.23.3 @babel/preset-env@7.23.5 webpack@5.89.0 webpack-cli@5.1.4 webpack-dev-server@4.15.1 babel-loader@9.1.3
cd frontend && #npm install @mui/icons-material

npm install @mui/material version (5.x.x) using --legacy-peer-deps #to resolve the dependency conflict.

npm install --save-dev style-loader css-loader
#npm warn idealTree Removing dependencies.style-loader in favor of devDependencies.style-loader
#npm warn idealTree Removing dependencies.css-loader in favor of devDependencies.css-loader
