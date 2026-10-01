import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import webpack, { type Configuration } from 'webpack';
import { merge } from 'webpack-merge';
import grafanaConfig, { type Env } from './.config/webpack/webpack.config.ts';

const root = process.cwd();
const packageMetadata = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8')) as { version: string };

class PluginMetadataWebpackPlugin {
  apply(compiler: webpack.Compiler) {
    compiler.hooks.thisCompilation.tap('PluginMetadataWebpackPlugin', (compilation) => {
      compilation.hooks.processAssets.tap({
        name: 'PluginMetadataWebpackPlugin',
        // Hash the final bundle after create-plugin's banner/minification.
        stage: webpack.Compilation.PROCESS_ASSETS_STAGE_REPORT,
      }, () => {
        const bundle = compilation.getAsset('module.js')?.source.buffer();
        const pluginJson = compilation.getAsset('plugin.json');
        if (!bundle || !pluginJson) { return; }
        const metadata = JSON.parse(pluginJson.source.source().toString());
        const hash = createHash('sha256').update(bundle).digest('hex').slice(0, 12);
        const releaseBuild = process.env.GRAFANA_PLUGIN_RELEASE === 'true';
        // Development builds use a content hash to invalidate Grafana's plugin cache.
        metadata.info.version = releaseBuild ? packageMetadata.version : `${packageMetadata.version}+${hash}`;
        metadata.info.updated = new Date().toISOString().slice(0, 10);
        compilation.updateAsset(
          'plugin.json',
          new webpack.sources.RawSource(JSON.stringify(metadata, null, 2) + '\n')
        );
      });
    });
  }
}

// Keep project-specific behavior outside the generated create-plugin config.
export default async (env: Env = {}): Promise<Configuration> => merge(await grafanaConfig(env), {
  plugins: [
    new PluginMetadataWebpackPlugin(),
  ],
});
