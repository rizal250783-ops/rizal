module.exports = {
  webpack: {
    configure: (config) => {
      config.ignoreWarnings = [{ message: /Failed to parse source map/ }];
      return config;
    },
  },
};
