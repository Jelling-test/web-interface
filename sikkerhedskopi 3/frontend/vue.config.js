module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://backend:5000',
        changeOrigin: true
      },
      '/socket.io': {
        target: 'http://backend:5000',
        changeOrigin: true,
        ws: true
      }
    }
  },
  configureWebpack: {
    devtool: 'source-map'
  },
  chainWebpack: config => {
    config.plugin('feature-flags').tap(args => {
      args[0].__VUE_PROD_DEVTOOLS__ = false;
      args[0].__VUE_OPTIONS_API__ = true;
      args[0].__VUE_PROD_HYDRATION_MISMATCH_DETAILS__ = false;
      return args;
    });
  }
}
