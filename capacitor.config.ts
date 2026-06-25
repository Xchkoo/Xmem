import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.xmem.android',
  appName: 'Xmem',
  webDir: 'frontend/dist',
  bundledWebRuntime: false,
  server: {
    androidScheme: 'https',
    hostname: 'localhost',
  },
};

export default config;
