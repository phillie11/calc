const path = require('path');

module.exports = {
  entry: './src/components/GT7Dashboard.tsx',
  mode: 'production',
  module: {
    rules: [
      {
        test: /\.(ts|tsx)$/,
        use: [
          {
            loader: 'ts-loader',
            options: {
              compilerOptions: {
                jsx: 'react-jsx'
              }
            }
          }
        ],
        exclude: /node_modules/,
      },
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-react', {
                runtime: 'automatic'
              }]
            ]
          }
        }
      }
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
  },
  output: {
    filename: 'gt7_dashboard.js',
    path: path.resolve(__dirname, '../static/js'),
    library: 'GT7Dashboard',
    libraryTarget: 'window',
    libraryExport: 'default',
    clean: true
  },
  externals: {
    'react': 'React',
    'react-dom': 'ReactDOM',
    'recharts': 'Recharts',
    'lucide-react': 'LucideReact'
  },
  optimization: {
    minimize: false // Disable minification for easier debugging
  }
};