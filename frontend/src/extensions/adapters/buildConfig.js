import path from 'node:path'
import { createRequire } from 'node:module'
import { reckonAdapterPlugin } from './vitePlugin.js'
import { hostPackageLoader } from './hostPackages.js'

// All knowledge of the host build stack lives beside the source adapter.
// Dependencies come from the installed CRM frontend, retaining its Vue version.
export async function createBuildConfig({ crmFrontend, appRoot, outDir, base }) {
  const load = hostPackageLoader(crmFrontend)
  const [{ default: vue }, { default: vueJsx }, { default: frappeui, lucideIcons },
    { VitePWA }, { default: tailwindcss }, { default: autoprefixer }] = await Promise.all([
    load('@vitejs/plugin-vue'), load('@vitejs/plugin-vue-jsx'), load('frappe-ui/vite'),
    load('vite-plugin-pwa'), load('tailwindcss'), load('autoprefixer'),
  ])
  if (typeof lucideIcons !== 'function') {
    throw new Error('This CRM build needs an adapter for its older Frappe UI icon plugin.')
  }
  // Only use the icon resolver. The auto-import plugins generate files in the host tree.
  const icons = lucideIcons().flat(Infinity).filter((plugin) => plugin.name === 'frappe-ui-lucide-icons')
  if (icons.length !== 1) throw new Error('Unsupported Frappe UI icon plugin layout')
  // Tailwind's loader handles its extensionless CommonJS/ESM plugin imports.
  const requireCRM = createRequire(path.join(crmFrontend, 'package.json'))
  const loadTailwindConfig = requireCRM('tailwindcss/loadConfig')
  const tailwindConfig = loadTailwindConfig(path.join(crmFrontend, 'tailwind.config.js'))
  const content = tailwindConfig.content.map((glob) => path.resolve(crmFrontend, glob).replaceAll('\\', '/'))
  content.push(path.join(appRoot, 'frontend/src/**/*.{vue,js}').replaceAll('\\', '/'))

  return {
    configFile: false,
    root: crmFrontend,
    base,
    publicDir: false,
    plugins: [
      reckonAdapterPlugin(crmFrontend),
      ...frappeui({ lucideIcons: false, frappeProxy: false, buildConfig: false, jinjaBootData: true }),
      ...icons, vue(), vueJsx(),
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
          // No authenticated HTML/API data in an offline cache.
          navigateFallback: null,
          globPatterns: ['**/*.{js,css,woff,woff2}'],
          runtimeCaching: [],
        },
        manifest: {
          name: 'Reckon CRM', short_name: 'Reckon CRM', display: 'standalone',
          start_url: '/crm', scope: '/crm', theme_color: '#172824', background_color: '#ffffff',
          icons: [192, 512].map((size) => ({
            src: `/assets/crm/manifest/manifest-icon-${size}.maskable.png`,
            sizes: `${size}x${size}`, type: 'image/png', purpose: 'any maskable',
          })),
        },
      }),
    ],
    resolve: {
      alias: {
        '@': path.join(crmFrontend, 'src'),
        '@reckon': path.join(appRoot, 'frontend/src'),
        '@framework/ui': path.resolve(crmFrontend, '../../frappe/ui/src'),
      },
      dedupe: ['vue', 'vue-router', 'frappe-ui', 'dompurify', '@tiptap/core', '@tiptap/pm',
        '@tiptap/vue-3', 'prosemirror-model', 'prosemirror-state', 'prosemirror-view', 'prosemirror-transform'],
    },
    css: { postcss: { plugins: [tailwindcss({ ...tailwindConfig, content }), autoprefixer()] } },
    build: {
      outDir, emptyOutDir: true, sourcemap: false,
      commonjsOptions: { include: [/tailwind.config.js/, /node_modules/] },
    },
  }
}
