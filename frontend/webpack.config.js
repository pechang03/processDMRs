const path = require('path');

module.exports = {
mode: 'development',
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
        use: {
        loader: 'babel-loader'
        }
    }
    ]
},
devServer: {
    static: {
    directory: path.join(__dirname, 'public'),
    },
    hot: true,
    port: 3000,
    open: true
},
resolve: {
    extensions: ['.js', '.jsx']
}
};

